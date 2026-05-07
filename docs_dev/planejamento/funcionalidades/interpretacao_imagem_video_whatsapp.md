# Plano: Interpretação de Imagens e Vídeos no Pipeline WhatsApp

## Contexto

O bot WhatsApp já transcreve áudios com sucesso via Groq Whisper. Porém, quando recebe imagens ou vídeos, mantém apenas um placeholder (`[imagem]`, `[video]`) sem extrair contexto útil. O objetivo é que o bot descreva imagens em detalhe e resuma vídeos (visual + áudio), inserindo como contexto textual antes de gerar a resposta — exatamente como faz com áudio.

**Problema de negócio**: cliente envia foto de produto e pergunta "quanto custa?" — hoje o bot não sabe do que se trata. Com esta feature, ele descreverá a imagem e usará como contexto para responder.

## Decisões de Design

### Provedor: Google Gemini 2.5 Flash

- **Imagem e Vídeo**: Google Gemini 2.5 Flash para ambos
- **Vídeo nativo**: Gemini processa vídeo completo (visual + áudio) em 1 chamada de API, sem FFmpeg
- **Custo**: ~$0.0001/imagem, ~$0.03/vídeo 5min — significativamente mais barato que OpenAI
- **API Key**: armazenada em CoreSettings como `google_api_key` (encrypted), com override por tenant
- **Dependência**: `google-genai` (SDK oficial Google AI)
- **Sem FFmpeg**: não precisa alterar imagem Docker

### Comparativo Google vs OpenAI para Vídeo

| Critério | Google Gemini 2.5 Flash | OpenAI GPT-4.1-mini |
|----------|------------------------|---------------------|
| **Vídeo nativo** | Sim (1 chamada de API) | Não (precisa FFmpeg) |
| **Áudio do vídeo** | Incluso automaticamente | Precisa Whisper separado |
| **Custo por vídeo 5min** | ~$0.03 | ~$0.15-0.20 |
| **Calls de API por vídeo** | 1 | 2+ (frames + Whisper) |
| **Dependências extras** | Nenhuma | FFmpeg (~80MB Docker) + `ffmpeg-python` |
| **Complexidade código** | Baixa (~50 linhas) | Alta (~150+ linhas) |
| **Qualidade visual** | Excelente (vídeo completo) | Boa (apenas frames estáticos) |
| **Qualidade áudio** | Excelente (contexto visual+áudio junto) | Boa (separado, sem contexto visual) |

### Outras decisões

- **Falha = transferência para humano** (bot não responde sem contexto visual)
- **Features separadas**: `interpret_image/` e `interpret_video/` (mesmo padrão de `transcribe_audio/`)
- **Prompts configuráveis**: via CoreSettings com defaults hardcoded
- **Limite de vídeo**: 300 segundos (5 min), configurável por tenant
- **Leitura dinâmica**: todas as configs passam por CoreSettings → TenantConfig → RuntimeConfig → ServiceHub (padrão existente)

## Arquivos a Criar (12 arquivos)

```
modules/ai_engine/features/
├── interpret_image/
│   ├── __init__.py
│   ├── datasource/
│   │   ├── __init__.py
│   │   └── interpret_image_datasource.py    # Google Gemini Vision
│   └── domain/
│       ├── __init__.py
│       └── usecase/
│           ├── __init__.py
│           └── interpret_image_usecase.py    # Valida URL/base64
│
└── interpret_video/
    ├── __init__.py
    ├── datasource/
    │   ├── __init__.py
    │   └── interpret_video_datasource.py     # Google Gemini nativo (upload + analyze)
    └── domain/
        ├── __init__.py
        └── usecase/
            ├── __init__.py
            └── interpret_video_usecase.py     # Valida URL/base64 + limite duração
```

## Arquivos a Modificar

### 1. `modules/ai_engine/utils/erros.py`
Adicionar `InterpretImageError` e `InterpretVideoError` (mesmo padrão de `TranscribeAudioError` linha 96).

### 2. `modules/ai_engine/utils/parameters.py`
Adicionar após `TranscribeAudioParameters` (linha 286):

- **`InterpretImageParameters`**: `image_url`, `mimetype`, `error`, `image_base64=""`, `caption=""`, `language="pt"`
- **`InterpretVideoParameters`**: `video_url`, `mimetype`, `seconds`, `error`, `video_base64=""`, `caption=""`, `language="pt"`, `max_seconds=300`

### 3. `modules/ai_engine/utils/types.py`
Adicionar após linha 191:
- `IIData`, `IIUsecase` (Interpret Image)
- `IVData`, `IVUsecase` (Interpret Video)

### 4. `modules/ai_engine/features/features_compose.py`
Substituir TODOs (linhas 411-413) por dispatch real:
- `imageMessage` → `_interpret_image()` (extrai `url`, `mimetype`, `base64`, `caption`)
- `videoMessage` → `_interpret_video()` (extrai `url`, `mimetype`, `base64`, `caption`, `seconds`)
- Novos métodos estáticos `_interpret_image()` e `_interpret_video()` seguindo padrão de `_transcribe_audio()` (linha 452)

### 5. `modules/services/config/context.py` — RuntimeConfig
Adicionar campos ao dataclass (após linha 27):
```python
# === Interpretação Visual ===
vision_provider: str = "google"
vision_model: str = "gemini-2.5-flash"
google_api_key: str = ""
prompt_image_description: str = ""
prompt_video_description: str = ""
video_max_seconds: int = 300
```

### 6. `modules/services/features/service_hub.py`
Adicionar 6 properties (após linha 90):
- `VISION_PROVIDER` → `ConfigProvider.get().vision_provider`
- `VISION_MODEL` → `ConfigProvider.get().vision_model`
- `GOOGLE_API_KEY` → `ConfigProvider.get().google_api_key`
- `PROMPT_IMAGE_DESCRIPTION` → `ConfigProvider.get().prompt_image_description`
- `PROMPT_VIDEO_DESCRIPTION` → `ConfigProvider.get().prompt_video_description`
- `VIDEO_MAX_SECONDS` → `ConfigProvider.get().video_max_seconds`

### 7. `app/tenants/models.py` — TenantConfig
Adicionar campos (após `transcription_model` linha 304):
- `vision_provider` (CharField, max 50, blank)
- `vision_model` (CharField, max 100, blank)
- `video_max_seconds` (IntegerField, null/blank)
- `google_api_key` via `api_keys` JSONField existente (mesmo padrão de `groq_api_key`, `openai_api_key`)

### 8. `app/tenants/services/config_loader.py`

**Em `load_for_request()` (linha 67)** — adicionar ao `RuntimeConfig(...)`:
```python
# === API Key Google (tenant sobrescreve core) ===
google_api_key=tenant_cfg.get("google_api_key")
    or core.get("google_api_key", ""),
# === Interpretação Visual ===
vision_provider=tenant_cfg.get("vision_provider")
    or core.get("vision_provider", "google"),
vision_model=tenant_cfg.get("vision_model")
    or core.get("vision_model", "gemini-2.5-flash"),
prompt_image_description=core.get(
    "prompt_image_description", ""
),
prompt_video_description=core.get(
    "prompt_video_description", ""
),
video_max_seconds=int(
    tenant_cfg.get("video_max_seconds")
    or core.get("video_max_seconds", "300")
),
```

**Em `_get_tenant_config()` (linha 176)** — adicionar ao `tenant_data`:
```python
"vision_provider": cfg.vision_provider if cfg.vision_provider else "",
"vision_model": cfg.vision_model if cfg.vision_model else "",
"video_max_seconds": str(cfg.video_max_seconds) if cfg.video_max_seconds else "",
```
E para a API key:
```python
google_key = cfg.get_api_key("google_api_key")
if google_key:
    tenant_data["google_api_key"] = google_key
```

### 9. `app/evolution_sync/domain/schemas.py`
Adicionar `caption` aos dicts de metadata (ainda não está sendo extraído):
- `imageMessage` (linha ~98): `"caption": msg_data.get("caption", ""),`
- `videoMessage` (linha ~117): `"caption": msg_data.get("caption", ""),`

### 10. `app/atendimentos/services/attendance_orchestrator.py`
Modificar `_convert_media_context()` (linha 439):
- No bloco `else` (conversão vazia, linha 513) e no `except` (linha 518): se tipo for `imageMessage` ou `videoMessage`, transferir para humano
- Novo método `_transfer_on_media_failure()`:
```python
def _transfer_on_media_failure(self, mensagem: "Mensagem") -> None:
    attendance = mensagem.atendimento
    self._structure_manager.apply_transfer_flow(attendance)
    logger.info(
        f"Atendimento {attendance.id} transferido "
        f"por falha visual (msg={mensagem.id})"
    )
```

### 11. `scripts/config_global/coresettings.json`
Adicionar 6 novas entries:

| Key | Value | encrypted | Descrição |
|-----|-------|-----------|-----------|
| `vision_provider` | `"google"` | false | Provedor de interpretação visual (google) |
| `vision_model` | `"gemini-2.5-flash"` | false | Modelo para interpretação visual |
| `google_api_key` | `""` | **true** | Chave de API do Google AI (Gemini) |
| `prompt_image_description` | (prompt default) | false | Prompt para descrição de imagens |
| `prompt_video_description` | (prompt default) | false | Prompt para resumo de vídeos |
| `video_max_seconds` | `"300"` | false | Duração máxima de vídeo (5 min) |

### 12. `pyproject.toml`
Adicionar dependência: `"google-genai>=1.0.0"`

## Detalhes dos Datasources

### InterpretImageDatasource
Reutiliza padrões de `TranscribeAudioDatasource` (base64 decode, download, temp files).

```python
class InterpretImageDatasource(IIData):
    _MAX_IMAGE_SIZE_BYTES = 20 * 1024 * 1024  # 20MB

    def __call__(self, parameters):
        # 1. Obtém bytes (base64 preferencial, URL fallback)
        # 2. Valida tamanho
        # 3. Monta prompt (com caption se houver)
        # 4. Chama Gemini via google.genai.Client
        #    imagem enviada inline como Part
        # 5. Retorna descrição textual
```

**Chamada Gemini para imagem**:
```python
from google import genai
from google.genai import types

client = genai.Client(api_key=SERVICEHUB.GOOGLE_API_KEY)
response = client.models.generate_content(
    model=model,  # "gemini-2.5-flash"
    contents=[
        types.Part.from_bytes(
            data=image_bytes,
            mime_type=mimetype,
        ),
        prompt,
    ],
)
return response.text
```

### InterpretVideoDatasource
Usa upload de arquivo do Gemini para vídeo nativo.

```python
class InterpretVideoDatasource(IVData):
    _MAX_VIDEO_SIZE_BYTES = 100 * 1024 * 1024  # 100MB

    def __call__(self, parameters):
        # 1. Obtém bytes do vídeo (base64 ou download)
        # 2. Salva em arquivo temporário
        # 3. Upload para Gemini File API
        # 4. Polling até estado ACTIVE
        # 5. generate_content com arquivo + prompt
        # 6. Cleanup: delete arquivo remoto + temp local
        # 7. Retorna resumo consolidado
```

**Chamada Gemini para vídeo**:
```python
from google import genai
import time

client = genai.Client(api_key=SERVICEHUB.GOOGLE_API_KEY)

# 1. Upload do vídeo
video_file = client.files.upload(
    file=temp_video_path,
    config={"mime_type": mimetype},
)

# 2. Aguardar processamento
while video_file.state.name == "PROCESSING":
    time.sleep(2)
    video_file = client.files.get(name=video_file.name)

# 3. Análise (visual + áudio em 1 call)
response = client.models.generate_content(
    model=model,
    contents=[video_file, prompt],
)

# 4. Cleanup
client.files.delete(name=video_file.name)

return response.text
```

## Prompts Default

**Imagem**:
```
Descreva esta imagem em detalhes em português. Inclua:
- Objetos visíveis e suas características
- Cores predominantes
- Texto legível (OCR) se houver
- Contexto geral da cena
Seja conciso mas completo. Máximo 3 parágrafos.
```

**Vídeo**:
```
Analise este vídeo completo (visual e áudio) e gere um resumo
em português. Inclua:
- Descrição geral do conteúdo visual
- Transcrição/resumo do áudio se houver fala
- Ações ou eventos importantes
- Contexto geral do vídeo
Seja conciso mas completo. Máximo 5 parágrafos.
```

## Fluxo de Configuração Dinâmica (leitura)

```
CoreSettings (banco, cache 5min)
  ↓ fallback
TenantConfig (banco, por request)
  ↓ merge (tenant sobrescreve core)
ConfigLoader.load_for_request()
  ↓ cria
RuntimeConfig (frozen dataclass, ContextVar)
  ↓ acesso via
ConfigProvider.get()
  ↓ expõe via
ServiceHub (singleton, properties)
  ↓ lido por
Datasources (InterpretImageDatasource, InterpretVideoDatasource)
```

Novas chaves seguem exatamente o mesmo caminho das existentes (`transcription_provider`, `groq_api_key`, etc.).

## Fases de Implementação

### Fase 1: Infraestrutura
1. Adicionar `google-genai` ao `pyproject.toml` + `uv sync`
2. Erros em `erros.py`
3. Parameters em `parameters.py`
4. Types em `types.py`
5. Campos `RuntimeConfig` em `context.py`
6. Properties `ServiceHub` em `service_hub.py`
7. Campos `TenantConfig` em `models.py` + migração
8. Atualizar `ConfigLoader` em `config_loader.py`
9. Entries no `coresettings.json`
10. `caption` no `schemas.py`

### Fase 2: Feature de Imagem
1. Criar `interpret_image/` com datasource e usecase
2. Dispatch `imageMessage` no `FeaturesCompose.converter_contexto()`
3. Método `FeaturesCompose._interpret_image()`

### Fase 3: Feature de Vídeo
1. Criar `interpret_video/` com datasource e usecase
2. Dispatch `videoMessage` no `FeaturesCompose.converter_contexto()`
3. Método `FeaturesCompose._interpret_video()`

### Fase 4: Tratamento de Falha
1. Modificar `_convert_media_context()` no orchestrator
2. Método `_transfer_on_media_failure()`

### Fase 5: Deploy
1. `uv run task type-check` + `uv run task lint`
2. Inserir `google_api_key` no CoreSettings (via admin ou bootstrap)
3. `uv run task server-deploy`

## Verificação

1. **type-check**: `uv run task type-check`
2. **lint**: `uv run task lint && uv run task format`
3. **Imagem com caption**: enviar foto + legenda → verificar descrição no `conteudo`
4. **Imagem sem caption**: enviar foto sem texto → verificar descrição funciona
5. **Vídeo curto (<5min)**: enviar vídeo → verificar resumo com visual + áudio
6. **Vídeo longo (>5min)**: verificar rejeição + transferência para humano
7. **Falha Google**: api_key inválida → verificar transferência para humano
8. **Tenant override**: configurar `vision_model` diferente em TenantConfig → verificar
