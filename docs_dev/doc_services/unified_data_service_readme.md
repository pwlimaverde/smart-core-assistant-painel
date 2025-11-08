# UnifiedDataService (UDS)

Este documento descreve a interface genérica `UnifiedDataService` (UDS),
seu fluxo de inicialização via `FeaturesCompose` e como acessar a instância
registrada no `SERVICEHUB`. A implementação de adapter/datasource concreto
para provedores (ex.: Notion) será adicionada posteriormente.

## Objetivo

- Padronizar operações de criação e manipulação de dados em provedores
  externos via uma interface única.
- Desacoplar o código de clientes específicos, suportando `data_source_id`
  e retornos por IDs.

## Estrutura

- `features/unifield_data_services/domain/interface/unified_data_service.py`:
  contrato ABC da interface.
- `utils/types.py`: aliases `UDSData` e `UDSUsecase` usando `UnifiedDataService`.
- `utils/parameters.py`: `UnifieldDataServicesParameters` com campos
  essenciais (`data_source_id`, `provider`, etc.).
- `features/unifield_data_services/domain/usecase/...`: UseCase que retorna
  `UnifiedDataService`.
- `features/features_compose.py`: método `unifield_data_services()` que
  registra a instância no `SERVICEHUB`.
- `features/service_hub.py`: setter/getter `set_unified_data_service` e
  `unified_data_service`.

## Uso

1. Inicialize features existentes (ex.: variáveis de ambiente) e o UDS:

```python
from smart_core_assistant_painel.modules.services.features.features_compose import (
    FeaturesCompose,
)

# Injeta variáveis remotas e recarrega config
FeaturesCompose.set_environ_remote()

# Inicializa o serviço de dados unificado e registra no SERVICEHUB
FeaturesCompose.unifield_data_services()
```

2. Obtenha a instância a partir do `SERVICEHUB`:

```python
from smart_core_assistant_painel.modules.services.features.service_hub import (
    SERVICEHUB,
)

uds = SERVICEHUB.unified_data_service

# Exemplo de chamada (adapter será implementado futuramente)
# container_id = uds.create_container(name="Root")
```

## Parâmetros

`UnifieldDataServicesParameters`:

- `data_source_id: str` — identificador da fonte de dados principal.
- `provider: str = "notion"` — provedor/adaptador alvo (plugável).
- `root_container_name: str = "Unified Data Root"` — nome padrão do
  container raiz.
- `enable_observability: bool = False` — ativa logs mínimos.

## Observações

- O datasource/adapter ainda não foi implementado — este documento cobre
  apenas a estrutura base e contratos. Ao implementar o adapter (ex.:
  `NotionDataSourceAdapter`), as operações da interface serão mapeadas
  para chamadas reais do provedor.

## Testes

- Recomenda-se usar `uv run task test-docker` para executar os testes
  sempre no ambiente Docker.