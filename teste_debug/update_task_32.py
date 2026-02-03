"""
Script para atualizar a Task 32 no TaskMaster.
Executa de forma segura, lendo o JSON, modificando e salvando.
"""

import json
from pathlib import Path

TASKS_FILE = Path(
    r"c:\PROJETOS\PYTHON\APPS\smart-core-assistant-painel\.taskmaster\tasks\tasks.json"
)

NEW_TASK_32 = {
    "id": 32,
    "title": "[REFACTOR] Arquitetura de Configuração SaaS Multi-Tenant",
    "description": "Implementar nova arquitetura de configuração usando ContextVar para injeção dinâmica, modelo CoreSettings para configs globais, e ConfigProvider desacoplado do Django para módulos puros Python.",
    "details": """## Contexto e Motivação
O sistema atual carrega configs do Firebase Remote Config via variáveis de ambiente. Na arquitetura SaaS multi-tenant, cada requisição pode ter um tenant diferente, impossibilitando o uso de env vars. A nova arquitetura usa:

1. **ContextVar** - variável de contexto nativa do Python que isola configs por requisição
2. **ConfigProvider** - interface pura Python que módulos usam para acessar configs
3. **ConfigLoader** - adaptador Django que carrega do banco e injeta no contexto
4. **CoreSettings** - modelo key-value para configs globais editáveis via Admin

## Decisões Arquiteturais
- API Keys: compartilhadas entre todos tenants
- Prompts do Sistema: globais e fixos
- Storage: banco de dados editável via Django Admin

## Componentes a Criar
1. App settings_manager com modelo CoreSettings
2. Módulo modules/services/config/ com ContextVar e ConfigProvider
3. ConfigLoader em app/tenants/services/
4. TenantConfigMiddleware
5. Script de carga com valores do Firebase
6. Refatoração do ServiceHub
7. Remoção do set_environ_remote""",
    "testStrategy": "1. CoreSettings CRUD via Admin\n2. ContextVar isola configs entre requisições\n3. ConfigProvider retorna valores do contexto\n4. ServiceHub funciona com nova arquitetura\n5. Aplicação inicia sem Firebase Remote Config",
    "status": "pending",
    "dependencies": ["31"],
    "priority": "high",
    "subtasks": [
        {
            "id": 1,
            "title": "Criar App settings_manager e Modelo CoreSettings",
            "description": "Criar novo app Django para gerenciamento de configurações globais com modelo key-value.",
            "details": "Estrutura: app/settings_manager/ com models.py (CoreSettings), admin.py, management/commands/load_core_settings.py. Modelo CoreSettings: key (PK), value (TextField), encrypted (bool), description. Métodos: get_value(key), get_all().",
            "status": "pending",
            "dependencies": [],
            "parentTaskId": 32,
            "testStrategy": "makemigrations sem erros, CRUD via Admin, get_value retorna valor correto",
        },
        {
            "id": 2,
            "title": "Criar Módulo Config com ContextVar e RuntimeConfig",
            "description": "Criar módulo puro Python em modules/services/config/ com ContextVar para isolamento de contexto e dataclass RuntimeConfig.",
            "details": "Arquivos: context.py (ContextVar, set_config, get_config), types.py (RuntimeConfig dataclass frozen=True com todos atributos de config). IMPORTANTE: Este módulo NÃO importa Django.",
            "status": "pending",
            "dependencies": [],
            "parentTaskId": 32,
            "testStrategy": "RuntimeConfig é frozen, set/get_config isolam valores por contexto, módulo não importa Django",
        },
        {
            "id": 3,
            "title": "Implementar ConfigProvider",
            "description": "Criar interface estática que módulos usam para acessar configurações de forma desacoplada.",
            "details": "Arquivo: modules/services/config/provider.py. Métodos estáticos: get() -> RuntimeConfig, groq_api_key(), openai_api_key(), model(), llm_class(), prompt(name).",
            "status": "pending",
            "dependencies": [2],
            "parentTaskId": 32,
            "testStrategy": "ConfigProvider.get() retorna RuntimeConfig do contexto, atalhos retornam valores corretos",
        },
        {
            "id": 4,
            "title": "Implementar ConfigLoader no Layer Django",
            "description": "Criar serviço que carrega configs do banco (CoreSettings + TenantConfig) e injeta no ContextVar.",
            "details": "Arquivo: app/tenants/services/config_loader.py. Métodos: load_for_request(tenant), _get_core_settings() com cache TTL 5min, _get_tenant_config(tenant). Regras de merge: API Keys sempre Core, Prompts sistema sempre Core, Prompts tenant do TenantConfig.",
            "status": "pending",
            "dependencies": [1, 2, 3],
            "parentTaskId": 32,
            "testStrategy": "Cache funciona, merge prioriza tenant sobre core, load_for_request cria RuntimeConfig correto",
        },
        {
            "id": 5,
            "title": "Implementar TenantConfigMiddleware",
            "description": "Criar middleware Django que injeta configuração no contexto de cada requisição.",
            "details": "Arquivo: app/tenants/middleware.py. Posicionar após TenantMiddleware. Chama ConfigLoader.load_for_request(request.tenant). Atualizar settings.py MIDDLEWARE.",
            "status": "pending",
            "dependencies": [4],
            "parentTaskId": 32,
            "testStrategy": "Cada requisição tem config injetada, diferentes tenants têm configs diferentes",
        },
        {
            "id": 6,
            "title": "Criar Script de Carga e Migrar Dados do Firebase",
            "description": "Criar management command que extrai valores atuais do Firebase Remote Config e salva no CoreSettings.",
            "details": "Arquivo: app/settings_manager/management/commands/load_core_settings.py. Etapas: 1) Definir mapeamento de configs (API Keys encrypted, LLM, Prompts, Embeddings, Thresholds), 2) Carregar FeaturesCompose.set_environ_remote() para popular env vars, 3) Para cada config, obter valor da env var e salvar no CoreSettings.",
            "status": "pending",
            "dependencies": [1],
            "parentTaskId": 32,
            "testStrategy": "Comando executa sem erros, CoreSettings populado com valores do Firebase",
        },
        {
            "id": 7,
            "title": "Refatorar ServiceHub para usar ConfigProvider",
            "description": "Modificar ServiceHub para delegar propriedades ao ConfigProvider, mantendo interface compatível.",
            "details": "Arquivo: modules/services/features/service_hub.py. Mudar propriedades para usar ConfigProvider: MODEL -> ConfigProvider.model(), LLM_CLASS -> ConfigProvider.llm_class(), etc. Remover atributos _cache, _load_config(), reload_config().",
            "status": "pending",
            "dependencies": [3],
            "parentTaskId": 32,
            "testStrategy": "SERVICEHUB.MODEL retorna valor do contexto, código existente continua funcionando",
        },
        {
            "id": 8,
            "title": "Remover Firebase Remote Config e Limpar Código",
            "description": "Remover módulo set_environ_remote e referências, limpar código legado.",
            "details": "Remover: modules/services/features/set_environ_remote/. Modificar: features_compose.py (remover set_environ_remote), start_services.py (remover chamada), utils/parameters.py e types.py (remover SetEnvironRemote*), utils/erros.py (remover SetEnvironRemoteError).",
            "status": "pending",
            "dependencies": [5, 6, 7],
            "parentTaskId": 32,
            "testStrategy": "Aplicação inicia sem erros, não há imports quebrados, nenhuma referência a set_environ_remote",
        },
    ],
    "updatedAt": "2025-12-09T23:53:00.000Z",
}


def main():
    # Ler o arquivo
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Encontrar e substituir Task 32
    tasks = data["master"]["tasks"]
    task_32_idx = None

    for i, task in enumerate(tasks):
        if task.get("id") == 32:
            task_32_idx = i
            break

    if task_32_idx is not None:
        # Substituir task existente
        tasks[task_32_idx] = NEW_TASK_32
        print(f"Task 32 atualizada no índice {task_32_idx}")
    else:
        # Inserir após task 31
        task_31_idx = None
        for i, task in enumerate(tasks):
            if task.get("id") == 31:
                task_31_idx = i
                break

        if task_31_idx is not None:
            tasks.insert(task_31_idx + 1, NEW_TASK_32)
            print(f"Task 32 inserida após índice {task_31_idx}")
        else:
            tasks.append(NEW_TASK_32)
            print("Task 32 adicionada ao final")

    # Salvar
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Arquivo salvo com sucesso!")


if __name__ == "__main__":
    main()
