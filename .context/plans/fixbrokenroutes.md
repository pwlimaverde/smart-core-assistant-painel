# Correção de todas as rotas quebradas (Erro 500) em produção

Corrigir a quebra generalizada de rotas e telas de formulários no painel dos tenants em ambiente de produção. O erro ocorreu devido ao uso de `{{ csrf_input(request) }}` em templates sob o Jinja2, que colide com a injeção local de um objeto lazy do CSRF do Django (que não é chamável), resultando em `TypeError: '__proxy__' object is not callable`.

## Proposed Changes

### Design System Templates

Alterar todas as ocorrências de `{{ csrf_input(request) }}` para `{{ csrf_input }}` em todos os templates HTML do sistema de design que renderizam formulários.

#### [MODIFY] Todos os templates afetados em [templates](file:///c:/PROJETOS/PYTHON/APPS/smart-core-assistant-painel/src/smart_core_assistant_painel/modules/design_system/templates/)
- `whitelist.html`
- `whitelist_confirm.html`
- `whitelist_form.html`
- `config_ai.html`
- `config_database.html`
- `config_evolution.html`
- `config_form.html`
- `config_trello.html`
- `signup.html`
- `register_payment.html`
- `step_1_tenant.html`
- `step_2_payment.html`
- `step_3_config.html`
- `activate.html`
- `edit_permissions.html`
- `invite.html`
- `cadastrar_query_compose.html`
- `pre_processamento.html`
- `treinar_ia.html`
- `verificar_query_compose.html`
- `verificar_treinamentos.html`
- `cadastro.html`
- `login.html`
- `password_reset_confirm.html`
- `password_reset_form.html`

## Verification Plan

### Automated/Simulated Tests
- Executar uma simulação de requisição logada no shell do contêiner de produção usando o Django Client para garantir que a renderização da página `/apps/tenants/config/database/` não resulte mais em erro 500.

```bash
"from django.contrib.auth import get_user_model; from django.test import Client; User = get_user_model(); user = User.objects.get(username='comercialecoprintgrafica@gmail.com'); client = Client(HTTP_HOST='smartcoreassistant.com.br'); client.force_login(user); r = client.get('/apps/tenants/config/database/'); print(r.status_code)" | ssh hostinger-root "docker exec -i smartcoreassistant_app python -m smart_core_assistant_painel.app.manage shell"
```

### Manual Verification
- Acessar a URL `https://smartcoreassistant.com.br/apps/tenants/config/database/` via navegador com o usuário do tenant logado e verificar se a página carrega corretamente sem exibir a tela de erro 500.
