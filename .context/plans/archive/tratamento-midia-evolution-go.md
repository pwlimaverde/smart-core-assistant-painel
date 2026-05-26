# Plano: Tratamento Correto de Todos os Tipos de Mídia Recebidos

> **Status**: reestruturado contra documentação atual (Django 5.2.7, loguru ≥0.7.3,
> Evolution Go) e validado contra o código real em `master`/`feature/refatoracao-modular-atendimento`.
> Versão base do projeto: **1.2.2+012** → alvo **1.2.2+013**.

## Contexto

O usuário enviou PDF, imagem, áudio e vídeo separadamente para testar o recebimento
de mídia. A análise dos logs do servidor (`smartcoreassistant_celery_worker`)
revelou o estado exato de cada tipo.

### Diagnóstico pelos logs (v1.2.2+012)

| msg_id | tipo | fileLength | has_base64 | resultado |
|--------|------|-----------|-----------|-----------|
| 18110 / 18115 | documentMessage | 1.1 MB | True | persistido + análise IA (98 chars) |
| 18114 / 18119 | videoMessage | 1.0 MB | True | persistido + análise IA (2093 chars) |
| 18112 / 18118 | audioMessage | 19 KB | True | persistido + transcrição IA (140 chars) |
| 18113 | imageMessage (57 KB) | 57 KB | True | persistido + análise IA (1882 chars) |
| 18111 / 18116 | imageMessage (451 KB) | 451 KB | False | download 403 → **InterpretMediaError** |

**Conclusão**: 3 de 4 tipos funcionam. O único bug em produção é a **imagem grande
(forwarded, 451 KB) sem inline base64** — o fallback `POST /message/downloadmedia`
retorna erro (CDN do WhatsApp respondendo 403, que o Evolution Go encapsula como
500 genérico), e o código segue chamando `converter_contexto` com `base64_len=0`,
causando `InterpretMediaError`.

### Causa raiz (confirmada no código)

Em `_convert_media_context` (`attendance_orchestrator.py`, linhas 587-606): o bloco
`_persist_media_file` é corretamente protegido por `if has_base64`, mas
`converter_contexto` (linha 603) é chamado **incondicionalmente**, mesmo quando o
fallback de download falhou e `has_base64` continua `False`.

```python
# linha 587-596 — persistência JÁ protegida por has_base64 (correto)
file_saved = False
if has_base64 and not mensagem.arquivo_midia:
    try:
        self._persist_media_file(mensagem, metadados)
        file_saved = True
    except Exception as e:
        logger.error(...)

# linha 603 — PROBLEMA: chamado sem guard de has_base64
texto_convertido = FeaturesCompose.converter_contexto(
    metadados=metadados,
    message_type=mensagem.tipo,
)
```

---

## Mudanças a Implementar

### 1. Guarda antes de `converter_contexto`

**Arquivo**: `src/smart_core_assistant_painel/app/atendimentos/services/attendance_orchestrator.py`
**Local**: logo após o bloco `_persist_media_file` (após a linha 596) e **antes** do
log "Chamando converter_contexto" (linha 598).

Quando o fallback de download falhar (`has_base64` permanece `False`), não chamar a
IA. Registrar um placeholder em `analise_midia` e sair com `return`.

```python
# Sem base64 disponível (inline ausente E download via Evolution falhou):
# não há binário para a IA interpretar. Registra placeholder e sai —
# evita InterpretMediaError com base64_len=0.
if not has_base64:
    placeholder = (
        f"[{mensagem.tipo or 'mídia'} recebida — arquivo indisponível "
        "para análise]"
    )
    mensagem.analise_midia = placeholder
    mensagem.save(update_fields=["analise_midia"])
    logger.warning(
        "[MIDIA-CTX] Sem base64 após fallback de download | "
        "msg_id={} | tipo={} | placeholder registrado",
        mensagem.id,
        mensagem.tipo,
    )
    return
```

Notas de validação:
- `Model.save(update_fields=["analise_midia"])` — API estável no Django 5.2.7;
  emite UPDATE apenas do campo. Mesmo padrão já usado na linha 644.
- O `return` está dentro do `try` externo (linhas 538-649); seguro, pois não há
  cleanup posterior obrigatório dentro deste método.

### 2. Corrigir log multiline da análise IA

**Arquivo**: `attendance_orchestrator.py`
**Local**: linhas 622-629.

O log atual concatena o cabeçalho com o texto interpretado numa **única** chamada
multiline. Em loguru ≥0.7.3 o `\n` é preservado e exibido em múltiplas linhas,
**mas** ao filtrar logs por keyword (`grep "[MIDIA-CTX]"`) as linhas 2..N não contêm
o prefixo e somem do filtro. Separar em duas chamadas resolve.

Atual:
```python
logger.info(
    f"[MIDIA-CTX] <<< Análise IA registrada | "
    f"msg_id={mensagem.id} | tipo={mensagem.tipo} | "
    f"len_analise={len(texto_final)}\n"
    f"---[MIDIA-CTX] TEXTO INTERPRETADO]---\n"
    f"{texto_final}\n"
    f"---[MIDIA-CTX] FIM TEXTO INTERPRETADO]---"
)
```

Novo (duas chamadas; texto completo vai para `debug`):
```python
logger.info(
    "[MIDIA-CTX] <<< Análise IA registrada | msg_id={} | tipo={} | "
    "len_analise={}",
    mensagem.id,
    mensagem.tipo,
    len(texto_final),
)
logger.debug(
    "[MIDIA-CTX] Texto interpretado | msg_id={}:\n{}",
    mensagem.id,
    texto_final,
)
```

Notas de validação:
- Padrão de placeholder `{}` com argumentos posicionais é o **recomendado** pela
  doc atual do loguru (`logger.info("msg {}", value)`) — avalia lazy e evita
  injeção de `\n` vindo de dados externos. f-string continua funcionando, mas
  adotamos o padrão recomendado aqui por o `texto_final` ser conteúdo externo
  (saída de IA sobre mídia do usuário).
- O texto completo vai para `logger.debug` — fora do filtro de produção `info`,
  mas disponível quando o nível de debug estiver ativo.

### 3. Adicionar `stickerMessage` ao `_MEDIA_TYPES`

**Arquivo**: `attendance_orchestrator.py`
**Local**: linhas 95-100 (dentro de `process_contact_response`).

```python
_MEDIA_TYPES = (
    "audioMessage",
    "imageMessage",
    "videoMessage",
    "documentMessage",
    "stickerMessage",  # ← adicionar
)
```

### 4. (GAP CRÍTICO) Adicionar branch `stickerMessage` em `EvolutionMessageData.from_dict`

**Arquivo**: `src/smart_core_assistant_painel/app/evolution_sync/domain/schemas.py`
**Local**: dentro da cadeia `if/elif` de `from_dict`, após o branch
`documentMessage` (após a linha 248) e antes do `return cls(...)` (linha 250).

**Por que é obrigatório** (validado no código):
- `translate_go_payload` (schemas.py linha 463-478) **já** trata `MediaType="sticker"`
  genericamente: produz `messageType="stickerMessage"` e normaliza o sub-objeto
  (`URL`→`url`, `fileSHA256`→`fileSha256`, `fileEncSHA256`→`fileEncSha256`, e embute
  o `base64` irmão). Ou seja, o envelope chega correto.
- Porém `from_dict` **não tem branch** para `stickerMessage` → `metadata` fica `{}`.
- Consequência: `_convert_media_context` vê `has_url=False`/`has_base64=False`
  (linha 555), loga "sem URL/base64" e sai (linha 560). O sticker nunca é persistido
  nem analisado.
- A camada de persistência **já está pronta**: `_persist_media_file` (linha 694)
  mapeia `stickerMessage` → `.webp`. Falta apenas popular `metadata`.

Branch a adicionar (espelha o de `imageMessage`, sem `caption`; stickers não têm
caption nem fileName):

```python
elif message_type == "stickerMessage":
    msg_data = message.get("stickerMessage", {})
    text = "[sticker]"
    metadata = {
        "mimetype": msg_data.get("mimetype"),
        "url": msg_data.get("url"),
        # Stickers normalmente NÃO trazem base64 inline no webhook;
        # o download via Evolution (/message/downloadmedia) é o caminho
        # esperado — daí a importância dos campos de encriptação abaixo.
        "base64": msg_data.get("base64")
        or message.get("base64")
        or "",
        "mediaKey": msg_data.get("mediaKey", ""),
        "directPath": msg_data.get("directPath", ""),
        "fileSha256": msg_data.get("fileSha256", ""),
        "fileEncSha256": msg_data.get("fileEncSha256", ""),
        "fileLength": msg_data.get("fileLength"),
        "mediaKeyTimestamp": msg_data.get("mediaKeyTimestamp"),
    }
```

Notas de validação:
- Mantém **exatamente** o conjunto de chaves dos branches `imageMessage`/`videoMessage`
  já existentes — os campos de encriptação (`mediaKey`, `directPath`, `fileSha256`,
  `fileEncSha256`, `fileLength`, `mediaKeyTimestamp`) são os que
  `_fetch_media_base64_from_evolution` reenvia ao `POST /message/downloadmedia`.
- Conforme a doc do Evolution Go: stickers **não** trazem base64 inline no webhook —
  o binário só vem via `POST /message/downloadmedia` (que usa
  `msg.GetStickerMessage()` no servidor). Por isso o fallback de download é o caminho
  primário do sticker, e os campos de encriptação são indispensáveis.
- `text = "[sticker]"` como placeholder de conteúdo do balão (stickers não têm
  caption), coerente com `"[imagem]"`/`"[audio]"` dos outros branches.

### 5. Bump de versão, CHANGELOG e deploy

- `pyproject.toml`: `version = "1.2.2+013"` (linha 3).
- `CHANGELOG.md`: nova entrada no topo (manter o cabeçalho de comentário existente).
  Sugestão:

  ```markdown
  ## 1.2.2+013 - 2026-05-21 (build manual, sem tag)

  ### Fixed
  - **Mídia sem base64 (forwarded grande) causava InterpretMediaError**: quando o
    fallback `POST /message/downloadmedia` falha (CDN do WhatsApp → 403, encapsulado
    em 500 pelo Evolution Go), a IA era chamada com `base64_len=0`. Agora registra
    placeholder em `analise_midia` e retorna sem chamar `converter_contexto`.
  - **Logs `[MIDIA-CTX]` multiline sumiam de filtros**: o texto interpretado ficava
    em linhas sem o prefixo; separado em `logger.info` (cabeçalho) + `logger.debug`
    (texto completo), usando placeholders `{}` (padrão loguru recomendado).

  ### Added
  - **Suporte a `stickerMessage`**: adicionado a `_MEDIA_TYPES`
    (`attendance_orchestrator.py`) e branch dedicado em
    `EvolutionMessageData.from_dict` (`schemas.py`). O download via
    `/message/downloadmedia` e a persistência `.webp` já existiam.
  ```

- Deploy (conforme convenção da fase de estruturação — patch `+NNN`, **sem tag**,
  deploy manual via comandos do `pyproject.toml` com project name):
  ```bash
  uv run task server-rebuild-app
  uv run task server-rebuild-workers
  ```

---

## Ordem de Implementação Sugerida

1. `schemas.py` — branch `stickerMessage` em `from_dict` (item 4). Base do suporte.
2. `attendance_orchestrator.py` — `_MEDIA_TYPES` (item 3).
3. `attendance_orchestrator.py` — guard `has_base64` (item 1). Corrige o bug em produção.
4. `attendance_orchestrator.py` — logs (item 2).
5. Versão + CHANGELOG + deploy (item 5).

## Verificação Pós-Implementação

- `uv run pyright` nos dois arquivos (sem novos erros de tipo).
- Lint/format conforme configuração do projeto.
- Reenviar imagem grande forwarded → confirmar `analise_midia` com placeholder e
  ausência de `InterpretMediaError` nos logs do worker.
- Enviar um sticker → confirmar `messageType=stickerMessage`, metadata populada,
  download via `/message/downloadmedia`, arquivo `.webp` persistido e análise IA.

---

## Correções Aplicadas (plano original → reestruturado)

| # | Item do plano original | Ajuste aplicado | Motivo (lib/versão/recurso) |
|---|------------------------|-----------------|------------------------------|
| 1 | Guard `has_base64` antes de `converter_contexto` | **Mantido e validado**. Confirmado que o gap existe no código real (linha 603 chama `converter_contexto` sem guard; persistência na 588 já protegida). `save(update_fields=["analise_midia"])` confirmado estável. | Django 5.2.7 — `Model.save(update_fields=...)` estável; `post_save` agora propaga `update_fields` (sem impacto aqui). |
| 2 | Log multiline → 2 chamadas | **Mantido e refinado**: trocado f-string por placeholders posicionais `{}` no `info`/`debug`. O log real (linhas 622-629) difere do citado no plano (delimitadores `---[MIDIA-CTX] TEXTO INTERPRETADO]---`), mas o problema de filtragem é o mesmo. | loguru ≥0.7.3 — `\n` é preservado mas quebra filtros por keyword; padrão recomendado é `logger.info("msg {}", value)` (lazy + evita injeção de `\n` de dados externos, relevante pois `texto_final` é saída de IA sobre conteúdo do usuário). |
| 3 | `stickerMessage` em `_MEDIA_TYPES` | **Mantido**. Confirmado que a tupla (linhas 95-100) não contém sticker. | — (lista interna do projeto). |
| 4 | **NOVO** — branch `stickerMessage` em `from_dict` | **Adicionado** (não estava no plano original). Sem ele, `_MEDIA_TYPES` sozinho não funciona: `from_dict` retornaria `metadata={}` e o sticker sairia em "sem URL/base64". | Evolution Go — `translate_go_payload` (linha 463) já gera `stickerMessage`; `/message/downloadmedia` suporta sticker via `GetStickerMessage()`; stickers não trazem base64 inline (download obrigatório, exige campos de encriptação). |
| 5 | Endpoint de download | **Confirmado correto**: `POST /message/downloadmedia` (o `/downloadimage` do swagger é 404; já migrado no build +012). Plano original não citava o path; documentado aqui para rastreabilidade. | Evolution Go — único mecanismo de download é `POST /message/downloadmedia`; resposta é data URL `data:<mime>;base64,...` (prefixo já removido em `_persist_media_file`, linha 671). |
| 6 | Persistência `.webp` do sticker | **Verificado pré-existente**: `_persist_media_file` (linha 694) já mapeia `stickerMessage → .webp` via `ContentFile` + `save(..., save=False)`. Nenhuma mudança necessária. | Django 5.2.7 — `FileField.save(name, content, save=False)` e `ContentFile(bytes)` estáveis; `save=False` não dispara `model.save()` (o save vem depois com `update_fields=["arquivo_midia"]`). |
| 7 | Versão/deploy | **Mantido** (1.2.2+013). Reforçada a convenção da fase de estruturação: patch `+NNN`, **sem git tag**, deploy manual via `uv run task server-rebuild-*` com project name. | Convenção do projeto (memória/CHANGELOG). |

**Sem APIs depreciadas ou removidas detectadas** nas libs envolvidas (Django 5.2.7,
loguru ≥0.7.3). As correções foram: adição do gap crítico de sticker em `from_dict`,
adoção do padrão de logging recomendado do loguru e validação dos pontos do plano
contra o código real.
