# Mapeamento de Dados: Django ↔ Trello (com `trello_sync`)

## 1. Visão Geral da Arquitetura

A integração entre a Central de Atendimento e o Trello é baseada em uma arquitetura desacoplada, utilizando um aplicativo intermediário chamado `trello_sync`. Esta abordagem evita modificações nos modelos de dados principais do sistema e centraliza a lógica de sincronização.

O fluxo de dados segue o seguinte padrão:

1.  **Modelos Principais**: `operacional.FluxoAtendimento`, `operacional.EtapaFluxo`, `atendimentos.Atendimento`, `operacional.Atendente`.
2.  **Camada de Sincronização (Signals)**: Django Signals (`post_save`) monitoram alterações nos modelos principais.
3.  **Modelos de Mapeamento (`trello_sync`)**: `TrelloBoard`, `TrelloList`, `TrelloCard`, `TrelloMember`. Estes modelos estabelecem uma relação `OneToOne` com os modelos principais e armazenam os IDs do Trello.
4.  **API do Trello**: Os serviços de sincronização interagem com a API do Trello para criar, atualizar e ler os objetos correspondentes (Boards, Lists, Cards, Members).

![Arquitetura de Mapeamento](https://i.imgur.com/diagram.png) <!-- Placeholder para um diagrama futuro -->

## 2. Mapeamento Detalhado de Entidades

| Modelo Principal (Fonte) | Relacionamento | Modelo de Mapeamento (`trello_sync`) | Objeto Trello (Destino) | Cardinalidade | Dono da Criação |
| :--- | :---: | :--- | :--- | :---: | :--- |
| `operacional.FluxoAtendimento` | `OneToOne` | `trello_sync.TrelloBoard` | **Board** | 1:1 | Django |
| `operacional.EtapaFluxo` | `OneToOne` | `trello_sync.TrelloList` | **List** | 1:1 | Django |
| `atendimentos.Atendimento` | `OneToOne` | `trello_sync.TrelloCard` | **Card** | 1:1 | Django |
| `operacional.Atendente` | `OneToOne` | `trello_sync.TrelloMember` | **Member** | 1:1 | Django |

### 2.1. FluxoAtendimento ↔ TrelloBoard ↔ Board

-   **Gatilho**: Criação de uma nova instância de `FluxoAtendimento`.
-   **Ação**: Um signal `post_save` dispara um serviço que:
    1.  Cria um novo Board no Trello via API.
    2.  Cria uma instância de `TrelloBoard` no app `trello_sync`, armazenando o `trello_board_id` retornado pela API e a chave estrangeira para o `FluxoAtendimento`.
    3.  Registra um Webhook no Trello para monitorar eventos neste Board.

### 2.2. EtapaFluxo ↔ TrelloList ↔ List

-   **Gatilho**: Criação de uma nova instância de `EtapaFluxo`.
-   **Ação**: Um signal `post_save` dispara um serviço que:
    1.  Busca o `TrelloBoard` correspondente ao `FluxoAtendimento` da etapa.
    2.  Cria uma nova List (coluna) no Board do Trello via API.
    3.  Cria uma instância de `TrelloList`, armazenando o `trello_list_id` e a chave estrangeira para a `EtapaFluxo`.

### 2.3. Atendimento ↔ TrelloCard ↔ Card

-   **Gatilho**: Criação de uma nova instância de `Atendimento`.
-   **Ação**: Um signal `post_save` dispara um serviço que:
    1.  Identifica a `EtapaFluxo` inicial do `Atendimento`.
    2.  Busca a `TrelloList` correspondente a essa etapa.
    3.  Cria um novo Card na List do Trello via API.
    4.  Cria uma instância de `TrelloCard`, armazenando o `trello_card_id` e a chave estrangeira para o `Atendimento`.

### 2.4. Atendente ↔ TrelloMember ↔ Member

-   **Gatilho**: Criação de uma nova instância de `Atendente`.
-   **Ação**: Um signal `post_save` dispara um serviço que:
    1.  Verifica se o usuário já existe como membro no Trello (usando o e-mail).
    2.  Se não existir, convida o usuário para o Board principal da organização no Trello.
    3.  Cria uma instância de `TrelloMember`, armazenando o `trello_member_id` e a chave estrangeira para o `Atendente`.

## 3. Estratégia de Sincronização

-   **Fonte da Verdade (Estrutura)**: O Django é a fonte da verdade para a **estrutura** do fluxo (quais Boards e Lists existem e suas configurações).
-   **Fonte da Verdade (Estado Operacional)**: O Trello é a fonte da verdade para o **estado operacional** dos atendimentos (em qual List um Card está, quem são os membros, comentários, etc.).
-   **Sincronização Django → Trello**: Ocorre via API, acionada por Django Signals, para criar a estrutura inicial (Boards, Lists) e os Cards.
-   **Sincronização Trello → Django**: Ocorre via **Webhooks**. Eventos no Trello (movimentação de cards, adição de comentários, etc.) enviam uma notificação para um endpoint dedicado no Django. O serviço de webhook então processa a notificação, busca o registro correspondente no app `trello_sync` (usando o ID do card, lista ou board) e atualiza o estado do `Atendimento` no banco de dados principal.