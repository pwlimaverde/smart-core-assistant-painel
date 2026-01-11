# Change: Refatorar UI para Padronizar Design System "Smart Core"

## Why

O sistema atualmente possui inconsistências visuais críticas que tornam a aplicação difícil de usar:

1. **Páginas sem sidebar**: URLs como `/treinamento/verificar-treinamentos/` abrem sem a barra lateral, enquanto `/tenants/config/database/` exibe corretamente
2. **Dashboard quebrado**: Cards com tamanhos diferentes e erro visual no final da página
3. **Navegação confusa**: Link "Dashboard" na sidebar direciona para `/tenants/dashboard/` quando deveria ser consistente
4. **Superusuário sem área apropriada**: Visualização completamente quebrada para superusuários que deveriam ser direcionados para `/admin/`
5. **Permissões não respeitadas na UI**: Usuários comuns veem opções que não deveriam (ex: Gestão de Usuários)

A raiz técnica do problema é que templates de `treinamento` estendem `base.html` diretamente em vez de `base_dashboard.html`.

## What Changes

- **MODIFIED**: Templates de `treinamento` agora estendem `base_dashboard.html` em vez de `base.html`
- **MODIFIED**: Redirecionamento no login baseado em tipo de usuário (superuser → admin, tenant user → dashboard)
- **MODIFIED**: Rota `/dashboard/` agora redireciona para `/tenants/dashboard/`
- **ADDED**: Controles de visibilidade na sidebar baseados em permissões
- **ADDED**: Template tag `can_view_module` para verificação de permissões em templates
- **MODIFIED**: Cards do dashboard com altura padronizada (`h-full`)

## Impact

- **Affected specs**: 
  - `template-hierarchy` (padronização de herança de templates)
  - `navigation-permissions` (sidebar baseada em permissões)
  - `login-redirect` (redirecionamento por tipo de usuário)
- **Affected code**:
  - `ui/treinamento/templates/treinamento/*.html` (5 arquivos) - mudança de herança
  - `ui/core/views.py` - redirect em dashboard
  - `ui/usuarios/views.py` - lógica de redirecionamento no login
  - `ui/core/templates/base_dashboard.html` - controles de permissão na sidebar
  - `tenants/templatetags/permission_tags.py` - nova template tag

---

## Problema Detalhado

### Evidências Visuais

As imagens fornecidas demonstram:

| Página | Comportamento Atual | Comportamento Esperado |
|--------|---------------------|------------------------|
| `/tenants/config/database/` | ✅ Sidebar visível, layout correto | Manter |
| `/treinamento/verificar-treinamentos/` | ❌ Página limpa sem sidebar | Exibir sidebar |
| `/tenants/dashboard/` | ⚠️ Cards com tamanhos diferentes | Cards com altura uniforme |

### Causa Raiz

Templates de `treinamento` fazem:
```html
{% extends "base.html" %}  <!-- ERRADO -->
```

Deveriam fazer:
```html
{% extends "base_dashboard.html" %}  <!-- CORRETO -->
```

---

## Escopo

### Incluído
- Correção de herança de templates (`base.html` → `base_dashboard.html`)
- Padronização do Design System (cores, tipografia, componentes)
- Reestruturação da sidebar com navegação baseada em permissões
- Redirecionamento correto por tipo de usuário no login
- Correção de links inconsistentes
- Padronização de altura de cards no dashboard

### Excluído
- Criação de novas funcionalidades de negócio
- Alterações em models ou lógica de negócio
- Refatoração de APIs
- Responsividade mobile (fase futura)

---

## Análise de Impacto

| Área | Nível | Descrição |
|------|-------|-----------|
| Templates | Alto | 5+ arquivos modificados |
| Views | Médio | Ajustes em 2 views (login, dashboard) |
| CSS/Design | Baixo | Apenas padronização de classes existentes |
| Lógica | Baixo | Sem alteração em regras de negócio |
| Testes | Mínimo | Apenas testes manuais de navegação |

---

## Dependências

- Nenhuma nova dependência externa
- Sistema de permissões `TenantUser` já existente
- Template tags `permission_tags` existentes (serão estendidas)

---

## Arquivos Relacionados

| Arquivo | Modificação |
|---------|-------------|
| `treinamento/templates/treinamento/verificar_treinamentos.html` | Mudar herança para `base_dashboard.html` |
| `treinamento/templates/treinamento/treinar_ia.html` | Mudar herança para `base_dashboard.html` |
| `treinamento/templates/treinamento/pre_processamento.html` | Mudar herança para `base_dashboard.html` |
| `treinamento/templates/treinamento/cadastrar_query_compose.html` | Mudar herança para `base_dashboard.html` |
| `treinamento/templates/treinamento/verificar_query_compose.html` | Mudar herança para `base_dashboard.html` |
| `core/views.py` | Redirecionar `/dashboard/` para tenant dashboard |
| `usuarios/views.py` | Lógica de redirecionamento por tipo de usuário |
| `core/templates/base_dashboard.html` | Adicionar controles de permissão |
| `tenants/templatetags/permission_tags.py` | Nova tag `can_view_module` |
| `tenants/templates/tenants/dashboard.html` | Padronizar altura dos cards |
