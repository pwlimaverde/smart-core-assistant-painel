# Mapeamento de Campos do Atendimento para Custom Fields no ClickUp

## Visão Geral

Este documento propõe um mapeamento detalhado dos campos do model
`Atendimento` (app `atendimentos`) para campos personalizados (Custom
Fields) em cards do ClickUp, com foco em enriquecer o contexto para os
atendentes na Central de Atendimento. A proposta considera a arquitetura
por Departamentos (Folder), Fluxos por departamento (List) e Etapas
(`EtapaFluxo`) mapeadas para Status da List.

- Base técnica: Django + PostgreSQL, UI Kanban por departamento.
- Integração: ClickUp API v2 (`Authorization: Bearer <token>`).
- Referências: `CENTRAL_DE_ATENDIMENTO.md` e `02_plano_de_integracao.md`.

## Campos do Model `Atendimento`

Campos principais identificados no model (`src/.../atendimentos/models.py`):

- `id` (AutoField)
- `contato` (FK `clientes.Contato`)
- `departamento` (FK `operacional.Departamento`)
- `fluxo_atendimento` (FK `operacional.FluxoAtendimento`)
- `status` (Enum `StatusAtendimento` – legado)
- `etapa_atual` (FK `operacional.EtapaFluxo` – etapa no fluxo)
- `data_inicio` (DateTime)
- `data_fim` (DateTime | null)
- `data_ultima_mensagem` (DateTime | null)
- `assunto` (Char | null)
- `prioridade` (Char; baixa/normal/alta/urgente)
- `atendente_humano` (FK `operacional.Atendente` | null)
- `contexto_conversa` (JSON)
- `historico_status` (JSON list)
- `tags` (JSON list)
- `avaliacao` (Integer 1–5 | null)
- `feedback` (Text | null)
- `data_primeira_resposta` (DateTime | null)
- `canal` (Char; whatsapp/email/telefone/web)

## Mapeamento para Custom Fields no ClickUp

Princípios:

- Campos que melhoram a leitura rápida do card, contexto do cliente,
  SLAs e próximos passos.
- Reuso preferencial em **Workspace** para padrões (Canal, Avaliação),
  e **List** para campos específicos de fluxos (Ex.: Resumo).
- Onde houver equivalentes nativos do ClickUp (Assignees, Priority,
  Status), usar nativos e complementar com CF apenas se necessário.

| Campo (Model)             | CF no ClickUp (nome)         | Tipo CF no ClickUp       | Nível        | Por que é importante |
|---------------------------|-------------------------------|--------------------------|--------------|----------------------|
| `departamento`            | `Department`                  | Lista suspensa           | Workspace    | Filtro e agregação cross-list; visível mesmo fora da pasta. |
| `fluxo_atendimento`       | `Flow`                        | Texto                    | List         | Ajuda a identificar o fluxo quando há múltiplos por pasta. |
| `etapa_atual` → Status    | — (usar Status da List)       | —                        | List         | Alinha com Kanban nativo; evita duplicação de status. |
| `status` (legado)         | —                             | —                        | —            | Não criar CF; manter compatibilidade interna apenas. |
| `assunto`                 | `Subject (Summary)`           | Texto                    | List         | Resumo legível no card, além do título quando necessário. |
| `data_inicio`             | `Service Start`               | Data                     | Workspace    | Ponto inicial para SLA e métricas operacionais. |
| `data_fim`                | `Service End`                 | Data                     | Workspace    | Cálculo de tempo total de atendimento. |
| `data_ultima_mensagem`    | `Last Message At`             | Data                     | Workspace    | Ajuda no ordenamento e triagem por recência. |
| `prioridade`              | `Priority (Local)`            | Lista suspensa           | List         | Alternativa ao nativo; útil se granularidade difere do padrão. |
| `atendente_humano`        | `Atendente`                   | Pessoas                  | Workspace    | Destaca o responsável pelo caso como campo dedicado. |
| `historico_status`        | —                             | —                        | —            | Removido do card (não exibir). |
| `tags`                    | — (usar `tags` nativo)        | —                        | —            | Tags nativas do ClickUp para categorização. |
| `canal`                   | `Channel`                     | Lista suspensa           | Workspace    | Estratégia e métricas por canal (WhatsApp, e-mail etc.). |

### Campos derivados recomendados (do relacionamento `contato`)

Para enriquecer o entendimento, é valioso expor dados-chave do contato:

| Origem                        | CF no ClickUp (nome)   | Tipo CF no ClickUp    | Nível      | Benefício |
|-------------------------------|------------------------|-----------------------|------------|-----------|
| `contato.nome`                | `Contato`              | Texto                 | Workspace  | Atendimento humanizado e melhor triagem. |
| `contato.telefone`            | `Telefone`             | Telefone              | Workspace  | Contato rápido; integrações de discagem. |
| `contato.email`               | `Email`                | E-mail                | Workspace  | Escalonamento e follow-up por e-mail. |
| `contato.nome_perfil_whatsapp`| `Nome Perfil WhatsApp` | Texto                 | Workspace  | Identificação consistente com o perfil do WhatsApp. |
| `contato.metadados`           | `Metadados do Contato` | Área de texto         | Workspace  | Referências técnicas/CRM para auditoria e contexto. |

> Observação: estes campos são populados a partir da FK `contato`. Caso o
> model não exponha todos os atributos, usar services para leitura
> agregada no momento da sincronização com ClickUp.

### Campos derivados recomendados (do relacionamento `cliente`)

Para enriquecer o contexto empresarial, expor dados-chave do cliente:

| Origem              | CF no ClickUp (nome)  | Tipo CF no ClickUp    | Nível     | Benefício |
|---------------------|-----------------------|-----------------------|-----------|-----------|
| `cliente.nome_fantasia` | `Nome Fantasia`     | Texto                 | Workspace | Identificação comercial clara do cliente. |
| `cliente.ramo_atividade`| `Ramo de Atividade` | Lista suspensa        | Workspace | Segmentação e análise por setor. |
| `cliente.observacoes`   | `Observações`       | Área de texto         | Workspace | Contexto adicional para atendimento e histórico. |
| `cliente.metadados`     | `Metadados do Cliente` | Área de texto       | Workspace | Metadados estruturados (JSON/texto) para consulta técnica. |

## Status e Fluxo: Diretrizes de Mapeamento

- `EtapaFluxo` deve ser mapeada para o **Status** da List correspondente.
- Sugestão de correspondência (ajustável por fluxo):
  - `FILA` → `Novo` (type: `open`)
  - `EM_ATENDIMENTO` → `Em atendimento` (type: `open`)
  - `PENDENCIA` → `Aguardando cliente` (type: `open`)
  - `TRANSFERIDO` → `Transferido` (type: `open` ou mover para a fila do
    novo departamento)
  - `RESOLVIDO` → `Resolvido` (type: `closed`)
  - `CANCELADO` → `Cancelado` (type: `closed`)

- Manter a coerência entre `departamento`, `fluxo_atendimento` e
  `etapa_atual` (já validado em `clean()` no Django).

## Plano de Implementação via ClickUp API

1. Descoberta de IDs
   - `GET /api/v2/team` → `team_id`.
   - Criar/obter `space_id` e `folder_id` conforme planejamento.
   - `POST /api/v2/space/{space_id}/folder` (Departamento).
   - `POST /api/v2/folder/{folder_id}/list` (Fluxo do Departamento).

2. Configuração de Status (List)
   - Enviar `statuses` já na criação da List.
   - Fallback/idempotência: `PUT /api/v2/list/{list_id}` com `statuses`.
   - Persistir correlação `EtapaFluxo.nome` ↔ `status` para sincronização.

3. Custom Fields (CF)
   - Descoberta e reuso: `GET /api/v2/team/{team_id}/field` (Workspace).
   - Anexar CF à List: `GET/POST /api/v2/list/{list_id}/field`.
   - Setar valor no card: `POST /api/v2/task/{task_id}/field/{field_id}`.
   - Estratégia: campos **Workspace** para reuso (Channel, Rating, datas),
     campos **List** para contexto específico (Subject, Conversation Context).

4. Criação e Atualização de Cards (Tasks)
   - Criar: `POST /api/v2/list/{list_id}/task` com `name`, `status`,
     `assignees` (usar nativo para `atendente_humano`).
   - Atualizar Status: `PUT /api/v2/task/{task_id}`.
   - Setar CFs: `POST /api/v2/task/{task_id}/field/{field_id}` por campo.

5. Webhooks
   - `POST /api/v2/team/{team_id}/webhook` (events: task create/update/move/status change).
   - Consumir no Django e refletir mudanças ao sistema interno.

6. Persistência de Mapeamento
   - Manter tabela/local store com `field_id` por CF, por List/Workspace.
   - Validar compatibilidade de tipos antes de setar valores.

### Exemplos de Requisição (resumo)

- Criar List com Status personalizados:

```
POST https://api.clickup.com/api/v2/folder/{folder_id}/list
Authorization: Bearer <token>
{
  "name": "Fluxo Atendimento WhatsApp",
  "statuses": [
    {"status": "Novo", "type": "open"},
    {"status": "Em atendimento", "type": "open"},
    {"status": "Aguardando cliente", "type": "open"},
    {"status": "Resolvido", "type": "closed"}
  ]
}
```

- Adicionar comentário com intent e entidades:

```
POST https://api.clickup.com/api/v2/task/{task_id}/comment
Authorization: Bearer <token>
{
  "comment_text": "Mensagem: Cliente solicitou atualização de cadastro\nIntent: Atualizar cadastro\nEntidades: nome_cliente=ACME Ltda; novo_endereco=Rua X, 123"
}
```

## Justificativas por Campo (Resumo)

- `Channel`: imediatamente destaca o canal de origem, melhorando priorização
  e roteamento.
- `First Response At` e `Service Start/End`: possibilitam SLAs confiáveis
  e auditoria.
- `Last Message At`: ordena por recência e evita estagnação de casos.
- `Customer Rating` e `Customer Feedback`: insights de satisfação e motivos
  para melhoria contínua.
- `Department` e `Flow`: reforçam contexto quando cards são vistos fora
  da pasta/list.
- `Subject (Summary)` e `Conversation Context`: balanceiam legibilidade e
  detalhamento sem poluir a descrição.
- `Contact Name/Phone/Email/ID` (derivados): acessibilidade e correlação
  rápida com o CRM interno.

## Segurança e Operação

- Autenticação: `Authorization: Bearer <token>` via variável de ambiente
  (ex.: `CLICKUP_TOKEN`), sem segredos em código.
- Logs estruturados: usar `loguru` e saídas mais ricas com `rich` em scripts.
- Testes: rodar sempre em Docker com `uv run task test-docker` e cobertura
  ≥80% para integrações críticas (CF set/get, status, webhooks).

## Limites de Custom Fields (ClickUp)

- Quantidade de campos: a documentação oficial não define um limite
  explícito de quantos campos personalizados você pode criar por
  Workspace/Space/Folder/List. O limite relevante é de **uso** de
  Custom Fields no plano Free.
- Limite de uso (Free): no plano Free, há **60 usos** de Custom Fields.
  Um “uso” é contabilizado cada vez que você adiciona um valor a um
  Custom Field em uma task. Após atingir 60 usos, você não poderá
  adicionar valores até fazer upgrade. Referência oficial: Custom Fields
  uses (ClickUp Help).
  - Fonte: https://help.clickup.com/hc/en-us/articles/10993484102167-Custom-Fields-uses
  - Introdução: https://help.clickup.com/hc/en-us/articles/6303536766231-Intro-to-Custom-Fields
- Planos pagos: os planos pagos oferecem **usos ilimitados** de Custom
  Fields.
- Opções por campo: para `Dropdown` e `Label`, é possível criar até
  **500 opções** por campo. Fonte: Create Custom Fields (ClickUp Help).
  - Fonte: https://help.clickup.com/hc/en-us/articles/6303481086487-Create-Custom-Fields
- Campos obrigatórios: “Required Custom Fields” estão disponíveis a
  partir do plano **Business** e acima.

> Em resumo: você pode criar os campos necessários para o mapeamento; o
> principal limitador no plano Free é o número de vezes que você consegue
> definir valores (60 usos). Em planos pagos, esse limitador não existe.

## Instruções para criar os campos manualmente no ClickUp

Siga este passo a passo para criar os Custom Fields e anexá-los às suas
Lists/Spaces conforme o mapeamento acima.

1) Ativar o ClickApp de Custom Fields (se ainda não estiver ativo)

- Abra o App Center.
- No menu lateral, selecione “All ClickApps”.
- Procure por “Custom Fields” e ative o ClickApp.
- Opcional: selecione os Spaces onde o ClickApp deve ficar ativo.

2) Criar campos pelo Custom Field Manager (recomendado para organização)

- Abra o “Custom Field Manager”.
- No sidebar, selecione a localização de destino: `Workspace`, ou um
  `Space`, `Folder` ou `List` específica.
- Clique em “Create new field”.
- Escolha o tipo correto (Short Text, Long Text, Dropdown, Label,
  Date/Time, Number, Phone, Email, URL, etc.).
- Nomeie o campo conforme o mapeamento proposto (ex.: `Canal`,
  `Departamento`, `Assunto`, `Atendente`, `Nome Fantasia`, `Ramo de Atividade`).
- Para `Dropdown/Label`, cadastre as opções necessárias (ex.: canais
  “WhatsApp”, “Email”, “Telefone”; prioridades locais “baixa”, “normal”,
  “alta”, “urgente”).
- Clique em “Create”. O campo será disponibilizado para todas as tasks
  da localização selecionada.

3) Criar campos a partir de uma List/Table view (alternativa prática)

- Acesse a List/Space/Folder desejada e abra a List ou Table view.
- No topo direito da tabela, clique no ícone de `+` (ou no menu
  `...` → “Add a column”).
- Pesquise e selecione o tipo de campo.
- Nomeie e personalize o campo.
- Clique em “Create”. O campo será adicionado como coluna e aplicado às
  tasks na localização da view.

4) Criar campos diretamente dentro de uma Task

- Abra uma task na List desejada.
- Role até a seção “Custom Fields” e clique no `+`.
- Selecione “Create field”, escolha o tipo e nomeie.
- Clique em “Create”. O campo será aplicado a todas as tasks da List.

5) Anexar campos já existentes a novas localizações

- Use o Custom Field Manager para adicionar um campo existente a outros
  Spaces/Folders/Lists do Workspace.
- Isso permite reuso consistente de `Workspace` fields (ex.: `Channel`,
  `Atendente`, `Canal`, datas) em diversas Lists.

6) Boas práticas de nomenclatura e tipos

- Prefira nomes em português para consistência operacional: `Assunto`,
  `Departamento`, `Etapa`, `Canal`, `Início do Atendimento`, `Fim do Atendimento`,
  `Última Mensagem`, `Contato`, `Telefone`, `Email`, `Nome Perfil WhatsApp`,
  `Nome Fantasia`, `Ramo de Atividade`, `Observações`, `Metadados do Contato`,
  `Metadados do Cliente`, `Atendente`.
- Garanta que o tipo do campo esteja correto (ex.: `DateTime` para
  datas, `Dropdown/Label` com opções, `Phone` para telefone, `Email` para
  e-mail, `Number` para avaliação).

7) Validação rápida

- Após criar e anexar os campos, abra uma task e aplique valores em
  alguns deles para garantir que aparecem e persistem.
- Em seguida, valide a sincronização automática pelo sistema e verifique
  os valores dos campos no card.

> Referências oficiais com passo a passo:
> - Create Custom Fields: https://help.clickup.com/hc/en-us/articles/6303481086487-Create-Custom-Fields
> - Intro to Custom Fields (limites e ativação): https://help.clickup.com/hc/en-us/articles/6303536766231-Intro-to-Custom-Fields
> - Custom Fields uses (detalhes de uso no plano Free): https://help.clickup.com/hc/en-us/articles/10993484102167-Custom-Fields-uses

## Checklist de Campos a Criar (Nomes e Tipos)

Campos recomendados para o fluxo de Atendimento (nomes em português).

- Assunto: Texto — nível List
- Departamento: Lista suspensa — nível Workspace (opções: nomes dos departamentos)
- Etapa: Texto — nível List
- Prioridade: Lista suspensa — nível List (opções: Baixa, Normal, Alta, Urgente)
- Canal: Lista suspensa — nível Workspace (opções: WhatsApp, Email, Telefone, Web)
- Contato: Texto — nível Workspace
- Telefone: Telefone — nível Workspace
- Email: E-mail — nível Workspace
- Início do Atendimento: Data — nível Workspace
- Última Mensagem: Data — nível Workspace
- Fim do Atendimento: Data — nível Workspace
- Nome Perfil WhatsApp: Texto — nível Workspace
- Metadados do Contato: Área de texto — nível Workspace
- Nome Fantasia: Texto — nível Workspace
- Ramo de Atividade: Lista suspensa — nível Workspace
- Observações: Área de texto — nível Workspace
- Metadados do Cliente: Área de texto — nível Workspace
- Atendente: Pessoas — nível Workspace

Observações:

- Dropdown/Label: até 500 opções por campo. Defina as opções de `Canal` e `Prioridade (local)` conforme sua operação.
- Campos nativos do ClickUp como `Assignees`, `Tags` e `Priority` (nativo) devem ser usados quando fizerem sentido; os Custom Fields acima complementam o contexto do card.

## Checklist de Sincronização

- [ ] Lists têm `statuses` coerentes com `EtapaFluxo`.
- [ ] CFs de Workspace anexados às Lists de todos os Departamentos.
- [ ] `field_id` persistidos e versionados.
- [ ] Criação de Task popula: `Canal`, `Contato/Telefone/Email`, `Nome Perfil WhatsApp`, dados de Cliente (`Nome Fantasia`, `Ramo de Atividade`, `Observações`), e `Atendente`.
- [ ] Movimentos atualizam `status` e CFs de datas (Start/End/Last Message).
- [ ] Comentários de mensagens incluem `Intent` e `Entidades` conforme padrão definido.
- [ ] Webhooks refletem mudanças de ClickUp para o sistema interno.

## Tabela de Mapeamento Completa: Campos do Sistema vs Tipos no ClickUp

| Campo do Sistema | Campo Correspondente no ClickUp | Tipo no ClickUp |
|------------------|----------------------------------|-----------------|
| assunto | Subject (Summary) | Texto |
| atendimento_avaliacao | Avaliação | Avaliação |
| atendimento_feedback | Feedback | Área de texto (texto longo) |
| canal | Canal | Lista suspensa |
| cliente.metadados | Metadados do Cliente | Área de texto (texto longo) |
| cliente.nome_fantasia | Nome Fantasia | Texto |
| cliente.observacoes | Observações | Área de texto (texto longo) |
| cliente.ramo_atividade | Ramo de Atividade | Lista suspensa |
| contato.email | Email | E-mail |
| contato.metadados | Metadados do Contato | Área de texto (texto longo) |
| contato.nome | Contato | Texto |
| contato.nome_perfil_whatsapp | Nome Perfil WhatsApp | Texto |
| contato.telefone | Telefone | Telefone |
| data_fim | Fim do Atendimento | Data |
| data_inicio | Início do Atendimento | Data |
| data_ultima_mensagem | Última Mensagem | Data |
| departamento | Department | Lista suspensa |
| fluxo_atendimento | Flow | Texto |
| prioridade | Priority (Local) | Lista suspensa |
| tags | Tags | Rótulos |

## Guia de Criação Manual dos Campos no ClickUp

Siga estas instruções detalhadas para criar manualmente cada campo no ClickUp, conforme o tipo correto mapeado.

### Campos de Texto (Texto)

Para criar campos do tipo **Texto**:
1. Acesse o Custom Field Manager ou a lista desejada
2. Clique em "Create new field"
3. Selecione o tipo "Texto"
4. Configure conforme o campo:
   - **Contato**: Campo para nome do contato
   - **Nome Fantasia**: Nome comercial do cliente
   - **Flow**: Nome do fluxo de atendimento
   - **Subject (Summary)**: Resumo do atendimento
   - **Nome Perfil WhatsApp**: Nome no perfil do WhatsApp

### Campos de Área de Texto (Área de texto)

Para criar campos do tipo **Área de texto**:
1. Acesse o Custom Field Manager ou a lista desejada
2. Clique em "Create new field"
3. Selecione o tipo "Área de texto (texto longo)"
4. Configure conforme o campo:
   - **Metadados do Cliente**: Para informações estruturadas do cliente
   - **Metadados do Contato**: Para informações estruturadas do contato
   - **Observações**: Para notas adicionais do cliente
   - **Feedback**: Para feedback do atendimento

### Campos de Lista Suspensa (Lista suspensa)

Para criar campos do tipo **Lista suspensa**:
1. Acesse o Custom Field Manager ou a lista desejada
2. Clique em "Create new field"
3. Selecione o tipo "Lista suspensa"
4. Configure conforme o campo:
   - **Department**: Adicione cada departamento como uma opção
   - **Canal**: Opções: WhatsApp, Email, Telefone, Web
   - **Priority (Local)**: Opções: Baixa, Normal, Alta, Urgente
   - **Ramo de Atividade**: Adicione os ramos de atividade dos clientes

### Campos de Data (Data)

Para criar campos do tipo **Data**:
1. Acesse o Custom Field Manager ou a lista desejada
2. Clique em "Create new field"
3. Selecione o tipo "Data"
4. Configure conforme o campo:
   - **Início do Atendimento**: Para data de início do atendimento
   - **Última Mensagem**: Para data da última mensagem
   - **Fim do Atendimento**: Para data de conclusão do atendimento

### Campos Específicos

Para campos de tipo específico:
1. **Email** (E-mail):
   - Tipo: E-mail
   - Campo: Email do contato
   
2. **Telefone** (Telefone):
   - Tipo: Telefone
   - Campo: Telefone do contato
   
3. **Pessoas** (Pessoas):
   - Tipo: Pessoas
   - Campo: Atendente responsável
   
4. **Avaliação** (Avaliação):
   - Tipo: Avaliação
   - Campo: Avaliação do atendimento (1-5)
   
5. **Rótulos** (Rótulos):
   - Tipo: Rótulos
   - Campo: Tags do atendimento

## Exemplos de Código para Criar Campos via API do ClickUp

### Exemplo: Criar Campo de Texto Simples

```python
import requests

# Configurações
API_TOKEN = "seu_token_aqui"
WORKSPACE_ID = "id_do_workspace"
LIST_ID = "id_da_lista_opcional"  # Opcional, para campos de nível de lista

# Headers para autenticação
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Criar campo de texto simples
def criar_campo_texto(workspace_id, field_name, list_id=None):
    """Cria um campo de texto simples no ClickUp."""
    url = f"https://api.clickup.com/api/v2/workspace/{workspace_id}/field"
    
    if list_id:
        # Para campos de nível de lista
        url = f"https://api.clickup.com/api/v2/list/{list_id}/field"
    
    data = {
        "name": field_name,
        "type": "text"
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Exemplo de uso
campo_contato = criar_campo_texto(WORKSPACE_ID, "Contato")
print(f"Campo criado: {campo_contato}")
```

### Exemplo: Criar Campo de Lista Suspensa

```python
def criar_campo_lista_suspensa(workspace_id, field_name, options, list_id=None):
    """Cria um campo de lista suspensa no ClickUp."""
    url = f"https://api.clickup.com/api/v2/workspace/{workspace_id}/field"
    
    if list_id:
        # Para campos de nível de lista
        url = f"https://api.clickup.com/api/v2/list/{list_id}/field"
    
    data = {
        "name": field_name,
        "type": "drop_down",
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
campo_canal = criar_campo_lista_suspensa(WORKSPACE_ID, "Canal", opcoes_canal)
print(f"Campo criado: {campo_canal}")
```

### Exemplo: Criar Campo de Área de Texto

```python
def criar_campo_area_texto(workspace_id, field_name, list_id=None):
    """Cria um campo de área de texto no ClickUp."""
    url = f"https://api.clickup.com/api/v2/workspace/{workspace_id}/field"
    
    if list_id:
        # Para campos de nível de lista
        url = f"https://api.clickup.com/api/v2/list/{list_id}/field"
    
    data = {
        "name": field_name,
        "type": "text_area"  # Área de texto (texto longo)
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Exemplo de uso
campo_observacoes = criar_campo_area_texto(WORKSPACE_ID, "Observações")
print(f"Campo criado: {campo_observacoes}")
```

### Exemplo: Criar Campo de Data

```python
def criar_campo_data(workspace_id, field_name, list_id=None):
    """Cria um campo de data no ClickUp."""
    url = f"https://api.clickup.com/api/v2/workspace/{workspace_id}/field"
    
    if list_id:
        # Para campos de nível de lista
        url = f"https://api.clickup.com/api/v2/list/{list_id}/field"
    
    data = {
        "name": field_name,
        "type": "date"
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Exemplo de uso
campo_data_inicio = criar_campo_data(WORKSPACE_ID, "Início do Atendimento")
print(f"Campo criado: {campo_data_inicio}")
```

### Exemplo: Criar Campo de E-mail

```python
def criar_campo_email(workspace_id, field_name, list_id=None):
    """Cria um campo de e-mail no ClickUp."""
    url = f"https://api.clickup.com/api/v2/workspace/{workspace_id}/field"
    
    if list_id:
        # Para campos de nível de lista
        url = f"https://api.clickup.com/api/v2/list/{list_id}/field"
    
    data = {
        "name": field_name,
        "type": "email"
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Exemplo de uso
campo_email = criar_campo_email(WORKSPACE_ID, "Email")
print(f"Campo criado: {campo_email}")
```

### Exemplo: Criar Campo de Telefone

```python
def criar_campo_telefone(workspace_id, field_name, list_id=None):
    """Cria um campo de telefone no ClickUp."""
    url = f"https://api.clickup.com/api/v2/workspace/{workspace_id}/field"
    
    if list_id:
        # Para campos de nível de lista
        url = f"https://api.clickup.com/api/v2/list/{list_id}/field"
    
    data = {
        "name": field_name,
        "type": "phone"
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Exemplo de uso
campo_telefone = criar_campo_telefone(WORKSPACE_ID, "Telefone")
print(f"Campo criado: {campo_telefone}")
```

### Script Completo para Criar Todos os Campos

```python
import requests
import json

# Configurações
API_TOKEN = "seu_token_aqui"
WORKSPACE_ID = "id_do_workspace"

# Headers para autenticação
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def criar_campo(workspace_id, field_name, field_type, type_config=None, list_id=None):
    """Função genérica para criar um campo no ClickUp."""
    url = f"https://api.clickup.com/api/v2/workspace/{workspace_id}/field"
    
    if list_id:
        # Para campos de nível de lista
        url = f"https://api.clickup.com/api/v2/list/{list_id}/field"
    
    data = {
        "name": field_name,
        "type": field_type
    }
    
    if type_config:
        data["type_config"] = type_config
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

def criar_todos_os_campos(workspace_id, list_id=None):
    """Cria todos os campos necessários para o fluxo de atendimento."""
    
    # Campos de texto simples
    campos_texto = [
        ("Contato", "text"),
        ("Nome Fantasia", "text"),
        ("Flow", "text"),
        ("Subject (Summary)", "text"),
        ("Nome Perfil WhatsApp", "text")
    ]
    
    for nome, tipo in campos_texto:
        campo = criar_campo(workspace_id, nome, tipo, list_id=list_id)
        print(f"Campo de texto '{nome}' criado: {campo}")
    
    # Campos de área de texto
    campos_area_texto = [
        ("Metadados do Cliente", "text_area"),
        ("Metadados do Contato", "text_area"),
        ("Observações", "text_area"),
        ("Feedback", "text_area")
    ]
    
    for nome, tipo in campos_area_texto:
        campo = criar_campo(workspace_id, nome, tipo, list_id=list_id)
        print(f"Campo de área de texto '{nome}' criado: {campo}")
    
    # Campos de lista suspensa
    campos_lista_suspensa = [
        ("Department", ["Departamento 1", "Departamento 2", "Departamento 3"]),
        ("Canal", ["WhatsApp", "Email", "Telefone", "Web"]),
        ("Priority (Local)", ["Baixa", "Normal", "Alta", "Urgente"]),
        ("Ramo de Atividade", ["Varejo", "Serviços", "Indústria", "Tecnologia"])
    ]
    
    for nome, opcoes in campos_lista_suspensa:
        type_config = {
            "options": [
                {"name": option, "orderindex": idx} 
                for idx, option in enumerate(opcoes)
            ]
        }
        campo = criar_campo(workspace_id, nome, "drop_down", type_config, list_id)
        print(f"Campo de lista suspensa '{nome}' criado: {campo}")
    
    # Campos de data
    campos_data = [
        ("Início do Atendimento", "date"),
        ("Última Mensagem", "date"),
        ("Fim do Atendimento", "date")
    ]
    
    for nome, tipo in campos_data:
        campo = criar_campo(workspace_id, nome, tipo, list_id=list_id)
        print(f"Campo de data '{nome}' criado: {campo}")
    
    # Campos específicos
    campos_especificos = [
        ("Email", "email"),
        ("Telefone", "phone"),
        ("Atendente", "people"),
        ("Avaliação", "rating"),
        ("Tags", "labels")
    ]
    
    for nome, tipo in campos_especificos:
        campo = criar_campo(workspace_id, nome, tipo, list_id=list_id)
        print(f"Campo específico '{nome}' criado: {campo}")

# Exemplo de uso
criar_todos_os_campos(WORKSPACE_ID)
```

### Estrutura Recomendada

- **Campos de Workspace**: Aplicam a todos os espaços de trabalho
  - Department
  - Canal
  - Contato
  - Telefone
  - Email
  - Início do Atendimento
  - Última Mensagem
  - Fim do Atendimento
  - Nome Perfil WhatsApp
  - Metadados do Contato
  - Nome Fantasia
  - Ramo de Atividade
  - Observações
  - Metadados do Cliente
  - Atendente

- **Campos de List**: Aplicam apenas a listas específicas
  - Subject (Summary)
  - Priority (Local)
  - Flow

---

### Observações Finais

- Priorizar o uso de campos nativos de ClickUp (Status, Assignees, Tags,
  Priority) e suplementar com CFs apenas para contexto adicional.
- Campos derivados do `contato` são críticos para visão 360º do cliente
  no card e devem ser priorizados.
- Onde o `status` legado ainda for necessário, manter conversão interna
  para os `statuses` da List, sem criar CF redundante.

## Mensagens e Comentários (Intent e Entidades)

- Mensagens do atendimento devem ser registradas como comentários na Task.
- Em cada comentário, incluir obrigatoriamente os campos `Intent` e `Entidades`.
- Formatos recomendados:
  - Texto estruturado:
    - Mensagem: "..."
    - Intent: "Atualizar cadastro"
    - Entidades: chave=valor; outra_chave=valor
  - Alternativa em JSON (como bloco de texto no comentário):
    {
      "intent": "Atualizar cadastro",
      "entities": {
        "nome_cliente": "ACME Ltda",
        "novo_endereco": "Rua X, 123"
      }
    }
- Integração via API: postar comentário com `comment_text` contendo a mensagem e os campos `Intent` e `Entidades` ao final.