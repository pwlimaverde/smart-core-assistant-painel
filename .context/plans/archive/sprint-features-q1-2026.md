# Plano: Sprint Features Q1/2026 - Teste de Treinamento, Refatoração Apps e Whitelist UI

**Status**: Concluído (Feature 1 e 3 implementadas; Feature 2 adiada)
**Criado**: 2026-02-07
**Atualizado**: 2026-02-07
**Concluído**: 2026-02-07
**Responsável**: Claude Code
**Tipo**: Feature Development + Refactoring
**Prioridade**: Alta
**Branch**: `feature/teste-reposta-query`

---

## Resumo Executivo

Este plano abrange 3 iniciativas:
1. **Feature de Teste de Treinamento** - Chat interativo na página "Verificar Query" para testar respostas do bot
2. **Refatoração de Apps Django** - Reorganizar estrutura de diretórios do projeto
3. **Whitelist no Painel de Configurações** - Interface UI para gerenciar números ignorados

---

## Feature 1: Teste de Treinamento na Página Verificar Query

### Objetivo
Adicionar uma seção de chat interativo na página `verificar_query_compose` (ou nova página dedicada) onde o usuário pode:
- Enviar uma mensagem simulada e ver a resposta do bot
- Visualizar entidades extraídas da mensagem
- Avaliar se a resposta foi boa ou ruim
- Corrigir a resposta e reenviar caso necessária

### Análise do Estado Atual

**Arquivos Envolvidos:**
- `app/treinamento/views.py` - Views do treinamento (verificar_query_compose na linha 390)
- `app/treinamento/urls.py` - URLs do treinamento
- `app/treinamento/templates/treinamento/verificar_query_compose.html` - Template atual (somente lista intents)
- `modules/ai_engine/features/features_compose.py` - Facade `FeaturesCompose` com `analise_mensage()`
- `modules/ai_engine/features/analise_previa_mensagem/` - Feature de análise prévia (extrai entidades/intents)
- `app/treinamento/models.py` - Models `Treinamento`, `Documento`, `QueryCompose`

**API de IA Disponível:**
- `FeaturesCompose.analise_mensage()` - Retorna `AMTuple(resposta_bot, confiabilidade, transferir_atendimento, fluxo_transferencia)`
- `FeaturesCompose.analise_previa_mensagem()` - Retorna `APMTuple(entidades_extraidas, intents_detectados)`
- `FeaturesCompose.generate_embeddings()` - Gera vetor de embedding
- `Documento.buscar_documentos_similares()` - Busca RAG por similaridade
- `QueryCompose.buscar_comportamento_similar()` - Busca intent mais similar

### Etapas de Implementação

#### Etapa 1.1: Criar View de Teste de Resposta (Backend)
**Arquivo:** `app/treinamento/views.py`

Criar nova view `testar_resposta_query` que:
1. Recebe mensagem via POST (AJAX/JSON)
2. Gera embedding da mensagem com `FeaturesCompose.generate_embeddings()`
3. Busca documentos similares com `Documento.buscar_documentos_similares()`
4. Busca comportamento similar com `QueryCompose.buscar_comportamento_similar()`
5. Executa `FeaturesCompose.analise_previa_mensagem()` para extrair entidades
6. Executa `FeaturesCompose.analise_mensage()` com os dados de contexto
7. Retorna JSON com:
   - `resposta_bot`: texto da resposta
   - `confiabilidade`: score de confiança (0.0 a 1.0)
   - `transferir_atendimento`: bool
   - `fluxo_transferencia`: string
   - `entidades_extraidas`: lista de entidades detectadas
   - `intents_detectados`: lista de intents detectados
   - `documentos_utilizados`: IDs dos documentos RAG usados
   - `query_compose_match`: tag do QueryCompose mais similar (se houver)

```python
# Assinatura proposta
def testar_resposta_query(request: HttpRequest) -> HttpResponse:
    """[TRN-TEST-001] Endpoint AJAX para testar resposta do bot.

    Recebe mensagem simulada e retorna análise completa.
    """
```

#### Etapa 1.2: Criar View de Feedback da Resposta (Backend)
**Arquivo:** `app/treinamento/views.py`

Criar view `feedback_resposta_query` que:
1. Recebe avaliação (bom/ruim) via POST
2. Se ruim, recebe a resposta corrigida do usuário
3. Armazena o feedback para análise futura (novo model ou log estruturado)
4. Opcionalmente, permite gerar novo treinamento a partir da correção

```python
# Assinatura proposta
def feedback_resposta_query(request: HttpRequest) -> HttpResponse:
    """[TRN-TEST-002] Registra feedback sobre a resposta do bot."""
```

#### Etapa 1.3: Criar Model de Feedback (Opcional)
**Arquivo:** `app/treinamento/models.py`

Novo model `QueryTestFeedback`:
```python
class QueryTestFeedback(models.Model):
    """Registra feedback de testes de query para melhoria contínua."""

    mensagem_original = models.TextField()
    resposta_bot = models.TextField()
    resposta_corrigida = models.TextField(blank=True, null=True)
    avaliacao = models.CharField(max_length=10)  # 'bom' ou 'ruim'
    confiabilidade = models.FloatField()
    entidades_json = models.JSONField(default=dict)
    intents_json = models.JSONField(default=dict)
    documentos_ids = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
```

#### Etapa 1.4: Registrar URLs
**Arquivo:** `app/treinamento/urls.py`

Adicionar:
```python
path("testar-resposta/", views.testar_resposta_query, name="testar_resposta_query"),
path("feedback-resposta/", views.feedback_resposta_query, name="feedback_resposta_query"),
```

#### Etapa 1.5: Criar Template de Teste
**Arquivo:** `app/treinamento/templates/treinamento/testar_query.html`

Nova página dedicada com:
1. **Área de Chat** - Input de mensagem + histórico de conversa
2. **Painel de Detalhes** - Exibe para cada resposta:
   - Score de confiabilidade (barra visual + número)
   - Entidades extraídas (cards/badges)
   - Intents detectados (cards/badges)
   - Documentos RAG utilizados (lista colapsável)
   - QueryCompose match (se houver)
   - Flag de transferência (se aplicável)
3. **Área de Avaliação** - Botões "Boa Resposta" / "Resposta Ruim"
4. **Área de Correção** (visível apenas se "Ruim") - Textarea para resposta corrigida + botão "Enviar Correção"

**Design System:** Extender `base_dashboard.html`, usar Tailwind CSS conforme padrão do projeto (stone colors, rounded-xl, shadow-sm)

#### Etapa 1.6: JavaScript para Interatividade
**Arquivo:** `app/core/static/js/testar_query.js` (ou inline no template)

- Fetch API para chamadas AJAX
- Loading state durante processamento (spinner)
- Atualização dinâmica do painel de detalhes
- Histórico de mensagens no chat
- Toggle da área de correção

#### Etapa 1.7: Adicionar Link de Navegação
**Arquivo:** `app/treinamento/templates/treinamento/verificar_query_compose.html`

Adicionar botão "Testar Respostas" ao lado de "Nova Intent" no header.

### Dependências
- `FeaturesCompose` precisa estar funcional (LLM + Embeddings configurados)
- Dados de treinamento vetorizados no banco
- QueryCompose com embeddings gerados

### Riscos
- Tempo de resposta da LLM pode ser lento (considerar loading/streaming)
- Custo de API por teste (cada teste consome tokens LLM)
- Ausência de dados de treinamento pode gerar respostas vazias

---

## Feature 2: Refatoração de Apps Django

### Objetivo
Reorganizar a estrutura de diretórios dos apps Django para maior clareza e consistência.

### Análise do Estado Atual

```
src/smart_core_assistant_painel/
├── app/
│   ├── __init__.py
│   ├── evolution_sync/          # App Django (fora de ui/)
│   │   ├── domain/schemas.py
│   │   ├── services/webhook.py
│   │   ├── models.py
│   │   ├── views.py
│   │   └── ...
│   ├── settings_manager/        # App Django (fora de ui/)
│   │   ├── management/commands/
│   │   ├── models.py
│   │   └── ...
│   ├── tenants/                 # App Django (fora de ui/)
│   │   ├── services/
│   │   ├── models.py
│   │   └── ...
│   ├── trello_sync/             # App Django (fora de ui/)
│   │   ├── models.py
│   │   └── ...
│   └── ui/                      # Subdiretório com mais apps
│       ├── core/                # Config Django (settings, urls, middleware)
│       ├── atendimentos/        # App Django
│       ├── clientes/            # App Django
│       ├── operacional/         # App Django
│       ├── treinamento/         # App Django
│       └── usuarios/            # App Django
└── modules/                     # Lógica de negócio (não-Django)
    ├── ai_engine/
    ├── services/
    └── initial_loading/
```

### Problemas Identificados

1. **Apps misturados em dois níveis**: Alguns apps estão em `app/` (evolution_sync, settings_manager, tenants, trello_sync) e outros em `app/` (atendimentos, clientes, operacional, treinamento, usuarios)
2. **`core` não é um app Django real**: É onde settings, urls e middleware ficam, mas é registrado como app
3. **Ausência de `oraculo` como app**: Referenciado na documentação mas não existe como app separado
4. **clickup_sync e notion_sync**: Comentados em `INSTALLED_APPS` mas pastas podem ainda existir
5. **Inconsistência**: Alguns apps têm `tenant_admin.py`, outros não; alguns têm `services/`, outros não

### Proposta de Nova Estrutura

```
src/smart_core_assistant_painel/
├── app/
│   ├── config/                  # Renomear core → config (settings, urls, middleware, wsgi, asgi)
│   │   ├── settings.py
│   │   ├── settings_test.py
│   │   ├── urls.py
│   │   ├── middleware.py
│   │   ├── celery.py
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   ├── context_processors.py
│   │   ├── views.py             # Views base (dashboard, home, landing)
│   │   ├── static/
│   │   └── templates/           # Templates base (base.html, 403, 404, 500)
│   │
│   ├── tenants/                 # Infraestrutura multi-tenant
│   │   └── ... (sem mudanças)
│   │
│   ├── usuarios/                # Mover de ui/ para app/
│   │   └── ...
│   │
│   ├── clientes/                # Mover de ui/ para app/
│   │   └── ...
│   │
│   ├── operacional/             # Mover de ui/ para app/
│   │   └── ...
│   │
│   ├── atendimentos/            # Mover de ui/ para app/
│   │   └── ...
│   │
│   ├── treinamento/             # Mover de ui/ para app/
│   │   └── ...
│   │
│   ├── settings_manager/        # Sem mudanças
│   │   └── ...
│   │
│   └── integrations/            # Agrupar integrações externas
│       ├── evolution_sync/      # Mover de app/ para integrations/
│       ├── trello_sync/         # Mover de app/ para integrations/
│       ├── clickup_sync/        # (se existir)
│       └── notion_sync/         # (se existir)
│
└── modules/                     # Sem mudanças
    └── ...
```

### Etapas de Implementação

> **NOTA IMPORTANTE:** Esta refatoração é de alto risco e deve ser feita com muito cuidado. Cada etapa deve ser um commit separado e testada antes de avançar.

#### Etapa 2.1: Análise de Impacto
- Mapear TODOS os imports que referenciam os caminhos atuais
- Mapear TODAS as referências em `INSTALLED_APPS`, `ROOT_URLCONF`, `MIDDLEWARE`
- Mapear referências em migrations, fixtures, scripts
- Mapear referências em templates (`{% url %}`, `{% load %}`)
- Documentar decisão final de estrutura

#### Etapa 2.2: Mover Apps de `ui/` para `app/` (um por vez)
Para cada app (`usuarios`, `clientes`, `operacional`, `atendimentos`, `treinamento`):

1. Mover diretório de `app/<nome>/` para `app/<nome>/`
2. Atualizar `apps.py` → `name = "smart_core_assistant_painel.app.<nome>"`
3. Atualizar `INSTALLED_APPS` em `settings.py`
4. Atualizar todos os imports no codebase (grep + replace)
5. Atualizar referências em migrations
6. Atualizar referências em urls.py
7. Rodar `uv run task lint` e `uv run task type-check`
8. Rodar `uv run task test-docker` para verificar se tudo funciona
9. Commit individual

#### Etapa 2.3: Renomear `core` para `config`
1. Mover `app/core/` para `app/config/`
2. Atualizar `ROOT_URLCONF`, `WSGI_APPLICATION`, `ASGI_APPLICATION` em settings
3. Atualizar todos os imports de middleware, context_processors
4. Atualizar `MIDDLEWARE` em settings
5. Atualizar referências em templates
6. Rodar testes

#### Etapa 2.4: Agrupar Integrações (Opcional)
1. Criar `app/integrations/`
2. Mover `evolution_sync`, `trello_sync` para `app/integrations/`
3. Atualizar imports e INSTALLED_APPS
4. Rodar testes

#### Etapa 2.5: Limpeza Final
1. Remover diretório `app/` (agora vazio)
2. Remover `app/manage.py` (se não for usado)
3. Limpar `__pycache__` residuais
4. Atualizar documentação (CLAUDE.md, .context/docs/)

### Riscos e Mitigações
| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Migrations com paths hardcoded | Migrations quebram | Atualizar dependencies em migrations |
| Imports circulares | App não inicia | Testar cada move individualmente |
| Templates com paths relativos | Templates não renderizam | Verificar APP_DIRS e DIRS |
| Docker/CI com paths antigos | Deploy quebra | Atualizar Dockerfile e CI |
| Celery tasks com imports antigos | Tasks falham | Verificar task registry |

### Alternativa Conservadora
Se a refatoração completa for muito arriscada, uma alternativa é:
- **Manter a estrutura atual** mas padronizar internamente (todos os apps com services/, templatetags/, etc.)
- **Criar apenas aliases/re-exports** para compatibilidade
- **Documentar a convenção** em CLAUDE.md

---

## Feature 3: Whitelist no Painel de Configurações

### Objetivo
Incluir no painel de configurações (UI do dashboard, não admin Django) a opção de cadastrar e gerenciar a whitelist de números que serão ignorados na resposta automática.

### Análise do Estado Atual

**O que já existe:**
- **Model `WhiteList`** em `app/evolution_sync/models.py` (campos: name, phone_number, active)
- **Tenant Admin** em `app/evolution_sync/tenant_admin.py` (TenantWhiteListAdmin com CRUD completo)
- **Filtro no webhook** em `app/evolution_sync/services/webhook.py` (`_is_whitelist_contact()`)
- **Testes** em `app/evolution_sync/tests/test_communication_rules.py`

**O que NÃO existe:**
- View no dashboard (fora do admin Django) para gerenciar whitelist
- Template dedicado no painel de configurações
- API REST para CRUD da whitelist

### Onde ficam as Configurações no Dashboard

As configurações do tenant são acessíveis via:
- **Admin Django Jazzmin** - Gerenciamento técnico (tenant_admin)
- **Dashboard UI** - Não existe painel de configurações com views próprias ainda

O `settings_manager/views.py` está **vazio** - não há views de configuração no dashboard.

### Proposta: Criar Painel de Configurações no Dashboard

#### Etapa 3.1: Criar Views de Configurações Base
**Arquivo:** `app/settings_manager/views.py` (atualmente vazio)

Criar views para o painel de configurações:
```python
def configuracoes_index(request: HttpRequest) -> HttpResponse:
    """Página principal de configurações do tenant."""
    # Lista cards para cada seção de configuração

def configuracoes_whitelist(request: HttpRequest) -> HttpResponse:
    """Gestão de whitelist de números."""
    # Lista, adiciona, edita, remove números da whitelist
```

#### Etapa 3.2: Criar URLs de Configurações
**Arquivo:** `app/settings_manager/urls.py` (criar novo)

```python
app_name = "configuracoes"

urlpatterns = [
    path("", views.configuracoes_index, name="index"),
    path("whitelist/", views.configuracoes_whitelist, name="whitelist"),
    path("whitelist/adicionar/", views.whitelist_adicionar, name="whitelist_adicionar"),
    path("whitelist/<int:id>/editar/", views.whitelist_editar, name="whitelist_editar"),
    path("whitelist/<int:id>/excluir/", views.whitelist_excluir, name="whitelist_excluir"),
    path("whitelist/<int:id>/toggle/", views.whitelist_toggle, name="whitelist_toggle"),
]
```

#### Etapa 3.3: Registrar URLs no Core
**Arquivo:** `app/core/urls.py`

Adicionar:
```python
path("configuracoes/", include("smart_core_assistant_painel.app.settings_manager.urls")),
```

#### Etapa 3.4: Criar Template Index de Configurações
**Arquivo:** `app/settings_manager/templates/configuracoes/index.html`

Grid de cards com seções:
- **WhatsApp** - Whitelist de números
- **IA** - Parâmetros do LLM (futuro)
- **Integrações** - Trello, Evolution (futuro)
- **Banco de Dados** - Informações (futuro)

#### Etapa 3.5: Criar Template de Whitelist
**Arquivo:** `app/settings_manager/templates/configuracoes/whitelist.html`

Funcionalidades:
1. **Tabela de números** - Colunas: Nome, Telefone, Status (Ativo/Inativo), Data Criação, Ações
2. **Botão "Adicionar Número"** - Abre modal ou redireciona para form
3. **Toggle Ativo/Inativo** - Switch inline para cada número
4. **Editar** - Modal ou página de edição (nome + telefone)
5. **Excluir** - Com confirmação
6. **Busca** - Filtro por nome ou telefone

**Design System:** Seguir padrão do `verificar_query_compose.html` (Tailwind, stone colors, rounded-xl)

#### Etapa 3.6: Criar Forms
**Arquivo:** `app/settings_manager/forms.py` (criar novo)

```python
class WhiteListForm(forms.ModelForm):
    class Meta:
        model = WhiteList
        fields = ['name', 'phone_number', 'active']

    def clean_phone_number(self):
        """Normaliza e valida o número de telefone."""
        # Remover caracteres não-numéricos
        # Validar formato brasileiro (55DDXXXXXXXXX)
```

#### Etapa 3.7: Implementar Views Completas
**Arquivo:** `app/settings_manager/views.py`

Views necessárias:
1. `configuracoes_whitelist` - GET: lista whitelist; POST: processar ações
2. `whitelist_adicionar` - GET: form; POST: criar
3. `whitelist_editar` - GET: form preenchido; POST: atualizar
4. `whitelist_excluir` - POST: deletar com confirmação
5. `whitelist_toggle` - POST: alternar ativo/inativo

**Permissões:** Verificar se usuário é ADMIN do tenant ou owner

#### Etapa 3.8: Adicionar Link na Sidebar/Navegação
**Arquivo:** `app/core/templates/base_dashboard.html`

Adicionar link "Configurações" na sidebar do dashboard, com ícone de engrenagem.

### Considerações Técnicas

**Cross-Database:** O model `WhiteList` está no banco do tenant (via `evolution_sync`). As views precisam usar o database router correto (já tratado pelo `TenantMiddleware`).

**Normalização de Telefone:** Reutilizar `_get_phone_variations()` do `WebhookProcessor` para validar e normalizar números no formulário.

**Permissões:** Criar helper ou decorator para verificar acesso ao módulo CONFIGURACOES:
```python
def _can_manage_settings(user) -> bool:
    """Verifica se o usuário pode gerenciar configurações."""
```

---

## Ordem de Execução Recomendada

| Prioridade | Feature | Esforço | Risco |
|------------|---------|---------|-------|
| 1 | Feature 3: Whitelist UI | Médio (3-5 dias) | Baixo |
| 2 | Feature 1: Teste de Treinamento | Alto (5-8 dias) | Médio |
| 3 | Feature 2: Refatoração Apps | Muito Alto (8-15 dias) | Alto |

**Justificativa:**
- **Whitelist UI** é a feature mais isolada, não quebra nada existente, e entrega valor imediato
- **Teste de Treinamento** depende da infraestrutura de IA já existente, médio risco
- **Refatoração** é alto risco e não entrega feature nova; pode ser feita incrementalmente

---

## Critérios de Sucesso

### Feature 1 - Teste de Treinamento
- [ ] Usuário consegue enviar mensagem e ver resposta do bot
- [ ] Entidades extraídas são exibidas corretamente
- [ ] Score de confiabilidade é exibido visualmente
- [ ] Avaliação bom/ruim funciona
- [ ] Correção de resposta é armazenada
- [ ] UI responsiva e alinhada com Design System

### Feature 2 - Refatoração
- [ ] Todos os apps em `app/` (sem subdiretório `ui/`)
- [ ] Todos os imports atualizados
- [ ] Migrations funcionando
- [ ] Testes passando (test-docker)
- [ ] Lint e type-check passando
- [ ] Documentação atualizada

### Feature 3 - Whitelist UI
- [ ] Painel de configurações acessível no dashboard
- [ ] CRUD completo de whitelist (listar, adicionar, editar, excluir)
- [ ] Toggle ativo/inativo funcionando
- [ ] Validação e normalização de telefone
- [ ] Permissões corretas aplicadas
- [ ] Integração com filtro existente do webhook

---

## Arquivos Relacionados

### Feature 1
- [views.py](../../src/smart_core_assistant_painel/app/treinamento/views.py)
- [urls.py](../../src/smart_core_assistant_painel/app/treinamento/urls.py)
- [models.py](../../src/smart_core_assistant_painel/app/treinamento/models.py)
- [features_compose.py](../../src/smart_core_assistant_painel/modules/ai_engine/features/features_compose.py)
- [verificar_query_compose.html](../../src/smart_core_assistant_painel/app/treinamento/templates/treinamento/verificar_query_compose.html)

### Feature 2
- [settings.py](../../src/smart_core_assistant_painel/app/core/settings.py)
- [urls.py (core)](../../src/smart_core_assistant_painel/app/core/urls.py)

### Feature 3
- [models.py (evolution)](../../src/smart_core_assistant_painel/app/evolution_sync/models.py)
- [views.py (settings_manager)](../../src/smart_core_assistant_painel/app/settings_manager/views.py)
- [webhook.py](../../src/smart_core_assistant_painel/app/evolution_sync/services/webhook.py)
- [tenant_admin.py](../../src/smart_core_assistant_painel/app/evolution_sync/tenant_admin.py)

---

**Última Atualização**: 2026-02-07
**Responsável**: Claude Code
