# Technical Specification - Sprint Features Q1/2026

## Features
- Whitelist UI no Painel de Configurações
- Teste de Treinamento com Chat Interativo

## Resumo Técnico
Implementação de views Django, templates Tailwind CSS e endpoints AJAX para duas features no dashboard multi-tenant.

## Arquitetura

### Componentes Afetados

| Componente | Mudança | Arquivos |
|------------|---------|----------|
| Views (settings_manager) | Novas views CRUD whitelist | `app/settings_manager/views.py` |
| URLs (settings_manager) | Novo urls.py | `app/settings_manager/urls.py` |
| Forms (settings_manager) | Novo forms.py | `app/settings_manager/forms.py` |
| Templates (settings_manager) | Novos templates | `app/settings_manager/templates/` |
| URLs (core) | Include configuracoes | `app/core/urls.py` |
| Template (core) | Link sidebar | `app/core/templates/base_dashboard.html` |
| Views (treinamento) | Novas views teste/feedback | `app/treinamento/views.py` |
| URLs (treinamento) | Novas URLs | `app/treinamento/urls.py` |
| Models (treinamento) | Novo QueryTestFeedback | `app/treinamento/models.py` |
| Templates (treinamento) | Novo template teste | `app/treinamento/templates/` |

## Design Detalhado

### Feature 3: Whitelist UI

#### Views
- `configuracoes_index(request)` → Página principal de configurações
- `configuracoes_whitelist(request)` → Lista whitelist
- `whitelist_adicionar(request)` → Form de adição
- `whitelist_editar(request, id)` → Form de edição
- `whitelist_excluir(request, id)` → Exclusão com confirmação
- `whitelist_toggle(request, id)` → Toggle ativo/inativo (AJAX)

#### Form
```python
class WhiteListForm(forms.ModelForm):
    class Meta:
        model = WhiteList
        fields = ['name', 'phone_number', 'active']
```

#### URLs
```
/configuracoes/              → index
/configuracoes/whitelist/    → lista
/configuracoes/whitelist/adicionar/    → form criar
/configuracoes/whitelist/<id>/editar/  → form editar
/configuracoes/whitelist/<id>/excluir/ → deletar
/configuracoes/whitelist/<id>/toggle/  → toggle ativo
```

### Feature 1: Teste de Treinamento

#### Model
```python
class QueryTestFeedback(models.Model):
    mensagem_original = models.TextField()
    resposta_bot = models.TextField()
    resposta_corrigida = models.TextField(blank=True)
    avaliacao = models.CharField(max_length=10)
    confiabilidade = models.FloatField()
    entidades_json = models.JSONField(default=dict)
    intents_json = models.JSONField(default=dict)
    documentos_ids = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(AUTH_USER_MODEL)
```

#### Views
- `testar_resposta_query(request)` → POST AJAX, retorna análise JSON
- `feedback_resposta_query(request)` → POST AJAX, registra feedback

#### URLs
```
/treinamento/testar-resposta/    → testar_resposta_query
/treinamento/feedback-resposta/  → feedback_resposta_query
```

## Segurança
- [x] Isolamento de tenant via TenantMiddleware
- [x] CSRF em todos os forms e AJAX (X-CSRFToken header)
- [x] Verificação de login_required
- [x] Verificação de permissões admin
- [x] Inputs validados via Django Forms

## Testes
- Testes manuais pós-implementação (sem testes automatizados neste sprint)

## Checklist de Implementação
- [ ] Feature 3: Views settings_manager
- [ ] Feature 3: Forms whitelist
- [ ] Feature 3: URLs settings_manager
- [ ] Feature 3: Templates configurações
- [ ] Feature 3: Link sidebar
- [ ] Feature 1: Model QueryTestFeedback
- [ ] Feature 1: Views teste/feedback
- [ ] Feature 1: URLs treinamento
- [ ] Feature 1: Template testar_query
- [ ] Feature 1: JavaScript interatividade
- [ ] Feature 1: Link navegação
