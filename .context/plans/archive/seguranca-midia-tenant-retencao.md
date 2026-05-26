---
status: filled
generated: 2026-05-25
agents:
  - type: "security-auditor"
    role: "Isolamento por tenant e controle de acesso à mídia"
  - type: "backend-specialist"
    role: "View autenticada, X-Accel-Redirect, upload_to por tenant e task de retenção"
  - type: "devops-specialist"
    role: "Ajuste do nginx (location interna) e deploy"
docs:
  - "security.md"
  - "architecture.md"
  - "data-flow.md"
phases:
  - id: "phase-1"
    name: "Isolamento por tenant no caminho (upload_to dinâmico)"
    prevc: "E"
    agent: "backend-specialist"
    status: "pending"
  - id: "phase-2"
    name: "Serving autenticado + X-Accel-Redirect (view + nginx)"
    prevc: "E"
    agent: "backend-specialist"
    status: "pending"
  - id: "phase-3"
    name: "Retenção de 30 dias (task Celery beat diária)"
    prevc: "E"
    agent: "backend-specialist"
    status: "pending"
---

# Segurança e retenção do armazenamento de mídia por tenant

> Isolar a mídia por tenant no path, servir arquivos por view autenticada com
> `X-Accel-Redirect` (acesso só do dono da instância, com checagem de atendimento),
> e apagar o binário após 30 dias via task Celery beat diária (mantendo análise/resumo).

## Artefatos detalhados
- **Plano completo:** [`seguranca-midia-tenant-retencao/plano_completo_seguranca-midia-tenant-retencao.md`](./seguranca-midia-tenant-retencao/plano_completo_seguranca-midia-tenant-retencao.md)
- **Doc auxiliar (validações Django/Celery/nginx):** [`seguranca-midia-tenant-retencao/info_aux_seguranca-midia-tenant-retencao.md`](./seguranca-midia-tenant-retencao/info_aux_seguranca-midia-tenant-retencao.md)

## Problema (avaliação de segurança)
1. nginx serve `/media/` **público, sem autenticação** → qualquer um com a URL baixa o arquivo.
2. `upload_to="midias_atendimento/%Y/%m/"` **sem slug do tenant** → arquivos de todos os tenants no mesmo volume, sem isolamento no filesystem.
3. Sem retenção → arquivos acumulam (risco de disco).

## Decisões confirmadas
- Serving: **view autenticada + `X-Accel-Redirect`**.
- Retenção: apagar **apenas o binário** após 30 dias (mantém `analise_midia`/`resumo_midia` e a mensagem).

## Fases (PREVC: E)

### Phase 1 — Isolamento por tenant
`media_upload_to(instance, filename)` → `midias_atendimento/<tenant_slug>/%Y/%m/arquivo` (usa `get_current_tenant()`). Migration `0010` (AlterField; não move legados).

### Phase 2 — Serving autenticado + X-Accel-Redirect
View `MensagemMediaView` em `chat_evolution` (`/workspace/chat/api/messages/<id>/media/`): `@_require_workspace` + `_can_access_atendimento` + isolamento por DB do tenant → `X-Accel-Redirect: /protected-media/<arquivo.name>`. nginx: `/media/` público → `location /protected-media/ { internal; alias /var/www/media/; }`. `_extract_media.src` passa a apontar para a view.

### Phase 3 — Retenção 30 dias
Setting `MEDIA_RETENTION_DAYS=30`; task `purge_old_media_all_tenants` (itera tenants, `set_current_tenant`, remove `arquivo_midia` de mensagens >30d, mantém textos); `CELERY_BEAT_SCHEDULE` diário (crontab 03:30).

## Conformidade
Multi-Tenant (DB + path + autorização por request); sem libs novas; sem credenciais novas (`MEDIA_RETENTION_DAYS` opcional).

## Verificação
makemigrations 0010 + migrate; pyright/ruff limpos; novo arquivo em `.../<slug>/...`; `/media/` direto → 404; view deslogado → bloqueia; logado com acesso → serve; id de outro tenant → 404; mídia carrega/baixa no chat; task de retenção remove binário e preserva análise/resumo; deploy rebuild app+workers + reload nginx.
