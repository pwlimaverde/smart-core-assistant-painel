# Chat Integrado — Pasta de Planejamento

Iniciativa de transformar o painel num substituto fluido do WhatsApp Web, com atendimento integrado ao kanban e **adaptação do cliente Django (`evolution_sync`) para consumir o Evolution Go** já em produção nos servidores dos tenants.

> ⚠️ **Fora do escopo:** deploy, configuração e operação dos servidores Evolution Go (responsabilidade do devops do servidor — Hostinger, ex.: container `paulo-ecoprint-evolution`, repo `paulo-ecoprint-server`). Aqui tratamos apenas do **cliente** Django que fala com esse servidor.
>
> **Modelo de uso:** o tenant nunca toca em SSH/Docker. Ele preenche apenas `server_url` + Global API Key no formulário `tenants/config/evolution/`, e o **sistema automaticamente** cria instâncias, configura webhooks, busca QR Code, sincroniza status e baixa mídia. Se algo no servidor exige intervenção (ex.: ativar licença, corrigir CORS), o sistema **detecta** e **avisa o usuário** via flag de erro na tela — operador escala para o devops do servidor.
>
> **Status do servidor `paulo-ecoprint-evolution` em 2026-05-19 10:27 UTC:** ✅ Licença ativada (`Key f65f53d0...4072`), `GET /instance/all` retornando `200 OK` com lista vazia. Servidor pronto para receber o primeiro provisioning automático pelo sistema. Detalhes e histórico na [§8.2 do companion](./evolution_go_migracao.md).

## Documentos desta pasta

| Documento | Foco | Tamanho |
|---|---|---|
| [`chat_whatsapp_experiencia_completa.md`](./chat_whatsapp_experiencia_completa.md) | **Plano principal** — mapa do gap UX vs WhatsApp Web, roadmap em 4 fases, modelo de dados, endpoints Django, sequência de 5 PRs, métricas. | ~370 linhas |
| [`evolution_go_migracao.md`](./evolution_go_migracao.md) | **Companion técnico** — adaptação de baixo nível do app `evolution_sync` (endpoints v2→Go, payload do webhook, modelos novos, plano de cutover, checklist de pressupostos com o devops do tenant). | ~290 linhas |

> Os documentos são **complementares e não duplicados**: o principal trata do produto (o que o atendente vai ver); o companion trata da infraestrutura (como o backend se conecta com o Evolution Go).

## Estado da branch atual

Branch `feature/chat-whatsapp-redesign` (não-mergeada ainda) já entrega:
- Mídia visível inline (imagem, áudio, vídeo, PDF)
- Lightbox para imagem/vídeo + iframe preview de PDF
- Toggle "Ver análise IA" (transcrição/resumo escondidos por padrão)
- Card kanban com `contato_nome` e `assunto` em linhas separadas
- Normalização de `push_name` (evita lixo permanente no `Contato`)
- Campos novos em `Mensagem`: `arquivo_midia` (FileField) + `analise_midia` (TextField)

## Próximos passos

1. **Iniciar workflow PREVC** no ai-context (`workflow-init` chamado em paralelo a este README).
2. **Sequência de PRs** definida no plano principal §7:
   - PR 1: Read receipts + auto-mark-read + `MESSAGE_UPDATE`
   - PR 2: Date separators + agrupamento + scroll-to-bottom + drag&drop
   - PR 3: Reply (mensagem citada)
   - PR 4: Presence bidirecional
   - PR 5: Gravação de áudio no painel
3. **Adaptação do cliente para Evolution Go** corre em paralelo (companion doc §9), bloqueando os PRs que dependem dos endpoints novos. O servidor Go em si já está em produção — apenas precisamos validar a checklist do §8 com o devops do tenant antes de cada cutover.

## Como atualizar este planejamento

- Mudanças de produto/UX → editar `chat_whatsapp_experiencia_completa.md`.
- Mudanças de endpoint/payload/modelo Evolution → editar `evolution_go_migracao.md`.
- Cada documento mantém suas próprias referências bibliográficas.
- Após cada PR mergeado, marcar o item correspondente na §1 do plano principal de ❌/⚠️ para ✅.
