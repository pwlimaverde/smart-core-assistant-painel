# Sincronização de Exclusão com ClickUp

## Overview

Este documento descreve as funcionalidades implementadas para garantir que, quando um dado for excluído no painel, ele também seja removido permanentemente do ClickUp.

## Problema Resolvido

Anteriormente, ao excluir dados no painel, os mesmos não eram refletidos no ClickUp:
- **FluxoAtendimento**: apenas era arquivado, não excluído permanentemente
- **Atendimento**: não havia sincronização de exclusão
- **Atendente**: método de remoção era um no-op (não fazia nada)
- **Departamento**: não havia sincronização de exclusão
- **EtapaFluxo**: apenas reconfigurava statuses, mas não removia da API

## Solução Implementada

### 1. Novos Métodos no Adapter do ClickUp

Foram adicionados métodos de exclusão no `ClicupUnifiedDataService`:

- `delete_item(item_id: str) -> bool`: Exclui uma task
- `delete_list(list_id: str) -> bool`: Exclui uma lista  
- `delete_folder(folder_id: str) -> bool`: Exclui uma pasta
- `remove_member(member_id: str) -> bool`: Remove um membro do workspace

### 2. Atualização dos Serviços de Sincronização

#### FlowSyncService
- Novo método `delete_list_for_fluxo(fluxo_id: int)`: Remove permanentemente a lista do ClickUp e o registro local

#### TicketSyncService  
- Novo método `delete_task(atendimento_id: int) -> bool`: Remove permanentemente a task do ClickUp e o registro local

#### MemberSyncService
- Refatorado para incluir o adapter do ClickUp
- Novo método `remove_member(atendente_id: int) -> bool`: Remove o membro do ClickUp (se não for local) e o registro local

#### DepartmentProvisionService
- Novo método `delete_on_department_delete(departamento: Any)`: Remove o folder e o registro local do space

### 3. Novas Tasks Assíncronas

- `task_fluxo_delete_list(fluxo_id: int)`: Executa a exclusão da lista
- `task_atendimento_delete_task(atendimento_id: int)`: Executa a exclusão da task
- `task_atendente_remove_member(atendente_id: int)`: Executa a remoção do membro (agora funcional)
- `task_departamento_delete_folder(departamento_id: int)`: Executa a exclusão do folder

### 4. Atualização dos Signals

Todos os sinais `pre_delete` foram atualizados para chamar as novas tasks de exclusão:

```python
@receiver(pre_delete, sender=FluxoAtendimento)
def fluxo_deleted_delete_clickup(sender, instance, **kwargs):
    """Exclui permanentemente a List ClickUp ao excluir um FluxoAtendimento (assíncrono)."""
    # Chama task_fluxo_delete_list

@receiver(pre_delete, sender=Atendimento)  
def atendimento_deleted_delete_task_clickup(sender, instance, **kwargs):
    """Exclui permanentemente a Task ClickUp ao excluir um Atendimento (assíncrono)."""
    # Chama task_atendimento_delete_task

@receiver(pre_delete, sender=Atendente)
def atendente_deleted_remove_member_clickup(sender, instance, **kwargs):
    """Remove membro do ClickUp ao excluir Atendente (assíncrono)."""
    # Chama task_atendente_remove_member

@receiver(pre_delete, sender=Departamento)
def departamento_deleted_delete_folder_clickup(sender, instance, **kwargs):
    """Exclui permanentemente o Folder ClickUp ao excluir um Departamento (assíncrono)."""
    # Chama task_departamento_delete_folder
```

## Fluxo de Exclusão

1. **Signal Disparado**: Quando um modelo é excluído no Django
2. **Task Enfileirada**: Django Q enfileira a task assíncrona correspondente
3. **Execução da Task**: A task é executada em background
4. **Remoção Local**: Primeiro remove o registro do banco local
5. **Remoção Remota**: Depois exclui o recurso do ClickUp API
6. **Log**: Registra sucesso ou falha da operação

## Tratamento de Erros

- Todas as operações de exclusão retornam `bool` indicando sucesso/falha
- Logs detalhados são gerados para debug
- Falhas na API do ClickUp não impedem a remoção do registro local
- Operações são idempotentes (executar múltiplas vezes não causa problemas)

## Casos Especiais

### Membros Locais
Se um atendente tiver `external_id` começando com "local-", apenas o registro local é removido (não há necessidade de remover do ClickUp).

### Hierarquia de Exclusão
A exclusão segue a ordem correta para evitar violações de dependência:
1. Tasks (Atendimentos) → Lists (Fluxos) → Folders (Departamentos)

## Testes

Foram criados testes unitários abrangentes em `tests/modules/app/clickup_sync/test_deletion_sync.py`:

- Testes de tasks assíncronas
- Testes de serviços de sincronização  
- Testes de signals
- Testes do adapter do ClickUp
- Testes com mocks para simular API

## Uso

A sincronização de exclusão é automática e transparente para o usuário. Não é necessária nenhuma configuração adicional.

### Para Executar Manualmente (se necessário):

```python
# Excluir lista de fluxo
from smart_core_assistant_painel.app.clickup_sync.services import FlowSyncService
service = FlowSyncService()
service.delete_list_for_fluxo(fluxo_id)

# Excluir task de atendimento  
from smart_core_assistant_painel.app.clickup_sync.services import TicketSyncService
service = TicketSyncService()
service.delete_task(atendimento_id)

# Remover membro
from smart_core_assistant_painel.app.clickup_sync.services import MemberSyncService
service = MemberSyncService()
service.remove_member(atendente_id)

# Excluir folder de departamento
from smart_core_assistant_painel.app.clickup_sync.services import DepartmentProvisionService
service = DepartmentProvisionService()
service.delete_on_department_delete(departamento)
```

## Considerações de Performance

- Operações são assíncronas (não bloqueiam o request principal)
- Logs são otimizados para não impactar performance
- Remoção local sempre ocorre, mesmo se API do ClickUp falhar

## Segurança

- Validações de existência de registros antes da exclusão
- Tokens de API não são expostos nos logs
- Operações respeitam permissões do usuário no Django