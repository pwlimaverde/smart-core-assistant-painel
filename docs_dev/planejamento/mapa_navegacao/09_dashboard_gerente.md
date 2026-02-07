# Módulo 9 - Dashboard Gerente

> 📋 **Status**: ⏳ Pendente Implementação
> 📅 **Data**: 2026-01-15
> 🔗 **Índice**: [00_indice.md](./00_indice.md)

---

## Resumo do Módulo

| Métrica              | Valor                              |
| -------------------- | ---------------------------------- |
| **Total de Páginas** | 2                                  |
| **Template Base**    | ⚠️ A verificar                     |
| **Autenticação**     | ✅ Requerida                       |
| **Permissão**        | `MANAGER` + permissão `treinar_ia` |
| **App**              | `ui.usuarios`                      |

---

## Página 1: Dashboard Gerente

### Informações Básicas

| Campo             | Valor                                |
| ----------------- | ------------------------------------ |
| **Nome**          | Dashboard Gerente                    |
| **URL**           | `/usuarios/dashboard-gerente/`       |
| **URL Name**      | `dashboard_gerente`                  |
| **View**          | `dashboard_gerente` (Function-Based) |
| **Template**      | `dashboard_gerente.html`             |
| **Template Base** | ⚠️ A verificar                       |
| **App**           | `ui.usuarios`                        |
| **Arquivo View**  | `app/usuarios/views.py:168-224`   |

### Permissões

| Tipo                 | Valor                                              |
| -------------------- | -------------------------------------------------- |
| **Autenticação**     | ✅ Requerida                                       |
| **Roles Permitidos** | Usuários com permissão `treinar_ia`                |
| **Módulo**           | N/A                                                |
| **Decorator/Mixin**  | `@login_required` + `has_permission('treinar_ia')` |

### Métricas Exibidas

| Métrica                    | Descrição                |
| -------------------------- | ------------------------ |
| Total de Atendimentos      | Contagem geral           |
| Atendimentos Abertos       | Status aberto            |
| Atendimentos Fechados      | Status fechado           |
| Atendimentos por Atendente | Breakdown por pessoa     |
| Tempo Médio                | Tempo médio de resolução |

### Links da Página

| #   | Nome do Link     | URL de Destino             | URL Name                 | Resumo              |
| --- | ---------------- | -------------------------- | ------------------------ | ------------------- |
| 1   | Treinamento IA   | `/treinamento/treinar-ia/` | `treinamento:treinar_ia` | Treinar IA          |
| 2   | Dashboard Tenant | `/tenants/dashboard/`      | `tenants:dashboard`      | Dashboard principal |

### Auditoria Design System

| Item                  | Status       | Observação        |
| --------------------- | ------------ | ----------------- |
| Template base correto | ⏳ Verificar | A verificar       |
| Sidebar visível       | ⏳ Verificar | Navegação         |
| Navegação funcional   | ⏳ Verificar | Links             |
| Responsividade        | ⏳ Verificar | Cards de métricas |
| Padrões visuais       | ⏳ Verificar | Gráficos, tabelas |

---

## Página 2: Permissões (Superuser)

### Informações Básicas

| Campo             | Valor                              |
| ----------------- | ---------------------------------- |
| **Nome**          | Gerenciamento de Permissões        |
| **URL**           | `/usuarios/permissoes/`            |
| **URL Name**      | `permissoes`                       |
| **View**          | `permissoes` (Function-Based)      |
| **Template**      | `permissoes.html`                  |
| **Template Base** | ⚠️ A verificar                     |
| **App**           | `ui.usuarios`                      |
| **Arquivo View**  | `app/usuarios/views.py:143-150` |

### Permissões

| Tipo                 | Valor                                          |
| -------------------- | ---------------------------------------------- |
| **Autenticação**     | ✅ Requerida                                   |
| **Roles Permitidos** | 🔴 **Apenas `is_superuser`**                   |
| **Módulo**           | N/A                                            |
| **Decorator/Mixin**  | `@login_required` + verificação `is_superuser` |

### Dados Exibidos

- Lista de usuários do sistema
- Status de cada usuário
- Ação de tornar gerente

### Links da Página

| #   | Nome do Link   | URL de Destino                  | URL Name         | Resumo             |
| --- | -------------- | ------------------------------- | ---------------- | ------------------ |
| 1   | Tornar Gerente | `/usuarios/tornar_gerente/<id>` | `tornar_gerente` | Conceder permissão |
| 2   | Admin          | `/admin/`                       | N/A              | Django Admin       |

### Auditoria Design System

| Item                  | Status       | Observação        |
| --------------------- | ------------ | ----------------- |
| Template base correto | ⏳ Verificar | A verificar       |
| Sidebar visível       | ⏳ Verificar | Navegação         |
| Navegação funcional   | ⏳ Verificar | Ações por usuário |
| Responsividade        | ⏳ Verificar | Tabela            |
| Padrões visuais       | ⏳ Verificar | Botões            |

---

## API: Tornar Gerente

### Informações Básicas

| Campo            | Valor                              |
| ---------------- | ---------------------------------- |
| **URL**          | `/usuarios/tornar_gerente/<id>`    |
| **URL Name**     | `tornar_gerente`                   |
| **View**         | `tornar_gerente` (Function-Based)  |
| **Método**       | GET (redireciona após ação)        |
| **Arquivo View** | `app/usuarios/views.py:153-165` |

### Parâmetros

| Parâmetro | Tipo | Descrição     |
| --------- | ---- | ------------- |
| `id`      | int  | ID do usuário |

### Permissões

| Tipo                 | Valor                        |
| -------------------- | ---------------------------- |
| **Autenticação**     | ✅ Requerida                 |
| **Roles Permitidos** | 🔴 **Apenas `is_superuser`** |

### Comportamento

| Ação      | Resultado                                |
| --------- | ---------------------------------------- |
| Executado | Adiciona role `gerente` ao usuário       |
| Sucesso   | Redireciona para `/usuarios/permissoes/` |

---

## Controle de Acesso

### Matriz de Permissões

| Role             | Dashboard Gerente | Permissões | Tornar Gerente |
| ---------------- | ----------------- | ---------- | -------------- |
| Superuser        | ✅                | ✅         | ✅             |
| Com `treinar_ia` | ✅                | ❌         | ❌             |
| Admin            | ❌\*              | ❌         | ❌             |
| Manager          | ❌\*              | ❌         | ❌             |
| Staff            | ❌                | ❌         | ❌             |
| Viewer           | ❌                | ❌         | ❌             |

> \*A menos que tenha permissão `treinar_ia` explícita

---

## Pontos de Atenção Identificados

### 🟡 Observações

1. **Permissão `treinar_ia`** - Dashboard Gerente usa `rolepermissions` com permissão específica
2. **Página de Permissões** - Funcionalidade legada, apenas para superuser

---

## Checklist de Validação do Módulo

- [ ] Todas as páginas documentadas
- [ ] Todos os links mapeados
- [ ] Permissões verificadas
- [ ] Template base auditado
- [ ] **APROVADO PELO USUÁRIO**
