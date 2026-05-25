# Plano Completo — Segurança e retenção do armazenamento de mídia por tenant

## Contexto

Após corrigir o carregamento de mídia (volume do worker), ficou exposto que o armazenamento de arquivos tem **falhas de segurança** e não tem **retenção**:

1. **Acesso público sem autenticação** — `docker/nginx/conf.d/smartcore.conf` serve `location /media/ { alias /var/www/media/; }` sem qualquer verificação de login/tenant. Qualquer um com a URL baixa o arquivo. Nomes baseados no message-id do WhatsApp = segurança por obscuridade, não controle de acesso.
2. **Sem isolamento por tenant no filesystem** — `Mensagem.arquivo_midia` usa `upload_to="midias_atendimento/%Y/%m/"` (sem slug do tenant). Bancos são isolados (DB router), mas os arquivos ficam todos no mesmo volume `smartcore_media_files`, sem barreira entre tenants.
3. **Sem retenção** — arquivos acumulam indefinidamente (risco de disco).

**Contexto de tenant disponível:** `get_current_tenant()` / `get_current_tenant_slug()` (`tenants/tenant_context.py`) funcionam no worker via `TenantTask` (`tenants/celery.py`). Tenants ficam em subdomínios; o middleware resolve o tenant por request. `Mensagem` é roteada para o DB do tenant (`tenants/db_router.py`).

**Decisões do dono (confirmadas):**
- Serving: **view autenticada + `X-Accel-Redirect`**.
- Retenção: apagar **apenas o binário** após 30 dias (mantém `analise_midia`/`resumo_midia` e a mensagem).

---

## FASE 1 — Isolamento por tenant no caminho (PREVC: E · backend)

- `atendimentos/models.py`: trocar `upload_to="midias_atendimento/%Y/%m/"` por um **callable** `media_upload_to(instance, filename)`:
  - usa `get_current_tenant()` → `slug`; retorna `f"midias_atendimento/{slug or '_shared'}/{Y}/{m}/{filename}"`.
  - import local de `get_current_tenant` dentro do callable (evita ciclo de import no módulo de models).
- Migration `0010_*` (AlterField em `arquivo_midia`). **Não move arquivos existentes** (ficam no caminho antigo sem slug); a view de serving e a retenção operam sobre `arquivo_midia.name` qualquer que seja o caminho, então não há quebra.

## FASE 2 — Serving autenticado + X-Accel-Redirect (PREVC: E · backend + infra)

- **Nova view** em `chat_evolution/views_api.py` (ex. `MensagemMediaView`):
  - rota em `chat_evolution/api_urls.py`: `messages/<int:mensagem_id>/media/` → resolve para `/workspace/chat/api/messages/<id>/media/`.
  - `@_require_workspace` (login + tenant); `Mensagem.objects.filter(id=...).first()` (roteado ao DB do tenant → mídia de outro tenant retorna 404 naturalmente); `_can_access_atendimento(request, m.atendimento_id)`; exige `m.arquivo_midia`.
  - resposta **`HttpResponse` com corpo VAZIO** (NÃO `FileResponse` — ela transmitiria pelo Gunicorn e anularia o X-Accel) + headers:
    - `X-Accel-Redirect: /protected-media/<quote(arquivo.name)>`
    - `Content-Type: <mimetype>` (dos metadados; fallback `application/octet-stream`)
    - `Content-Disposition: inline; filename="<nome>"`
    - **não** definir `Content-Length` (o nginx define).
  - Para download, o front usa o attr `download` (já implementado) sobre a mesma URL.
- **nginx** (`docker/nginx/conf.d/smartcore.conf`): substituir o bloco público `location /media/` por **`location /protected-media/ { internal; alias /var/www/media/; }`** (só acessível via X-Accel-Redirect interno). Usar **`alias`** (não `root`) para o prefixo não entrar no path em disco. Remover o `/media/` público.
- **`chat_evolution/selectors.py` `_extract_media`**: `src` passa a apontar para a URL da view (`/workspace/chat/api/messages/{m.id}/media/`) em vez de `arquivo.url`. Manter fallback base64 (data URI) só quando não há arquivo persistido.
- Front-end (`chat_message.html`, `chat_alpine.js`): nenhuma mudança estrutural — continuam usando `m.media.src` (agora a URL autenticada). `downloadMedia`/lightbox seguem funcionando (mesma origem, com sessão/cookies).

## FASE 3 — Retenção de 30 dias (PREVC: E · backend)

- **Setting** `MEDIA_RETENTION_DAYS = config("MEDIA_RETENTION_DAYS", default=30, cast=int)` em `core/settings.py`.
- **Task** em `atendimentos/tasks.py`: `purge_old_media_all_tenants()` (global, `@shared_task` SEM `TenantTask`/slug — gerencia contexto manualmente como o keepalive):
  - itera `Tenant.objects.all()` (DB default); para cada um `set_current_tenant(tenant)` (padrão de `evolution_sync/tasks.py:keepalive_evolution_instances`), depois:
    - `Mensagem.objects.filter(timestamp__lt=now-RETENTION).exclude(arquivo_midia="").exclude(arquivo_midia__isnull=True)` → para cada, `m.arquivo_midia.delete(save=False)` (remove do storage **e** limpa o atributo do campo) + `m.save(update_fields=["arquivo_midia"])`. Mantém `analise_midia`/`resumo_midia`.
    - `set_current_tenant(None)` no finally.
  - logar contagem por tenant.
- **CELERY_BEAT_SCHEDULE** (`core/settings.py`): adicionar `purge-old-media` com `crontab(hour=3, minute=30)` (diária, madrugada). Import: `from celery.schedules import crontab`.

---

## Arquivos críticos
- `src/.../app/atendimentos/models.py` (callable `media_upload_to` + AlterField) + migration `0010`
- `src/.../app/chat_evolution/views_api.py` (`MensagemMediaView`) + `chat_evolution/api_urls.py`
- `src/.../app/chat_evolution/selectors.py` (`_extract_media` → URL da view)
- `docker/nginx/conf.d/smartcore.conf` (`/media/` → `/protected-media/ internal`)
- `src/.../app/atendimentos/tasks.py` (`purge_old_media_all_tenants`)
- `src/.../app/core/settings.py` (`MEDIA_RETENTION_DAYS`, `CELERY_BEAT_SCHEDULE`)
- Reuso: `tenants/tenant_context.py`, `tenants/celery.py` (TenantTask), padrão de `evolution_sync/tasks.py`, `_can_access_atendimento`/`_require_workspace` (views_api.py)

## Conformidade
- Multi-Tenant respeitado (isolamento por DB + agora por path + autorização por request). Sem credenciais novas em `.env` (apenas `MEDIA_RETENTION_DAYS` opcional). Sem libs novas.

## Verificação (end-to-end)
1. `makemigrations atendimentos` (0010) + `migrate`; `pyright`/`ruff` limpos no escopo.
2. **Isolamento:** novo arquivo é salvo em `midias_atendimento/<slug>/...`.
3. **Auth:** acessar `/workspace/chat/api/messages/<id>/media/` **deslogado** → redirect/login (não serve). Logado, com acesso ao atendimento → serve via X-Accel. Tentar id de outro tenant → 404. Acessar `/media/...` direto → 404 (não mais público).
4. **Mídia no chat:** imagem/áudio/vídeo/PDF carregam e baixam (via URL autenticada).
5. **Retenção:** rodar a task manualmente (`purge_old_media_all_tenants.delay()` ou via shell) com um registro forjado antigo → binário removido, `analise_midia`/`resumo_midia` preservados.
6. Deploy: rebuild app + workers + reload nginx (config nova); beat carrega o novo schedule.

## Correções aplicadas (validação contra docs atuais — /restructure-plan)
Libs: `django==5.2.7`, `celery` + `django-celery-beat`, nginx (infra). Nenhuma lib nova. Docs: context7 `/websites/djangoproject_en_5_2`, `/celery/django-celery-beat`; nginx via fontes oficiais/comunidade.

- **X-Accel-Redirect deve usar `HttpResponse` (corpo vazio) + headers, NÃO `FileResponse`** — confirmado na doc do Django: `FileResponse` transmite o arquivo pelo processo (Gunicorn), o que anularia o ganho do X-Accel. Corrigido na Fase 2.
- **Não definir `Content-Length`** na resposta da view (o nginx define ao servir o arquivo). Definir `Content-Type` e `Content-Disposition` explicitamente.
- **nginx: usar `alias` (não `root`)** na `location /protected-media/ { internal; }` — com `root` o prefixo entraria no caminho em disco. Confirmado nas fontes nginx/Django.
- **URL-encode do path** no header (`urllib.parse.quote`) por robustez — nomes já são sanitizados (alnum/`-`/`_`) e slug é kebab-case, mas mantém-se a segurança.
- **`FieldFile.delete(save=False)` já limpa o atributo do campo** (doc Django) — então basta `delete(save=False)` + `save(update_fields=["arquivo_midia"])`; mantém `analise_midia`/`resumo_midia`.
- **Retenção: task global sem `TenantTask`/slug** — gerencia o contexto com `set_current_tenant`/`set_current_tenant(None)` manualmente (igual ao `keepalive_evolution_instances`), pois roda pelo beat sem `tenant_slug`.
- **`crontab` de `celery.schedules`** para o agendamento diário, sincronizado pelo `DatabaseScheduler` já em uso.

## Riscos / atenção
- **X-Accel path:** o `alias /var/www/media/` + `X-Accel-Redirect: /protected-media/<arquivo.name>` precisa casar exatamente (sem barra dupla). Testar com 1 arquivo antes de validar tudo.
- **Arquivos legados** sem slug de tenant continuam servidos (a view autoriza por mensagem), mas estão num path comum; a retenção de 30 dias os remove naturalmente.
- **nginx:** enquanto o deploy não roda, `/media/` muda de comportamento — coordenar rebuild de app (novas URLs) + reload nginx juntos para não quebrar exibição.
