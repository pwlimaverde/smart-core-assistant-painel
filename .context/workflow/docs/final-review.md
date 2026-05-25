# Final Review — seguranca-midia-tenant-retencao
Data: 2026-05-25 · Modelo: Opus · Diff: working tree (não commitado)

## Veredito: CORRIGIDO

> Escopo auditado: mudanças **não commitadas** (working tree) nos caminhos declarados
> pelo plano. A branch `feature/refatoracao-modular-atendimento` acumula trabalho
> heterogêneo (203 arquivos em `master...HEAD`) — fora de escopo, conforme Etapa 0.4 do skill.

## 1. Plano vs. Implementado

| Item do plano | Status | Observação |
|---|---|---|
| **F1**: `media_upload_to(instance, filename)` callable | ✅ | `models.py:1006` retorna `midias_atendimento/{slug}/{Y}/{m}/{filename}`. |
| F1: usa `get_current_tenant()` + slug, fallback `_shared` | ✅ | `slug = getattr(t, "slug", "") or "_shared"`. |
| F1: import local de `get_current_tenant` | ✅ | Import dentro do callable, de `tenants.middleware` (linha 15). Evita ciclo. |
| F1: `arquivo_midia` aponta para o callable | ✅ | `models.py:1094` `upload_to=media_upload_to`. |
| F1: migration 0010 AlterField | ✅ | Depende de 0009; AlterField com `upload_to=...media_upload_to`. Não move legados. |
| **F2**: `MensagemMediaView` com `@_require_workspace` | ✅ | `views_api.py:465`. Login+tenant+permissão. |
| F2: checagem `_can_access_atendimento` | ✅ | Usa `mensagem.atendimento_id`; retorna 403 se negado. |
| F2: isolamento por DB do tenant (404 p/ outro tenant) | ✅ | `Mensagem.objects.filter(id=...).first()` roteado ao DB do tenant → 404 natural. |
| F2: `HttpResponse` vazio (NÃO FileResponse) | ✅ | `response = HttpResponse()`. |
| F2: `X-Accel-Redirect` com `quote(safe="/")` | ✅ | `urllib.parse.quote(arquivo.name, safe="/")` → `/protected-media/{quoted}`. |
| F2: Content-Type via mimetypes, fallback octet-stream | ✅ | `mimetypes.guess_type` + fallback. |
| F2: Content-Disposition inline | ✅ | `inline; filename="..."`. |
| F2: SEM Content-Length | ✅ | Não definido (nginx define). |
| F2: rota em api_urls | ✅ | `messages/<int:mensagem_id>/media/` → `mensagem_media`. |
| F2: nginx `/protected-media/` internal + `alias` | ✅ | `internal;` + `alias /var/www/media/;` (não `root`). |
| F2: `/media/` público removido | ✅ | Bloco substituído. |
| F2: `selectors._extract_media` → URL da view | ✅ | `src = f"/workspace/chat/api/messages/{m.id}/media/"`. Fallback base64 preservado. |
| **F3**: `MEDIA_RETENTION_DAYS` via config default 30 | ✅ | `config("MEDIA_RETENTION_DAYS", default=30, cast=int)`. |
| F3: task global sem TenantTask, itera `Tenant.objects.all()` | ✅ | `@shared_task(bind=True)` sem `base=TenantTask`. |
| F3: `set_current_tenant`/`set_current_tenant(None)` no finally | ✅ | Loop por tenant com `finally: set_current_tenant(None)`. |
| F3: `delete(save=False)` + `save(update_fields=["arquivo_midia"])` | ✅ | Preserva `analise_midia`/`resumo_midia`. |
| F3: `CELERY_BEAT_SCHEDULE` crontab(3,30) + import crontab | ✅ | `from celery.schedules import crontab`; `crontab(hour=3, minute=30)`. |

➕ **Além do plano**: `selectors.py:493` recebeu reformatação cosmética de `analise_midia` (one-liner) — irrelevante, não muda comportamento.

## 2. Correções Aplicadas

| Arquivo:linha | Problema | Correção |
|---|---|---|
| `migrations/0010_alter_mensagem_arquivo_midia.py:3` | ruff `I001`: bloco de import não ordenado | Reordenado: `from django.db ...` primeiro, depois import de 1ª parte. |
| `atendimentos/tasks.py:121` | pyright: `reportUnknownParameterType`/`reportMissingParameterType` no `self` da task `bind=True` | Adicionado `# type: ignore[no-untyped-def]`, mesmo padrão de `keepalive_evolution_instances`. |

## 3. Decisões Autônomas (revisar depois)
- **`# type: ignore[no-untyped-def]` no `self`**: replicou a convenção já estabelecida (keepalive task) em vez de remover `bind=True`. `self` não é usado; mantido por consistência.
- Reformatação cosmética em `selectors.py:493` veio no working tree; mantida por ser benigna.

## 4. Revalidação
- lint (ruff, escopo do plano): ✅ — migration/tasks/views_api/api_urls/selectors/settings passam. Único resíduo no escopo é o `F821 operacional` em `models.py`, **pré-existente em HEAD**.
- type-check (pyright, escopo do plano): ✅ — `tasks.py` limpo após correção. `settings.py:109` é erro **pré-existente** fora do escopo.
- testes: N/A (diretriz: não criar testes)

## 5. Pendências (escopo extra ou fora do plano)
- `ruff check src/` reporta ~25 erros project-wide, todos fora do escopo (ex.: `trello_adapter.py:332` F841; `models.py` F821 `operacional`). NÃO corrigidos por diretriz.
- `pyright` reporta `settings.py:109` (pré-existente) e ~97 warnings de tipos parciais (Django/Celery), pré-existentes/fora de escopo.
- Migration importa o módulo `...atendimentos.models` (gerado pelo Django via `deconstruct` do callable) — comportamento padrão e correto.

**Veredito final: CORRIGIDO** — implementação fiel ao plano nas 3 fases; 2 desvios de qualidade corrigidos; lint+type-check limpos no escopo. Erros remanescentes são pré-existentes/fora de escopo.
