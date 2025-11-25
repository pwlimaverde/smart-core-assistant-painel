# Modelos de Dados para o App `trello_sync`

## 1. Introdução

Seguindo a diretriz de não alterar o banco de dados principal, a integração com o Trello será gerenciada por um novo aplicativo Django chamado `trello_sync`. Este aplicativo conterá seus próprios modelos, que servirão como uma "camada espelho" para armazenar os identificadores (IDs) e outras informações relevantes do Trello.

A sincronização entre os modelos do sistema principal e os modelos do `trello_sync` será orquestrada por meio de **Django Signals**. Cada vez que um objeto relevante (como `Atendimento` ou `FluxoAtendimento`) for criado ou atualizado, um sinal `post_save` irá disparar a criação ou atualização do registro correspondente no `trello_sync`.

Esta arquitetura promove um baixo acoplamento, isola a lógica de integração e preserva a integridade do esquema de banco de dados existente.

## 2. Estrutura dos Modelos em `trello_sync`

Os modelos abaixo serão criados em `src/smart_core_assistant_painel/app/trello_sync/models.py`.

### 2.1. Modelo `TrelloBoard`

Este modelo mapeia um `FluxoAtendimento` a um Board no Trello.

```python
from django.db import models
from smart_core_assistant_painel.app.operacional.models import FluxoAtendimento

class TrelloBoard(models.Model):
    """
    Espelha um FluxoAtendimento para o Trello, representando-o como um Board.
    """
    fluxo_atendimento = models.OneToOneField(
        FluxoAtendimento,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="trello_board"
    )
    trello_board_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="ID do Board no Trello"
    )
    trello_webhook_id = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        help_text="ID do Webhook criado para este Board no Trello"
    )

    def __str__(self):
        return f"Board: {self.fluxo_atendimento.nome}"
```

### 2.2. Modelo `TrelloList`

Mapeia uma `EtapaFluxo` a uma List (coluna) em um Board do Trello.

```python
from django.db import models
from smart_core_assistant_painel.app.operacional.models import EtapaFluxo

class TrelloList(models.Model):
    """
    Espelha uma EtapaFluxo para o Trello, representando-a como uma List.
    """
    etapa_fluxo = models.OneToOneField(
        EtapaFluxo,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="trello_list"
    )
    trello_list_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="ID da List no Trello"
    )

    def __str__(self):
        return f"List: {self.etapa_fluxo.nome}"
```

### 2.3. Modelo `TrelloCard`

Mapeia um `Atendimento` a um Card em uma List do Trello.

```python
from django.db import models
from smart_core_assistant_painel.app.atendimentos.models import Atendimento

class TrelloCard(models.Model):
    """
    Espelha um Atendimento para o Trello, representando-o como um Card.
    """
    atendimento = models.OneToOneField(
        Atendimento,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="trello_card"
    )
    trello_card_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="ID do Card no Trello"
    )

    def __str__(self):
        return f"Card: {self.atendimento.id}"
```

### 2.4. Modelo `TrelloMember`

Mapeia um `Atendente` a um Member (membro) no Trello.

```python
from django.db import models
from smart_core_assistant_painel.app.operacional.models import Atendente

class TrelloMember(models.Model):
    """
    Espelha um Atendente para o Trello, representando-o como um Member.
    """
    atendente = models.OneToOneField(
        Atendente,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="trello_member"
    )
    trello_member_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="ID do Member no Trello"
    )

    def __str__(self):
        return f"Member: {self.atendente.nome_atendente}"
```

## 3. Próximos Passos

1.  **Criar o App**: Executar `python manage.py startapp trello_sync` dentro do diretório `src/smart_core_assistant_painel/app/`.
2.  **Definir os Modelos**: Adicionar o código acima ao arquivo `trello_sync/models.py`.
3.  **Implementar os Signals**: Criar um arquivo `trello_sync/signals.py` e implementar os receivers `post_save` para os modelos `FluxoAtendimento`, `EtapaFluxo`, `Atendimento` e `Atendente`.
4.  **Registrar os Signals**: Importar e registrar os signals no método `ready()` da configuração do app em `trello_sync/apps.py`.
5.  **Gerar e Aplicar Migrations**: Executar `uv run task makemigrations trello_sync` e `uv run task migrate`.