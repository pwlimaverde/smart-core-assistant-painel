# Correção de Filtros DTL Incompatíveis no Jinja2

Registrar filtros customizados equivalentes do Django (date, yesno, pluralize, truncatechars, cut) no adaptador do ambiente Jinja2 (`jinja2_env.py`) e refatorar os templates do Design System de sintaxe DTL (`|filtro:arg`) para sintaxe Jinja2 (`|filtro(arg)`).

## Proposed Changes

### Adapters (Jinja2)

#### [MODIFY] [jinja2_env.py](file:///c:/PROJETOS/PYTHON/APPS/smart-core-assistant-painel/src/smart_core_assistant_painel/modules/design_system/adapters/django/jinja2_env.py)
- Implementar as funções Python correspondentes para:
  - `date_filter(value, format_str)`
  - `yesno_filter(value, arg)`
  - `pluralize_filter(value, arg)`
  - `truncatechars_filter(value, num)`
  - `cut_filter(value, arg)`
- Registrar essas funções no mapeamento global de filtros de ambiente `env.filters` em `environment(...)`.

### Design System Templates

Refatorar a sintaxe dos filtros aplicados em todos os arquivos de template detectados.

#### [MODIFY] Todos os templates com filtros DTL em [templates](file:///c:/PROJETOS/PYTHON/APPS/smart-core-assistant-painel/src/smart_core_assistant_painel/modules/design_system/templates/)
- `whitelist.html` (substituir `yesno:` e `date:`)
- `instance_list.html` (substituir `yesno:`)
- `instance_detail.html` (substituir `date:`)
- `verificar_treinamentos.html` (substituir `date:`)
- `verificar_query_compose.html` (substituir `date:`)
- `list.html` de tenants (substituir `date:`)
- `config_debug.html` (substituir `truncatechars:`)
- `backoffice/dashboard.html` (substituir `cut:` e `date:`)
- `settings_manager/.../index.html` (substituir `pluralize:`)

## Verification Plan

### Automated/Simulated Tests
- Simular a requisição logada à URL `/evolution/instances/` através do Django Client remoto no contêiner para garantir que o erro de sintaxe desapareça e a página seja carregada com status 200.
- Executar testes rápidos em `/operacional/whitelist/`, `/apps/tenants/users/` e `/apps/tenants/bo/` para validar a renderização correta de datas e filtros.

```bash
"from django.contrib.auth import get_user_model; from django.test import Client; User = get_user_model(); user = User.objects.get(username='comercialecoprintgrafica@gmail.com'); client = Client(HTTP_HOST='smartcoreassistant.com.br'); client.force_login(user); print('Inst:', client.get('/evolution/instances/').status_code)" | ssh hostinger-root "docker exec -i smartcoreassistant_app python -m smart_core_assistant_painel.app.manage shell"
```

### Manual Verification
- Acessar `https://smartcoreassistant.com.br/evolution/instances/` com o usuário do tenant logado e certificar que a listagem de instâncias renderiza perfeitamente e os badgdes/estados da API Evolution funcionam sem erros.
