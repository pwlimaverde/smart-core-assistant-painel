## MODIFIED Requirements

### Requirement: Templates de Páginas Internas Devem Estender base_dashboard.html
Todas as páginas que requerem autenticação e fazem parte do painel administrativo interno SHALL estender `base_dashboard.html`, garantindo consistência visual com sidebar e topbar.

#### Scenario: Template de treinamento exibe sidebar
- **WHEN** usuário autenticado com acesso ao tenant acessa "/treinamento/verificar-treinamentos/"
- **THEN** página exibe sidebar esquerda com navegação e topbar branca com email do usuário

#### Scenario: Template de query compose exibe sidebar
- **WHEN** usuário autenticado com acesso ao tenant acessa "/treinamento/cadastrar-query-compose/"
- **THEN** página exibe sidebar esquerda com navegação e conteúdo dentro da área principal

#### Scenario: Template de treinar IA exibe sidebar
- **WHEN** usuário autenticado com acesso ao tenant acessa "/treinamento/treinar-ia/"
- **THEN** página exibe sidebar esquerda com navegação

---

### Requirement: Estrutura de Blocos em Templates Filhos
Templates que estendem `base_dashboard.html` SHALL usar o bloco `{% block content %}` para seu conteúdo, sem definir estruturas HTML de layout próprias.

#### Scenario: Template filho não duplica estrutura de layout
- **WHEN** template de treinamento é renderizado estendendo base_dashboard.html
- **THEN** template NÃO contém tags `<header>`, `<main>`, `<aside>` próprias que dupliquem o layout base

---

## Arquivos Afetados

| Template | Estado Atual | Estado Proposto |
|----------|--------------|-----------------|
| `treinamento/verificar_treinamentos.html` | `{% extends "base.html" %}` | `{% extends "base_dashboard.html" %}` |
| `treinamento/treinar_ia.html` | `{% extends "base.html" %}` | `{% extends "base_dashboard.html" %}` |
| `treinamento/pre_processamento.html` | `{% extends "base.html" %}` | `{% extends "base_dashboard.html" %}` |
| `treinamento/cadastrar_query_compose.html` | `{% extends 'base.html' %}` | `{% extends "base_dashboard.html" %}` |
| `treinamento/verificar_query_compose.html` | `{% extends 'base.html' %}` | `{% extends "base_dashboard.html" %}` |
