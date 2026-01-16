# Refatoração UI Design System v2

> 📋 **Plano AI-Context**: [refactor-ui-design-system-v2.md](../../../.context/plans/refactor-ui-design-system-v2.md)
> 📁 **Mapa de Navegação**: [docs_dev/planejamento/mapa_navegacao](../../../docs_dev/planejamento/mapa_navegacao/00_indice.md)
> 📅 **Data**: 2026-01-15
> 🏷️ **Status**: Em Revisão

---

## Objetivo

Refatorar **100% das telas navegáveis** (31 páginas) do Smart Core Assistant Painel, garantindo:

1. **Conformidade com Design System** - Uso correto de `base_dashboard.html` ou `base_public.html`
2. **Mapeamento de Navegação** - Documentação de todos os links com nome, destino e resumo
3. **Auditoria de Permissões** - Verificação de roles autorizados por página
4. **Validação Sequencial** - Cada módulo aprovado antes de avançar para o próximo

---

## Contexto

### Arquitetura de Templates

O sistema possui uma hierarquia de templates Django:

```
base.html
├── base_public.html (páginas públicas)
│   ├── landing_page.html
│   ├── 403.html, 404.html, 500.html
│   ├── login.html, cadastro.html
│   └── tenants/onboarding/*.html (standalone)
│
└── base_dashboard.html (área autenticada)
    ├── base_tenants.html
    │   ├── tenants/dashboard.html
    │   ├── tenants/config_*.html
    │   └── tenants/users/*.html
    └── Tenant Admin (Jazzmin)
```

### Sistema de Permissões

| Componente       | Descrição                                                                       |
| ---------------- | ------------------------------------------------------------------------------- |
| `TenantRoleType` | Enum: `ADMIN`, `MANAGER`, `STAFF`, `VIEWER`                                     |
| `TenantModule`   | Enum: `CLIENTES`, `OPERACIONAL`, `TREINAMENTO`, `ATENDIMENTOS`, `CONFIGURACOES` |
| Mixins Django    | `LoginRequiredMixin`, `UserPassesTestMixin`                                     |
| RolePermissions  | Biblioteca para permissões granulares                                           |

---

## Escopo

### Incluído (31 Páginas em 9 Módulos)

| #         | Módulo                   | Páginas | Documento                                                                                        |
| --------- | ------------------------ | ------- | ------------------------------------------------------------------------------------------------ |
| 1         | Páginas Públicas e Erros | 4       | [01_paginas_publicas.md](../../../docs_dev/planejamento/mapa_navegacao/01_paginas_publicas.md)   |
| 2         | Autenticação             | 3       | [02_autenticacao.md](../../../docs_dev/planejamento/mapa_navegacao/02_autenticacao.md)           |
| 3         | Onboarding Wizard        | 4       | [03_onboarding.md](../../../docs_dev/planejamento/mapa_navegacao/03_onboarding.md)               |
| 4         | Backoffice (Super Admin) | 2       | [04_backoffice.md](../../../docs_dev/planejamento/mapa_navegacao/04_backoffice.md)               |
| 5         | Dashboard Tenant         | 1       | [05_dashboard_tenant.md](../../../docs_dev/planejamento/mapa_navegacao/05_dashboard_tenant.md)   |
| 6         | Configurações            | 5       | [06_configuracoes.md](../../../docs_dev/planejamento/mapa_navegacao/06_configuracoes.md)         |
| 7         | Gestão de Usuários       | 5       | [07_gestao_usuarios.md](../../../docs_dev/planejamento/mapa_navegacao/07_gestao_usuarios.md)     |
| 8         | Treinamento IA           | 5       | [08_treinamento_ia.md](../../../docs_dev/planejamento/mapa_navegacao/08_treinamento_ia.md)       |
| 9         | Dashboard Gerente        | 2       | [09_dashboard_gerente.md](../../../docs_dev/planejamento/mapa_navegacao/09_dashboard_gerente.md) |
| **TOTAL** |                          | **31**  |                                                                                                  |

### Não Incluído

- Django Admin padrão (`/admin/`)
- Tenant Admin Jazzmin (gerenciado separadamente)
- APIs sem interface visual
- Webhooks e callbacks

---

## Decisões de Design

### 1. Estrutura de Templates

| Tipo de Página       | Template Base                               | Decisão                                                 |
| -------------------- | ------------------------------------------- | ------------------------------------------------------- |
| Públicas             | `base_public.html`                          | Manter                                                  |
| Erro (403, 404, 500) | `base.html`                                 | **Avaliar migração** para `base_public.html`            |
| Onboarding           | `onboarding/base.html` (standalone)         | Manter (wizard isolado)                                 |
| Dashboard/Config     | `base_tenants.html` → `base_dashboard.html` | Padronizar                                              |
| Backoffice           | A definir                                   | Criar template específico ou usar `base_dashboard.html` |

### 2. Validação Sequencial

```
┌─────────────────────────────────────────────────────────────────┐
│  PROCESSO DE VALIDAÇÃO POR MÓDULO                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Para cada Módulo (1-9):                                        │
│    1. Implementar correções de Design System                    │
│    2. Verificar links funcionais                                │
│    3. Testar permissões por role                                │
│    4. Solicitar aprovação do usuário                            │
│    5. Só avançar após aprovação ✓                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Checklist por Página

Cada página será auditada em:

- [ ] Template base correto (herança)
- [ ] Sidebar visível (se aplicável)
- [ ] Links funcionais e mapeados
- [ ] Permissões documentadas e testadas
- [ ] Responsividade verificada
- [ ] Padrões visuais consistentes

---

## Dependências

| Dependência                 | Tipo         | Status          |
| --------------------------- | ------------ | --------------- |
| Jazzmin Theme               | Técnica      | ✅ Instalado    |
| RolePermissions             | Técnica      | ✅ Instalado    |
| TenantModule/TenantRoleType | Interna      | ✅ Implementado |
| Mapa de Navegação           | Documentação | ✅ Criado       |

---

## Critérios de Aceite

1. ✅ **Documentação Completa** - Todos os 9 módulos documentados no mapa de navegação
2. ⏳ **Templates Padronizados** - Todas as páginas usando template base correto
3. ⏳ **Links Funcionais** - Nenhum link quebrado
4. ⏳ **Permissões Testadas** - Cada role testado em cada página
5. ⏳ **Validação Sequencial** - Cada módulo aprovado individualmente
6. ⏳ **UI_MAP.md Final** - Documento consolidado ao final

---

## Riscos e Mitigações

| Risco                           | Probabilidade | Impacto | Mitigação                                  |
| ------------------------------- | ------------- | ------- | ------------------------------------------ |
| Templates com herança incorreta | Alta          | Alta    | Verificar `{% extends %}` em cada template |
| Permissões inconsistentes       | Média         | Alta    | Testar cada role manualmente               |
| Links quebrados                 | Média         | Média   | Validar todos os `{% url %}`               |
| Sidebar não aparece             | Alta          | Alta    | Verificar contexto e herança               |
