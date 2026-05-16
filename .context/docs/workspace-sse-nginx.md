# Workspace SSE — Configuração de infraestrutura (E.1.16)

Documento operacional do endpoint `/workspace/events/` (Server-Sent Events,
async view nativa do Django 4.1+). Não há rota ASGI dedicada — o mesmo
worker Uvicorn atende tudo.

## 1. Worker Uvicorn (Docker Compose)

Substituir o `command` do serviço Django (gunicorn sync) por:

```yaml
command: >-
  uvicorn smart_core_assistant_painel.app.core.asgi:application
  --host 0.0.0.0
  --port 8000
  --workers 3
  --proxy-headers
  --forwarded-allow-ips=*
  --timeout-keep-alive 75
  --no-access-log
```

Notas:

- `--workers 3` ajusta à CPU do KVM Hostinger (`grep -c ^processor /proc/cpuinfo`).
  Cada worker é multiplex async (não bloqueia em SSE).
- `--proxy-headers` confia em `X-Forwarded-*` do Nginx.
- `--timeout-keep-alive 75` deve ser maior que o intervalo de heartbeat
  configurado em `views_sse.py` (25s) somado a folga de rede.

Alternativa Gunicorn:

```text
gunicorn smart_core_assistant_painel.app.core.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  --workers 3 \
  --bind 0.0.0.0:8000 \
  --timeout 0
```

## 2. Nginx (proxy_pass)

```nginx
location /workspace/events/ {
    proxy_pass http://app:8000;
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Crítico para SSE
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 1h;
    proxy_send_timeout 1h;
    chunked_transfer_encoding off;
    add_header X-Accel-Buffering no always;
}
```

Demais rotas `/workspace/*` mantêm a configuração padrão (Django sync).

## 3. Healthcheck

A rota `/health/` permanece inalterada. Após rollout, validar manualmente:

```bash
curl -N -H "Accept: text/event-stream" https://<host>/workspace/events/
```

Deve receber `: connected` imediatamente e `: ping` a cada ~25s.

## 4. Troubleshooting

| Sintoma                                | Causa provável                      | Mitigação                                                                      |
|----------------------------------------|--------------------------------------|--------------------------------------------------------------------------------|
| EventSource fecha em 60s               | Nginx `proxy_read_timeout` baixo    | Ajustar para `1h` (acima)                                                      |
| EventSource recebe burst de eventos    | `proxy_buffering` ligado            | Adicionar `proxy_buffering off`                                                |
| Erro `redis.asyncio` indisponível      | Pacote `redis>=4.2` ausente         | `pip show redis` — versão >=4.2 já inclui `redis.asyncio`                      |
| Sem eventos no UI mas Redis publica    | Slug do tenant não bate             | Verificar `tenant_slug` na request e canal `sse:<slug>:events` via `redis-cli` |
| Worker trava em SSE                    | Rodando sob Gunicorn sync           | Trocar para Uvicorn (ver item 1)                                               |

## 5. Comandos úteis

```bash
# Acompanhar eventos publicados (substitua <slug>)
docker exec -it <redis_container> redis-cli SUBSCRIBE 'sse:<slug>:events'

# Forçar reconnect manual (DevTools console)
window.workspaceStore && document.getElementById('workspace-root')
  ._x_dataStack[0].connectSSE()
```
