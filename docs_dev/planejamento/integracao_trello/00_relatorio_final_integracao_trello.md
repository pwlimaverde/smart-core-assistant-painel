# Relatório Final: Estratégia de Integração com Trello via `trello_sync`

## 1. Resumo Executivo

Este relatório consolida a estratégia de integração da Central de Atendimento com o Trello, adotando uma arquitetura desacoplada para atender ao requisito de **não alterar o banco de dados existente**. A solução se baseia na criação de um novo aplicativo Django, `trello_sync`, que funcionará como uma camada intermediária, orquestrando a sincronização de dados de forma segura e organizada.

O `trello_sync` utilizará **Django Signals** para capturar eventos de criação e atualização nos modelos principais (como `Atendimento` e `FluxoAtendimento`) e traduzi-los em chamadas para a API do Trello. No sentido inverso, **Webhooks** configurados no Trello notificarão o `trello_sync` sobre interações dos usuários (como mover um card), que então atualizará o estado correspondente no sistema principal.

Essa abordagem preserva a integridade do esquema de banco de dados atual, aumenta a manutenibilidade e isola a lógica de integração, facilitando futuras atualizações.

## 2. Análise do Escopo e Decisão Arquitetural

-   **Requisito Mandatório**: Não modificar as tabelas do banco de dados principal.
-   **Decisão**: Criar um novo aplicativo Django (`trello_sync`) para abrigar os modelos e a lógica de sincronização.
-   **Justificativa**: A criação de um app dedicado oferece um baixo acoplamento, permitindo que a integração com o Trello seja desenvolvida, mantida e até mesmo desativada sem impactar o núcleo do sistema. Ele atua como um *sidecar* do banco de dados, estendendo a funcionalidade sem alterá-lo.

## 3. Estratégia de Integração Proposta

-   **Direção**: Bidirecional e orientada a eventos.
-   **Django → Trello**: A criação de fluxos, etapas e atendimentos no Django dispara `post_save` signals. O `trello_sync` intercepta esses sinais e, através de serviços de sincronização, cria os respectivos Boards, Lists e Cards no Trello via API.
-   **Trello → Django**: Ações no Trello (mover card, adicionar membro) disparam webhooks. Um endpoint no `trello_sync` recebe, valida e processa esses eventos, atualizando os modelos do sistema principal (`Atendimento`, `MovimentoFluxo`, etc.).

## 4. Mapeamento de Dados

O mapeamento conceitual permanece, mas a implementação é intermediada pelos modelos do `trello_sync`:

-   `FluxoAtendimento` (1) → (1) `TrelloBoard` (1) → (1) Trello Board
-   `EtapaFluxo` (1) → (1) `TrelloList` (1) → (1) Trello List
-   `Atendimento` (1) → (1) `TrelloCard` (1) → (1) Trello Card
-   `Atendente` (1) → (1) `TrelloMember` (1) → (1) Trello Member

## 5. Modelos de Dados (App `trello_sync`)

O `trello_sync` conterá os seguintes modelos para armazenar os IDs do Trello e estabelecer a ligação com os modelos principais:

-   **`TrelloBoard`**: `OneToOneField` com `FluxoAtendimento`, armazena `trello_board_id` e `trello_webhook_id`.
-   **`TrelloList`**: `OneToOneField` com `EtapaFluxo`, armazena `trello_list_id`.
-   **`TrelloCard`**: `OneToOneField` com `Atendimento`, armazena `trello_card_id`.
-   **`TrelloMember`**: `OneToOneField` com `Atendente`, armazena `trello_member_id`.

## 6. Próximos Passos

Com o planejamento e a arquitetura definidos e documentados, os próximos passos se concentram na implementação:

1.  **Criação do App**: Estruturar o aplicativo `trello_sync` com seus modelos, serviços e listeners de signals.
2.  **Desenvolvimento dos Serviços**: Implementar a lógica nos serviços `FlowSyncService`, `TicketSyncService` e `WebhookProcessingService`.
3.  **Criação do Endpoint**: Desenvolver a view para receber e validar os webhooks do Trello.
4.  **Testes**: Criar testes unitários e de integração para garantir a robustez da sincronização.
5.  **Documentação Técnica**: Detalhar a configuração e o uso do novo aplicativo no `README.md` do projeto.