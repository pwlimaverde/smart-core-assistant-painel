# Mapeamento de Campos do Atendimento para Custom Fields no ClickUp

## Visão Geral

Este documento define o mapeamento dos campos do model `Atendimento` (app `atendimentos`) para campos personalizados (Custom Fields) em cards do ClickUp, com foco em enriquecer o contexto para os atendentes na Central de Atendimento.

A proposta considera a arquitetura por Departamentos (Folder), Fluxos por departamento (List) e Etapas (`EtapaFluxo`) mapeadas para Status da List.

- **Base técnica**: Django + PostgreSQL, UI Kanban por departamento
- **Integração**: ClickUp API v2 (`Authorization: Bearer <token>`)
- **Referências**: `CENTRAL_DE_ATENDIMENTO.md` e `02_plano_de_integracao.md`

## Princípios de Mapeamento

- Campos que melhoram a leitura rápida do card, contexto do cliente, SLAs e próximos passos
- Reuso preferencial em **Workspace** para padrões (Canal, datas), e **List** para campos específicos de fluxos (ex: Assunto, Prioridade)
- Onde houver equivalentes nativos do ClickUp (Assignees, Tags, Status), usar nativos e complementar com CF apenas se necessário

---

## Campos Personalizados Necessários no ClickUp

Esta seção lista **todos** os campos personalizados que devem ser criados no ClickUp para a sincronização correta com o sistema.

### 📋 Tabela Resumo dos Campos

| Campo no ClickUp             | Tipo no ClickUp          | Descrição no ClickUp | Nível        | Campo Origem (Sistema)      | Justificativa |
|------------------------------|--------------------------|----------------------|--------------|----------------------------|---------------|
| `Assunto`                    | Texto                    | Resumo ou assunto principal do atendimento | List         | `assunto`                  | Resumo legível no card além do título |
| `Canal`                      | Lista suspensa           | Canal de comunicação utilizado pelo cliente (WhatsApp, Email, Telefone, Web) | Workspace    | `canal`                    | Estratégia e métricas por canal (WhatsApp, e-mail etc.) |
| `Contato`                    | Texto                    | Nome completo do contato que está sendo atendido | Workspace    | `contato.nome`             | Atendimento humanizado e melhor triagem |
| `Telefone`                   | Telefone                 | Número de telefone do contato para comunicação direta | Workspace    | `contato.telefone`         | Contato rápido; integrações de discagem |
| `Email`                      | E-mail                   | Endereço de e-mail do contato para follow-up | Workspace    | `contato.email`            | Escalonamento e follow-up por e-mail |
| `Nome Perfil WhatsApp`       | Texto                    | Nome exibido no perfil do WhatsApp do contato | Workspace    | `contato.nome_perfil_whatsapp` | Identificação consistente com o perfil do WhatsApp |
| `Início do Atendimento`      | Data                     | Data e hora de início do atendimento | Workspace    | `data_inicio`              | Ponto inicial para SLA e métricas operacionais |
| `Fim do Atendimento`         | Data                     | Data e hora de conclusão do atendimento | Workspace    | `data_fim`                 | Cálculo de tempo total de atendimento |
| `Última Mensagem`            | Data                     | Data e hora da última mensagem recebida ou enviada | Workspace    | `data_ultima_mensagem`     | Ajuda no ordenamento e triagem por recência |
| `Prioridade (Local)`         | Rótulos                  | Nível de prioridade do atendimento (Baixa, Normal, Alta, Urgente) | List         | `prioridade`               | Permite múltiplos níveis e cores diferentes |
| `Atendente`                  | Pessoas                  | Atendente humano responsável pelo atendimento | Workspace    | `atendente_humano`         | Destaca o responsável pelo caso como campo dedicado |
| `Nome Fantasia`              | Texto                    | Nome comercial/fantasia da empresa cliente | Workspace    | `cliente.nome_fantasia`    | Identificação comercial clara do cliente |
| `Ramo de Atividade`          | Texto                    | Setor ou ramo de atividade da empresa cliente | Workspace    | `cliente.ramo_atividade`   | Segmentação e análise por setor |
| `Observações`                | Área de texto            | Observações e notas importantes sobre o cliente | Workspace    | `cliente.observacoes`      | Contexto adicional para atendimento e histórico |

### 📝 Campos Nativos do ClickUp (Não criar como Custom Fields)

Estes campos já existem nativamente no ClickUp e devem ser utilizados:

- **Status**: Mapeado para `etapa_atual` (Status da List)
- **Tags**: Tags nativas do ClickUp para categorização (mapeado para `tags`)
- **Assignees**: Também pode ser usado junto com o campo `Atendente` para designar responsáveis

---

## Detalhamento dos Campos Personalizados

### 1. Campos de Informação do Contato

#### `Contato` (Texto - Workspace)
- **Origem**: `contato.nome`
- **Descrição**: Nome completo do contato que está sendo atendido
- **Finalidade**: Nome do contato para atendimento humanizado

#### `Telefone` (Telefone - Workspace)
- **Origem**: `contato.telefone`
- **Descrição**: Número de telefone do contato para comunicação direta
- **Finalidade**: Contato direto, integrações de discagem

#### `Email` (E-mail - Workspace)
- **Origem**: `contato.email`
- **Descrição**: Endereço de e-mail do contato para follow-up
- **Finalidade**: Escalonamento e follow-up

#### `Nome Perfil WhatsApp` (Texto - Workspace)
- **Origem**: `contato.nome_perfil_whatsapp`
- **Descrição**: Nome exibido no perfil do WhatsApp do contato
- **Finalidade**: Identificação consistente com perfil WhatsApp

### 2. Campos de Informação do Cliente

#### `Nome Fantasia` (Texto - Workspace)
- **Origem**: `cliente.nome_fantasia`
- **Descrição**: Nome comercial/fantasia da empresa cliente
- **Finalidade**: Identificação comercial do cliente

#### `Ramo de Atividade` (Texto - Workspace)
- **Origem**: `cliente.ramo_atividade`
- **Descrição**: Setor ou ramo de atividade da empresa cliente
- **Finalidade**: Segmentação por setor
- **Observação**: Campo de texto para permitir valores dinâmicos

#### `Observações` (Área de texto - Workspace)
- **Origem**: `cliente.observacoes`
- **Descrição**: Observações e notas importantes sobre o cliente
- **Finalidade**: Contexto adicional e histórico

### 3. Campos de Controle do Atendimento

#### `Assunto` (Texto - List)
- **Origem**: `assunto`
- **Descrição**: Resumo ou assunto principal do atendimento
- **Finalidade**: Resumo legível além do título

#### `Canal` (Lista suspensa - Workspace)
- **Origem**: `canal`
- **Descrição**: Canal de comunicação utilizado pelo cliente (WhatsApp, Email, Telefone, Web)
- **Opções**: `WhatsApp`, `Email`, `Telefone`, `Web`
- **Finalidade**: Identificação imediata do canal de origem

#### `Prioridade (Local)` (Rótulos - List)
- **Origem**: `prioridade`
- **Descrição**: Nível de prioridade do atendimento (Baixa, Normal, Alta, Urgente)
- **Opções**:
  - `Baixa` (Azul: #00A0E3)
  - `Normal` (Cinza: #B7B7B7)
  - `Alta` (Laranja: #FFA500)
  - `Urgente` (Vermelho: #FF3333)
- **Finalidade**: Identificação visual rápida por cores

#### `Atendente` (Pessoas - Workspace)
- **Origem**: `atendente_humano`
- **Descrição**: Atendente humano responsável pelo atendimento
- **Finalidade**: Identificação do responsável pelo atendimento

### 4. Campos de Datas e SLA

#### `Início do Atendimento` (Data - Workspace)
- **Origem**: `data_inicio`
- **Descrição**: Data e hora de início do atendimento
- **Finalidade**: Cálculo de SLA e métricas

#### `Fim do Atendimento` (Data - Workspace)
- **Origem**: `data_fim`
- **Descrição**: Data e hora de conclusão do atendimento
- **Finalidade**: Cálculo de tempo total

#### `Última Mensagem` (Data - Workspace)
- **Origem**: `data_ultima_mensagem`
- **Descrição**: Data e hora da última mensagem recebida ou enviada
- **Finalidade**: Ordenamento por recência

---

## Status e Fluxo: Mapeamento

### Mapeamento de Etapas para Status

- `etapa_atual` deve ser mapeada para o **Status** da List correspondente
- Sugestão de correspondência (ajustável por fluxo):
  - `FILA` → `Novo` (type: `open`)
  - `EM_ATENDIMENTO` → `Em atendimento` (type: `open`)
  - `PENDENCIA` → `Aguardando cliente` (type: `open`)
  - `TRANSFERIDO` → `Transferido` (type: `open`)
  - `RESOLVIDO` → `Resolvido` (type: `closed`)
  - `CANCELADO` → `Cancelado` (type: `closed`)

---

## Guia de Criação Manual dos Campos no ClickUp

### Passo 1: Ativar o ClickApp de Custom Fields

1. Abra o **App Center**
2. No menu lateral, selecione "All ClickApps"
3. Procure por "Custom Fields" e ative o ClickApp
4. Selecione os Spaces onde deseja ativar

### Passo 2: Criar Campos de Workspace

Crie os seguintes campos no nível **Workspace** (para reutilização em todas as Lists):

#### Campos de Texto
1. **Contato**
   - Tipo: Texto
   - Descrição: `Nome completo do contato que está sendo atendido`

2. **Nome Fantasia**
   - Tipo: Texto
   - Descrição: `Nome comercial/fantasia da empresa cliente`

3. **Nome Perfil WhatsApp**
   - Tipo: Texto
   - Descrição: `Nome exibido no perfil do WhatsApp do contato`

4. **Ramo de Atividade**
   - Tipo: Texto
   - Descrição: `Setor ou ramo de atividade da empresa cliente`

#### Campos de Área de Texto
5. **Observações**
   - Tipo: Área de texto
   - Descrição: `Observações e notas importantes sobre o cliente`

#### Campos Específicos
6. **Telefone**
   - Tipo: Telefone
   - Descrição: `Número de telefone do contato para comunicação direta`

7. **Email**
   - Tipo: E-mail
   - Descrição: `Endereço de e-mail do contato para follow-up`

8. **Atendente**
   - Tipo: Pessoas
   - Descrição: `Atendente humano responsável pelo atendimento`

#### Campos de Data
9. **Início do Atendimento**
   - Tipo: Data
   - Descrição: `Data e hora de início do atendimento`

10. **Fim do Atendimento**
    - Tipo: Data
    - Descrição: `Data e hora de conclusão do atendimento`

11. **Última Mensagem**
    - Tipo: Data
    - Descrição: `Data e hora da última mensagem recebida ou enviada`

#### Campos de Lista Suspensa
12. **Canal**
    - Tipo: Lista suspensa
    - Descrição: `Canal de comunicação utilizado pelo cliente (WhatsApp, Email, Telefone, Web)`
    - Opções: `WhatsApp`, `Email`, `Telefone`, `Web`

### Passo 3: Criar Campos de List

Crie os seguintes campos no nível **List** (específicos para cada fluxo):

1. **Assunto**
   - Tipo: Texto
   - Descrição: `Resumo ou assunto principal do atendimento`

2. **Prioridade (Local)**
   - Tipo: Rótulos
   - Descrição: `Nível de prioridade do atendimento (Baixa, Normal, Alta, Urgente)`
   - Opções:
     - `Baixa` (cor: #00A0E3 - Azul)
     - `Normal` (cor: #B7B7B7 - Cinza)
     - `Alta` (cor: #FFA500 - Laranja)
     - `Urgente` (cor: #FF3333 - Vermelho)

### Passo 4: Validação

1. Abra uma task na List
2. Verifique se todos os campos criados aparecem
3. Teste preenchendo valores para garantir persistência

---

## Implementação via ClickUp API

### 1. Criar Campo de Texto

```python
import requests

API_TOKEN = "seu_token_aqui"
WORKSPACE_ID = "id_do_workspace"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def criar_campo_texto(workspace_id, field_name, description):
    """Cria um campo de texto no ClickUp."""
    url = f"https://api.clickup.com/api/v2/workspace/{workspace_id}/field"
    
    data = {
        "name": field_name,
        "type": "text",
        "description": description
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Exemplo de uso
campo_contato = criar_campo_texto(
    WORKSPACE_ID, 
    "Contato",
    "Nome completo do contato que está sendo atendido"
)
print(f"Campo criado: {campo_contato}")
```

### 2. Criar Campo de Lista Suspensa

```python
def criar_campo_lista_suspensa(workspace_id, field_name, description, options):
    """Cria um campo de lista suspensa no ClickUp."""
    url = f"https://api.clickup.com/api/v2/workspace/{workspace_id}/field"
    
    data = {
        "name": field_name,
        "type": "drop_down",
        "description": description,
        "type_config": {
            "options": [
                {"name": option, "orderindex": idx} 
                for idx, option in enumerate(options)
            ]
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Exemplo de uso
opcoes_canal = ["WhatsApp", "Email", "Telefone", "Web"]
campo_canal = criar_campo_lista_suspensa(
    WORKSPACE_ID,
    "Canal",
    "Canal de comunicação utilizado pelo cliente (WhatsApp, Email, Telefone, Web)",
    opcoes_canal
)
print(f"Campo criado: {campo_canal}")
```

### 3. Criar Campo de Rótulos (Prioridade)

```python
def criar_campo_rotulos_prioridade(list_id):
    """Cria campo de rótulos para prioridades na List."""
    url = f"https://api.clickup.com/api/v2/list/{list_id}/field"
    
    data = {
        "name": "Prioridade (Local)",
        "type": "labels",
        "description": "Nível de prioridade do atendimento (Baixa, Normal, Alta, Urgente)",
        "type_config": {
            "sorting": "manual",
            "options": [
                {"name": "Baixa", "color": "#00A0E3", "orderindex": 0},
                {"name": "Normal", "color": "#B7B7B7", "orderindex": 1},
                {"name": "Alta", "color": "#FFA500", "orderindex": 2},
                {"name": "Urgente", "color": "#FF3333", "orderindex": 3}
            ]
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()
```

### 4. Criar Campo de Data

```python
def criar_campo_data(workspace_id, field_name, description):
    """Cria um campo de data no ClickUp."""
    url = f"https://api.clickup.com/api/v2/workspace/{workspace_id}/field"
    
    data = {
        "name": field_name,
        "type": "date",
        "description": description
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Exemplo de uso
campo_data_inicio = criar_campo_data(
    WORKSPACE_ID,
    "Início do Atendimento",
    "Data e hora de início do atendimento"
)
```

### 5. Criar Campo de Telefone

```python
def criar_campo_telefone(workspace_id, field_name, description):
    """Cria um campo de telefone no ClickUp."""
    url = f"https://api.clickup.com/api/v2/workspace/{workspace_id}/field"
    
    data = {
        "name": field_name,
        "type": "phone",
        "description": description
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()
```

### 6. Criar Campo de E-mail

```python
def criar_campo_email(workspace_id, field_name, description):
    """Cria um campo de e-mail no ClickUp."""
    url = f"https://api.clickup.com/api/v2/workspace/{workspace_id}/field"
    
    data = {
        "name": field_name,
        "type": "email",
        "description": description
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()
```

### 7. Criar Campo de Área de Texto

```python
def criar_campo_area_texto(workspace_id, field_name, description):
    """Cria um campo de área de texto no ClickUp."""
    url = f"https://api.clickup.com/api/v2/workspace/{workspace_id}/field"
    
    data = {
        "name": field_name,
        "type": "text_area",
        "description": description
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()
```

### 8. Criar Campo de Pessoas

```python
def criar_campo_pessoas(workspace_id, field_name, description):
    """Cria um campo de pessoas no ClickUp."""
    url = f"https://api.clickup.com/api/v2/workspace/{workspace_id}/field"
    
    data = {
        "name": field_name,
        "type": "users",
        "description": description
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()
```

---

## Script Completo para Criação Automática

```python
import requests
import json

# Configurações
API_TOKEN = "seu_token_aqui"
WORKSPACE_ID = "id_do_workspace"
LIST_ID = "id_da_lista"  # Para campos de List

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def criar_campo(workspace_id, field_name, field_type, description, type_config=None, list_id=None):
    """Função genérica para criar um campo no ClickUp."""
    url = f"https://api.clickup.com/api/v2/workspace/{workspace_id}/field"
    
    if list_id:
        url = f"https://api.clickup.com/api/v2/list/{list_id}/field"
    
    data = {
        "name": field_name,
        "type": field_type,
        "description": description
    }
    
    if type_config:
        data["type_config"] = type_config
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

def criar_todos_os_campos_workspace(workspace_id):
    """Cria todos os campos de Workspace."""
    print("=== Criando Campos de Workspace ===")
    
    # Campos de texto
    campos_texto = [
        ("Contato", "Nome completo do contato que está sendo atendido"),
        ("Nome Fantasia", "Nome comercial/fantasia da empresa cliente"),
        ("Nome Perfil WhatsApp", "Nome exibido no perfil do WhatsApp do contato"),
        ("Ramo de Atividade", "Setor ou ramo de atividade da empresa cliente")
    ]
    
    for nome, desc in campos_texto:
        resultado = criar_campo(workspace_id, nome, "text", desc)
        print(f"✓ Campo '{nome}' criado")
    
    # Campo de área de texto
    resultado = criar_campo(
        workspace_id,
        "Observações",
        "text_area",
        "Observações e notas importantes sobre o cliente"
    )
    print(f"✓ Campo 'Observações' criado")
    
    # Campos específicos
    resultado = criar_campo(
        workspace_id,
        "Telefone",
        "phone",
        "Número de telefone do contato para comunicação direta"
    )
    print(f"✓ Campo 'Telefone' criado")
    
    resultado = criar_campo(
        workspace_id,
        "Email",
        "email",
        "Endereço de e-mail do contato para follow-up"
    )
    print(f"✓ Campo 'Email' criado")
    
    resultado = criar_campo(
        workspace_id,
        "Atendente",
        "users",
        "Atendente humano responsável pelo atendimento"
    )
    print(f"✓ Campo 'Atendente' criado")
    
    # Campos de data
    campos_data = [
        ("Início do Atendimento", "Data e hora de início do atendimento"),
        ("Fim do Atendimento", "Data e hora de conclusão do atendimento"),
        ("Última Mensagem", "Data e hora da última mensagem recebida ou enviada")
    ]
    
    for nome, desc in campos_data:
        resultado = criar_campo(workspace_id, nome, "date", desc)
        print(f"✓ Campo '{nome}' criado")
    
    # Campo de lista suspensa (Canal)
    type_config = {
        "options": [
            {"name": option, "orderindex": idx}
            for idx, option in enumerate(["WhatsApp", "Email", "Telefone", "Web"])
        ]
    }
    resultado = criar_campo(
        workspace_id,
        "Canal",
        "drop_down",
        "Canal de comunicação utilizado pelo cliente (WhatsApp, Email, Telefone, Web)",
        type_config
    )
    print(f"✓ Campo 'Canal' criado")

def criar_todos_os_campos_list(list_id):
    """Cria todos os campos de List."""
    print("\n=== Criando Campos de List ===")
    
    # Campo de texto (Assunto)
    resultado = criar_campo(
        None,
        "Assunto",
        "text",
        "Resumo ou assunto principal do atendimento",
        list_id=list_id
    )
    print(f"✓ Campo 'Assunto' criado")
    
    # Campo de rótulos (Prioridade)
    type_config = {
        "sorting": "manual",
        "options": [
            {"name": "Baixa", "color": "#00A0E3", "orderindex": 0},
            {"name": "Normal", "color": "#B7B7B7", "orderindex": 1},
            {"name": "Alta", "color": "#FFA500", "orderindex": 2},
            {"name": "Urgente", "color": "#FF3333", "orderindex": 3}
        ]
    }
    resultado = criar_campo(
        None,
        "Prioridade (Local)",
        "labels",
        "Nível de prioridade do atendimento (Baixa, Normal, Alta, Urgente)",
        type_config,
        list_id
    )
    print(f"✓ Campo 'Prioridade (Local)' criado")

# Executar criação
if __name__ == "__main__":
    criar_todos_os_campos_workspace(WORKSPACE_ID)
    criar_todos_os_campos_list(LIST_ID)
    print("\n✅ Todos os campos foram criados com sucesso!")
```

---

## Plano de Implementação via ClickUp API

### 1. Descoberta de IDs
- `GET /api/v2/team` → `team_id`
- Criar/obter `space_id` e `folder_id` conforme planejamento
- `POST /api/v2/space/{space_id}/folder` (Departamento)
- `POST /api/v2/folder/{folder_id}/list` (Fluxo do Departamento)

### 2. Configuração de Status (List)
- Enviar `statuses` já na criação da List
- Fallback/idempotência: `PUT /api/v2/list/{list_id}` com `statuses`
- Persistir correlação `EtapaFluxo.nome` ↔ `status` para sincronização

### 3. Custom Fields (CF)
- Descoberta e reuso: `GET /api/v2/team/{team_id}/field` (Workspace)
- Anexar CF à List: `GET/POST /api/v2/list/{list_id}/field`
- Setar valor no card: `POST /api/v2/task/{task_id}/field/{field_id}`

### 4. Criação e Atualização de Cards (Tasks)
- Criar: `POST /api/v2/list/{list_id}/task` com `name`, `status`, `assignees`
- Atualizar Status: `PUT /api/v2/task/{task_id}`
- Setar CFs: `POST /api/v2/task/{task_id}/field/{field_id}` por campo

### 5. Webhooks
- `POST /api/v2/team/{team_id}/webhook` (events: task create/update/move/status change)
- Consumir no Django e refletir mudanças ao sistema interno

### 6. Persistência de Mapeamento
- Manter tabela/local store com `field_id` por CF, por List/Workspace
- Validar compatibilidade de tipos antes de setar valores

---

## Checklist de Sincronização

- [ ] Lists têm `statuses` coerentes com `EtapaFluxo`
- [ ] CFs de Workspace anexados às Lists de todos os Departamentos
- [ ] `field_id` persistidos e versionados
- [ ] Criação de Task popula: `Canal`, `Contato/Telefone/Email`, `Nome Perfil WhatsApp`, dados de Cliente (`Nome Fantasia`, `Ramo de Atividade`, `Observações`), e `Atendente`
- [ ] Movimentos atualizam `status` e CFs de datas (Início/Fim/Última Mensagem)
- [ ] Comentários de mensagens incluem `Intent` e `Entidades` conforme padrão definido
- [ ] Webhooks refletem mudanças de ClickUp para o sistema interno

---

## Limites de Custom Fields (ClickUp)

- **Quantidade de campos**: Sem limite explícito de quantos campos podem ser criados
- **Limite de uso (Free)**: 60 usos de Custom Fields (um "uso" = adicionar valor a um campo em uma task)
- **Planos pagos**: Usos **ilimitados** de Custom Fields
- **Opções por campo**: Até **500 opções** para campos `Dropdown` e `Label`
- **Campos obrigatórios**: Disponíveis a partir do plano **Business**

> **Referências oficiais**:
> - [Custom Fields uses](https://help.clickup.com/hc/en-us/articles/10993484102167-Custom-Fields-uses)
> - [Intro to Custom Fields](https://help.clickup.com/hc/en-us/articles/6303536766231-Intro-to-Custom-Fields)
> - [Create Custom Fields](https://help.clickup.com/hc/en-us/articles/6303481086487-Create-Custom-Fields)

---

## Mensagens e Comentários (Intent e Entidades)

- Mensagens do atendimento devem ser registradas como comentários na Task
- Em cada comentário, incluir obrigatoriamente os campos `Intent` e `Entidades`
- **Formato recomendado**:

```
Mensagem: "Cliente solicitou atualização de cadastro"
Intent: Atualizar cadastro
Entidades: nome_cliente=ACME Ltda; novo_endereco=Rua X, 123
```

- **Alternativa em JSON** (como bloco de texto no comentário):

```json
{
  "intent": "Atualizar cadastro",
  "entities": {
    "nome_cliente": "ACME Ltda",
    "novo_endereco": "Rua X, 123"
  }
}
```

- **Integração via API**: postar comentário com `comment_text` contendo a mensagem e os campos `Intent` e `Entidades`

### Exemplo de Requisição

```python
POST https://api.clickup.com/api/v2/task/{task_id}/comment
Authorization: Bearer <token>
{
  "comment_text": "Mensagem: Cliente solicitou atualização de cadastro\nIntent: Atualizar cadastro\nEntidades: nome_cliente=ACME Ltda; novo_endereco=Rua X, 123"
}
```

---

## Segurança e Operação

- **Autenticação**: `Authorization: Bearer <token>` via variável de ambiente (ex: `CLICKUP_TOKEN`), sem segredos em código
- **Logs estruturados**: Usar `loguru` e saídas mais ricas com `rich` em scripts
- **Testes**: Rodar sempre em Docker com `uv run task test-docker` e cobertura ≥80% para integrações críticas (CF set/get, status, webhooks)

---

## Observações Finais

- Priorizar o uso de campos nativos de ClickUp (Status, Assignees, Tags) e suplementar com CFs apenas para contexto adicional
- Campos derivados do `contato` e `cliente` são críticos para visão 360º do cliente no card
- Manter conversão interna para os `statuses` da List sem criar CF redundante
- Estrutura de campos segue arquitetura de Workspace (reutilizáveis) e List (específicos por fluxo)
- **Importante**: Ao criar cada campo no ClickUp, utilize as descrições fornecidas na coluna "Descrição no ClickUp" da tabela resumo para facilitar o entendimento e manutenção futura