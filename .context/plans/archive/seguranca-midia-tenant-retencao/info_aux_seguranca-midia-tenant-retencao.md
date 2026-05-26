# Documentação Auxiliar — Segurança e retenção de mídia por tenant

> Gerado em: 2026-05-25
> Plano canônico: `.context/plans/seguranca-midia-tenant-retencao.md`
> Plano completo: `.context/plans/seguranca-midia-tenant-retencao/plano_completo_seguranca-midia-tenant-retencao.md`

Versões (de `pyproject.toml`): `django==5.2.7`, `celery` (via langchain stack), `django-celery-beat`. Sem libs novas. nginx em produção (infra).

## Django 5.2 — FileField, serving, exclusão de arquivo
Library ID context7: `/websites/djangoproject_en_5_2`

### `upload_to` callable (isolamento por tenant)
Confirmado: `upload_to` aceita função `(instance, filename) -> str`.
```python
def media_upload_to(instance, filename):
    # MEDIA_ROOT/midias_atendimento/<tenant_slug>/<Y>/<m>/<filename>
    from smart_core_assistant_painel.app.tenants.middleware import get_current_tenant
    from django.utils import timezone
    t = get_current_tenant()
    slug = getattr(t, "slug", "") or "_shared"
    now = timezone.now()
    return f"midias_atendimento/{slug}/{now:%Y}/{now:%m}/{filename}"
```

### Servir via X-Accel-Redirect (NÃO usar FileResponse)
A doc confirma `HttpResponse` com headers manuais. Para X-Accel-Redirect o corpo é **vazio** e o nginx entrega o arquivo:
```python
resp = HttpResponse()  # corpo vazio
resp["X-Accel-Redirect"] = "/protected-media/" + arquivo.name  # nome relativo ao MEDIA_ROOT
resp["Content-Type"] = mimetype or "application/octet-stream"
resp["Content-Disposition"] = f'inline; filename="{nome}"'
# NÃO definir Content-Length (o nginx define).
return resp
```
- **`FileResponse` NÃO serve aqui**: ela transmitiria o arquivo pelo Gunicorn, anulando o ganho do X-Accel. Usar `HttpResponse` com header.

### Remover arquivo (retenção) — `FieldFile.delete()`
- `FieldFile.delete(save=True)` remove o arquivo do storage **e limpa os atributos do campo**.
- Ao deletar uma model, os arquivos relacionados **não** são removidos automaticamente (limpeza manual) — por isso a task de retenção.
- Padrão para retenção (limpar só o binário, eficiente):
```python
m.arquivo_midia.delete(save=False)   # apaga do storage + limpa o campo em memória
m.save(update_fields=["arquivo_midia"])
```

## nginx — X-Accel-Redirect com location interna
Fontes: [Nginx X-Accel Explained](https://blog.horejsek.com/nginx-x-accel-explained/), [Serve Protected Content X-Accel (Nginx+Django)](https://pavanskipo.medium.com/how-to-serve-protected-content-using-x-accel-nginx-django-fd529e428531)

- Bloco interno (só acessível via X-Accel-Redirect emitido pelo app):
```nginx
location /protected-media/ {
    internal;
    alias /var/www/media/;   # usar ALIAS (não root) para o prefixo /protected-media/ não entrar no path do arquivo
}
```
- Django retorna `X-Accel-Redirect: /protected-media/<path-relativo>` e o nginx serve de `/var/www/media/<path-relativo>`.
- **Gotchas:**
  - `alias` (não `root`): com `root`, o prefixo `/protected-media/` seria concatenado ao caminho no disco.
  - O valor do header deve ser **URL-encoded** se houver caracteres especiais. Nossos nomes são sanitizados (alnum/`-`/`_`) e o slug do tenant é kebab-case → seguro. Ainda assim, aplicar `urllib.parse.quote` no path por robustez.
  - O `location /media/` público atual deve ser **removido/!convertido para internal** para fechar o acesso direto.

## Celery / django-celery-beat — agendamento diário
Library IDs: `/websites/celeryq_dev_en_stable`, `/celery/django-celery-beat`

- O projeto usa `CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"` e `CELERY_BEAT_SCHEDULE` (dict) sincronizado ao DB no startup do beat.
- Para diário, usar `crontab` de `celery.schedules`:
```python
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    # ... existentes ...
    "purge-old-media": {
        "task": "smart_core_assistant_painel.app.atendimentos.tasks.purge_old_media_all_tenants",
        "schedule": crontab(hour=3, minute=30),
    },
}
```
- A task itera tenants e usa `set_current_tenant(tenant)` por tenant (padrão de `evolution_sync/tasks.py:keepalive_evolution_instances`). Como roda no beat→worker, não recebe `tenant_slug`; portanto **não** usa `TenantTask` por slug — gerencia o contexto manualmente (igual ao keepalive).

## Notas gerais
- Sem dependências novas; tudo já disponível (Django 5.2, Celery, django-celery-beat, nginx).
- Multi-tenant: isolamento por DB (router) + agora por path (upload_to) + autorização por request (view) — defesa em profundidade.
