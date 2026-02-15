---
status: ready
generated: 2026-02-14
title: "Contexto Multimídia no WhatsApp com OpenAI + Groq"
owners:
  - "backend-specialist"
  - "architect-specialist"
agents:
  - type: "architect-specialist"
    role: "Definir contratos, fluxos e decisões arquiteturais"
  - type: "backend-specialist"
    role: "Implementar pipelines de imagem e vídeo no padrão do áudio"
  - type: "devops-specialist"
    role: "Adicionar FFmpeg e ajustes de ambiente/containers"
  - type: "security-auditor"
    role: "Revisar handling de URL/base64 e exposição de dados sensíveis"
  - type: "code-reviewer"
    role: "Validar consistência com padrões do projeto"
  - type: "documentation-writer"
    role: "Atualizar documentação de arquitetura e operação"
docs:
  - "architecture.md"
  - "data-flow.md"
  - "security.md"
  - "tooling.md"
  - "development-workflow.md"
phases:
  - id: "phase-1"
    name: "Especificação Técnica"
    prevc: "P"
  - id: "phase-2"
    name: "Implementação"
    prevc: "E"
  - id: "phase-3"
    name: "Validação e Handoff"
    prevc: "V"
---

# Plano Estruturado: Contexto Multimídia no WhatsApp

> Objetivo: adicionar interpretação de imagem e vídeo no fluxo de mensagens WhatsApp para compor contexto antes da resposta do bot, mantendo arquitetura dinâmica por tenant e fallback imediato para transferência humana em caso de falha.

## 1. Objetivo e Escopo

### Objetivo principal
Garantir que mensagens com mídia (`imageMessage` e `videoMessage`) sejam convertidas em contexto textual útil para o atendimento antes da geração da resposta do bot.

### Resultado esperado de negócio
Quando o cliente enviar, por exemplo, foto de "sapato branco" e perguntar "quanto custa?", o sistema deve inferir o item e atributo (sapato + cor branca) e responder com base nesse contexto.

### Em escopo
- Pipeline separado para imagem e vídeo.
- Configuração dinâmica em `CoreSettings` + override em `TenantConfig`.
- Reuso do padrão técnico da feature de áudio (Parameters + UseCase + Datasource + integração em `FeaturesCompose`).
- Execução assíncrona no backend (Celery), com bloqueio da resposta até a análise concluir.
- Fallback de transferência para atendente humano via função já existente `apply_transfer_flow`.

### Fora de escopo
- Suporte Ollama.
- Interface nova de frontend para configuração avançada (somente admin existente neste ciclo).
- Criação de testes automatizados por este plano (restrição operacional atual do projeto).

## 2. Arquitetura Atual Relevante

### Pontos existentes que serão reutilizados
- Conversão multimídia central: `src/smart_core_assistant_painel/modules/ai_engine/features/features_compose.py`.
- Transcrição de áudio (referência de padrão): `src/smart_core_assistant_painel/modules/ai_engine/features/transcribe_audio/`.
- Carregamento dinâmico por tenant: `src/smart_core_assistant_painel/app/tenants/services/config_loader.py`.
- RuntimeConfig/ServiceHub: `src/smart_core_assistant_painel/modules/services/config/context.py` e `src/smart_core_assistant_painel/modules/services/features/service_hub.py`.
- Orquestração de resposta: `src/smart_core_assistant_painel/app/atendimentos/services/attendance_orchestrator.py`.

### Ajuste crítico de comportamento
Hoje, falha em conversão de mídia não interrompe resposta do bot.
Novo comportamento: falha/timeout da análise de imagem/vídeo deve acionar transferência humana e encerrar tentativa de resposta automática.

## 3. Modelos e Estratégia Custo-Benefício

### Imagem
- Primário: OpenAI `gpt-4o-mini` (melhor custo/benefício para visão em produção estável).
- Fallback: Groq `meta-llama/llama-4-scout-17b-16e-instruct`.

### Vídeo
- Extração técnica: frames + áudio via FFmpeg.
- Transcrição de áudio do vídeo: Groq `whisper-large-v3-turbo` (baixo custo).
- Consolidação contextual (frames + transcrição + pergunta): OpenAI `gpt-4.1-mini` primário.
- Fallback de consolidação: Groq `meta-llama/llama-4-scout-17b-16e-instruct`.

## 4. Contratos de Configuração Dinâmica

## 4.1 Novas chaves CoreSettings
- `image_analysis_provider`
- `image_analysis_model`
- `image_analysis_fallback_provider`
- `image_analysis_fallback_model`
- `video_analysis_provider`
- `video_analysis_model`
- `video_analysis_fallback_provider`
- `video_analysis_fallback_model`
- `video_transcription_provider`
- `video_transcription_model`
- `media_analysis_timeout_seconds`
- `media_max_file_mb`
- `video_max_seconds`
- `video_frame_stride_seconds`
- `video_max_frames`

## 4.2 Novos campos TenantConfig (override)
Adicionar campos equivalentes em `TenantConfig` (string/int) com comportamento:
- se preenchido no tenant, sobrescreve global;
- se vazio, usa CoreSettings.

## 4.3 Loader dinâmico
Atualizar `ConfigLoader` para mapear todas as novas chaves no `RuntimeConfig`.

## 4.4 ServiceHub
Expor propriedades para os novos parâmetros, mantendo padrão atual.

## 5. Design Técnico por Pipeline

## 5.1 Pipeline de Imagem
1. Entrada: `metadados` com `url` e/ou `base64`.
2. Validação: presença de fonte de mídia, tamanho máximo e mime compatível.
3. Análise primária: OpenAI (`gpt-4o-mini`) com prompt estruturado para:
   - objeto principal;
   - atributos relevantes (cor, material, marca, estado);
   - intenção inferida do cliente em conjunto com texto da mensagem.
4. Fallback: Groq visão.
5. Persistência:
   - salvar `contexto_convertido` em `mensagem.metadados`;
   - atualizar `mensagem.conteudo` com bloco contextual.

## 5.2 Pipeline de Vídeo
1. Entrada: `url` e/ou `base64`.
2. Validação: duração (`video_max_seconds`) e tamanho (`media_max_file_mb`).
3. Pré-processamento FFmpeg:
   - extrair frames por stride configurável;
   - extrair trilha de áudio.
4. Transcrição do áudio do vídeo.
5. Consolidação contextual em LLM:
   - resumo da cena;
   - timeline curta por timestamps;
   - intenção inferida conectando mídia + pergunta textual.
6. Persistência:
   - `contexto_convertido` em metadados;
   - conteúdo textual final na mensagem para análise de intenção.

## 5.3 Contrato de retorno multimídia
Criar resultado estruturado interno (dataclass/model) com:
- `status` (`success`, `failed`, `timeout`);
- `context_text`;
- `provider_used`;
- `model_used`;
- `latency_ms`;
- `error_message`.

## 6. Comportamento do Orquestrador

### Fluxo obrigatório antes da resposta
No `AttendanceOrchestrator._process_message_and_respond`:
1. detectar tipo multimídia;
2. processar mídia com timeout global de 30s;
3. só continuar para `analyze_message_content` após `status=success`.

### Regra de falha
Se `failed` ou `timeout`:
1. registrar motivo em `metadados`;
2. registrar resposta de transferência padrão;
3. chamar `apply_transfer_flow(attendance, None)`;
4. interromper geração automática de resposta do bot.

## 7. Estrutura de Implementação (mesmo padrão do áudio)

Criar novas features em `modules/ai_engine/features`:
- `interpret_image/`
  - `datasource/interpret_image_datasource.py`
  - `domain/usecase/interpret_image_usecase.py`
- `interpret_video/`
  - `datasource/interpret_video_datasource.py`
  - `domain/usecase/interpret_video_usecase.py`

Atualizações obrigatórias:
- `modules/ai_engine/utils/parameters.py` (novos Parameters).
- `modules/ai_engine/utils/types.py` (novos TypeAlias).
- `modules/ai_engine/features/features_compose.py` (dispatch e métodos privados).
- `app/tenants/models.py` + migration.
- `app/tenants/services/config_loader.py`.
- `modules/services/config/context.py`.
- `modules/services/features/service_hub.py`.
- `settings_manager` commands (`bootstrap_core_settings.py`, `load_core_settings.py`) e JSON de seed.

## 8. Fases de Trabalho

## Fase 1 — Especificação Técnica (P)
### Passos
1. Arquitetura: fechar contratos de parâmetros e retorno para imagem/vídeo.
2. Backend: definir prompts canônicos e formato de contexto textual.
3. DevOps: especificar adição de FFmpeg nos containers app/worker.
4. Segurança: validar política de download de mídia e limpeza de base64.

### Entregáveis
- Especificação técnica aprovada.
- Lista final de chaves dinâmicas (core + tenant).

### Checkpoint sugerido
`docs(plan): especificacao multimidia openai-groq`

## Fase 2 — Implementação (E)
### Passos
1. Implementar novos módulos de imagem e vídeo no padrão do áudio.
2. Integrar `FeaturesCompose.converter_contexto` com dispatch por tipo.
3. Integrar orquestrador para bloqueio de resposta até análise.
4. Implementar fallback de transferência em falha/timeout.
5. Adicionar campos dinâmicos em `TenantConfig` e `RuntimeConfig`.
6. Atualizar loaders e comandos de bootstrap/import de settings.
7. Ajustar Docker para FFmpeg.

### Entregáveis
- Código funcional para imagem e vídeo com fallback.
- Migração aplicada para novos campos tenant.
- Configuração dinâmica operacional.

### Checkpoint sugerido
`feat: contexto multimidia imagem e video com fallback humano`

## Fase 3 — Validação e Handoff (V)
### Passos
1. Validar cenários funcionais ponta a ponta em ambiente de staging.
2. Revisão de segurança de payload e logs.
3. Atualizar documentação técnica e operacional.
4. Preparar guia de rollout por tenant.

### Entregáveis
- Evidências de validação funcional.
- Runbook de operação e fallback.
- Plano de rollback validado.

### Checkpoint sugerido
`docs: validacao e handoff do fluxo multimidia`

## 9. Critérios de Sucesso

1. Imagem com pergunta de preço gera resposta contextual coerente.
2. Vídeo gera resumo + timeline + intenção contextual.
3. Resposta automática não é enviada antes da análise multimídia finalizar.
4. Falha/timeout em análise resulta em transferência humana imediata.
5. Configuração dinâmica funciona por tenant sem vazamento entre tenants.
6. Sem uso de Ollama em qualquer caminho da feature.

## 10. Riscos e Mitigações

| Risco | Prob. | Impacto | Mitigação |
| --- | --- | --- | --- |
| Mudança em modelo preview da Groq | Média | Médio | Usar OpenAI primário e Groq apenas fallback |
| Latência acima de 30s em vídeo | Média | Alto | Limitar duração/tamanho/frames e timeout rígido |
| Falha em download de mídia externa | Média | Médio | Retry curto + fallback para transferência |
| Sobrecarga de worker por FFmpeg | Média | Alto | Limites conservadores e ajuste de concorrência |

## 11. Dependências Técnicas

- FFmpeg disponível nos containers de app/worker.
- API keys válidas para OpenAI e Groq.
- Permissão de rede para download de mídia recebida da Evolution.

## 12. Rollback

### Gatilhos
- aumento significativo de timeout/falha;
- respostas incoerentes por erro de contexto;
- degradação de fila do worker.

### Procedimento
1. Desativar chaves de análise multimídia em CoreSettings (feature toggle por config).
2. Reverter dispatch de imagem/vídeo para comportamento anterior.
3. Manter somente transcrição de áudio ativa.
4. Monitorar estabilização da fila e atendimento.

## 13. Evidências de Validação (checklist)

- [ ] Caso: foto de produto + pergunta de preço.
- [ ] Caso: vídeo curto com pergunta contextual.
- [ ] Caso: timeout forçado e transferência automática.
- [ ] Caso: falha OpenAI e fallback Groq.
- [ ] Caso: falha total e transferência.
- [ ] Caso: tenant A/B com modelos diferentes.

