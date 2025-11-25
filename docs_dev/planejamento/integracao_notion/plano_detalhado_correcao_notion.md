# 🛠️ Guia de Implementação Detalhado (v2): Correção da Integração Notion

Este documento é um guia técnico passo a passo para corrigir os problemas de sincronização e visualização na integração com o Notion. Cada passo inclui o arquivo a ser modificado e os blocos de código exatos.

---

## **Fase 1: Corrigir a Sincronização de Mensagens e Relações (Prioridade Máxima)**

**Objetivo**: Garantir que tanto as **Mensagens** quanto os **Atendimentos** sejam salvos como páginas com as relações corretas. Esta é a base para os rollups funcionarem.

### **Passo 1.1: Ajustar o Modelo `MensagemSync`**

**Arquivo**: `src/smart_core_assistant_painel/app/notion_sync/models.py`

**Ação**: Altere o método `prepare_notion_data` no modelo `MensagemSync` para que ele chame o `to_notion_properties` em vez do `to_notion_block`.

**DEPOIS**:
```python
# C:\PROJETOS\PYTHON\APPS\smart-core-assistant-painel\src\smart_core_assistant_painel\app\notion_sync\models.py

class MensagemSync(models.Model):
    # ... (outros campos)
    def prepare_notion_data(self) -> None:
        """Prepara e formata os dados para sincronização com Notion."""
        try:
            from .services.mappers.mensagem_mapper import MensagemMapper
            # ✅ Agora, preparamos as propriedades para criar uma PÁGINA na database de Mensagens
            self.notion_properties = MensagemMapper.to_notion_properties(self)

            # ... (restante do método)
```

### **Passo 1.2: Criar o Novo `MensagemMapper`**

**Arquivo**: `src/smart_core_assistant_painel/app/notion_sync/services/mappers/mensagem_mapper.py`

**Ação**: Substitua o conteúdo deste arquivo pela implementação abaixo. Ela transforma uma mensagem em propriedades de uma página do Notion, incluindo a relação com o atendimento.

**NOVO CÓDIGO COMPLETO**:
```python
# C:\PROJETOS\PYTHON\APPS\smart-core-assistant-painel\src\smart_core_assistant_painel\app\notion_sync\services\mappers\mensagem_mapper.py

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from smart_core_assistant_painel.app.notion_sync.models import MensagemSync

class MensagemMapper:
    @staticmethod
    def to_notion_properties(sync_instance: "MensagemSync") -> dict:
        mensagem = sync_instance.mensagem
        properties = {}
        conteudo_texto = mensagem.conteudo or "(Mensagem sem texto)"
        properties["Conteúdo"] = {"title": [{"text": {"content": conteudo_texto[:2000]}}]}

        if sync_instance.atendimento_sync and sync_instance.atendimento_sync.external_id:
            properties["Atendimento Relacionado"] = {
                "relation": [{"id": sync_instance.atendimento_sync.external_id}]
            }

        if mensagem.tipo:
            properties["Tipo"] = {"select": {"name": mensagem.tipo}}
        if mensagem.remetente:
            properties["Remetente"] = {"select": {"name": mensagem.remetente}}
        if mensagem.timestamp:
            properties["Timestamp"] = {"date": {"start": mensagem.timestamp.isoformat()}}

        return properties
```

### **Passo 1.3: Ajustar o `AtendimentoMapper` para Enviar Relações**

**Arquivo**: `src/smart_core_assistant_painel/app/notion_sync/services/mappers/atendimento_mapper.py`

**Ação**: Adicione a lógica para incluir os IDs das relações com Contato, Atendente e Departamento ao criar ou atualizar um atendimento. **Isso é crucial para que os rollups funcionem.**

**CÓDIGO SUGERIDO**:
```python
# C:\PROJETOS\PYTHON\APPS\smart-core-assistant-painel\src\smart_core_assistant_painel\app\notion_sync\services\mappers\atendimento_mapper.py

# (importações necessárias)

class AtendimentoMapper:
    @staticmethod
    def to_notion_properties(sync_instance: "AtendimentoSync") -> dict:
        atendimento = sync_instance.atendimento
        properties = {
            "Protocolo": {"title": [{"text": {"content": atendimento.protocolo}}]},
            "Status": {"select": {"name": atendimento.status}},
            # ... outras propriedades básicas
        }

        # ✅ ADICIONAR RELAÇÕES (ESSENCIAL)
        if sync_instance.contato_sync and sync_instance.contato_sync.external_id:
            properties["Contato"] = {"relation": [{"id": sync_instance.contato_sync.external_id}]}

        if sync_instance.atendente_sync and sync_instance.atendente_sync.external_id:
            properties["Atendente"] = {"relation": [{"id": sync_instance.atendente_sync.external_id}]}

        if sync_instance.departamento_sync and sync_instance.departamento_sync.external_id:
            properties["Departamento"] = {"relation": [{"id": sync_instance.departamento_sync.external_id}]}

        return properties
```

### **Passo 1.4: Ajustar o Serviço de Sincronização para Mensagens**

**Arquivo**: `src/smart_core_assistant_painel/app/notion_sync/services/notion_service.py`

**Ação**: Altere a lógica de sincronização de mensagens para criar uma **página** em vez de anexar um **bloco**.

**LÓGICA CONCEITUAL (DEPOIS)**:
```python
# Nova lógica, que cria uma página
if model_name == "Mensagem":
    mensagens_config = NotionDatabaseConfig.objects.get(slug="ui_atendimentos_mensagem")
    mensagens_data_source_id = mensagens_config.data_source_id

    page_data = {
        "parent": {"type": "data_source_id", "data_source_id": str(mensagens_data_source_id)},
        "properties": notion_properties_data, # Dados do MensagemMapper.to_notion_properties
    }
    created_page = await self.client.pages.create(**page_data)
    return created_page.id
```

---

## **Fase 2: Implementar Rollups e Fórmulas no Notion**

**Objetivo**: Fazer com que o script de construção já crie a database de "Atendimentos" com todos os `rollups` sugeridos no diagnóstico, enriquecendo a visualização de dados.

### **Passo 2.1: Adicionar Rollups Completos ao Script de Construção**

**Arquivo**: `src/smart_core_assistant_painel/app/notion_sync/scripts/script_constructor_notion.py`

**Ação**: Na classe `NotionAtendimentosDatabaseConstructor`, localize o dicionário `update_atendimento` e adicione a lista completa de `rollups`.

**DEPOIS (Bloco `properties` completo)**:
```python
# C:\PROJETOS\PYTHON\APPS\smart-core-assistant-painel\src\smart_core_assistant_painel\app\notion_sync\scripts\script_constructor_notion.py

        update_atendimento = {
            "properties": {
                # --- Relações ---
                "Contato": {"relation": {"data_source_id": contato_ds_id, "single_property": {}, "dual_property": {"synced_property_name": "Atendimentos Relacionados"}}},
                "Atendente": {"relation": {"data_source_id": atendente_ds_id, "single_property": {}, "dual_property": {"synced_property_name": "Atendimentos Relacionados"}}},
                "Mensagens Relacionadas": {"relation": {"data_source_id": mensagem_ds_id, "dual_property": {"synced_property_name": "Atendimento Relacionado"}}},

                # --- Rollups do Contato/Cliente ---
                "Nome Contato": {"rollup": {"relation_property_name": "Contato", "rollup_property_name": "Nome Contato", "function": "show_original"}},
                "Telefone Contato": {"rollup": {"relation_property_name": "Contato", "rollup_property_name": "Telefone", "function": "show_original"}},
                "Nome Cliente": {"rollup": {"relation_property_name": "Contato", "rollup_property_name": "Nome Cliente (do Contato)", "function": "show_original"}}, # Supondo que o rollup já exista em Contatos

                # --- Rollups do Atendente ---
                "Nome Atendente": {"rollup": {"relation_property_name": "Atendente", "rollup_property_name": "Nome", "function": "show_original"}},

                # --- Rollups de Mensagens ---
                "Total Mensagens": {"rollup": {"relation_property_name": "Mensagens Relacionadas", "rollup_property_name": "Conteúdo", "function": "count"}},
                "Última Mensagem Recebida": {"rollup": {"relation_property_name": "Mensagens Relacionadas", "rollup_property_name": "Timestamp", "function": "latest_date"}},
                "Preview Última Mensagem": {"rollup": {"relation_property_name": "Mensagens Relacionadas", "rollup_property_name": "Conteúdo", "function": "show_original"}},

                # --- Fórmulas ---
                "Indicador Visual": {"formula": {"expression": "if(prop(\"Prioridade\") == \"Urgente\", \"🔥\", if(prop(\"Total Mensagens\") > 10, \"⚡\", \"💬\"))"}}
            }
        }
```
**Nota**: Lembre-se de atualizar também o schema salvo no banco de dados Django no método `save_database_configs` do mesmo script para refletir estas novas propriedades.

---

## **Fase 3: Finalizar a Compatibilidade com a API 2025-09-03**

**Objetivo**: Garantir que toda a aplicação use os padrões mais recentes da API do Notion.

### **Passo 3.1: Configurar a Versão da API no Cliente**

**Arquivo**: `src/smart_core_assistant_painel/app/notion_sync/services/notion_service.py`

**Ação**: Garanta que o cliente Notion seja inicializado com a versão correta da API.

**DEPOIS**:
```python
# C:\PROJETOS\PYTHON\APPS\smart-core-assistant-painel\src\smart_core_assistant_painel\app\notion_sync\services\notion_service.py

self.client = NotionAsyncClient(
    auth=self.token,
    notion_version="2025-09-03"  # ✅ Garanta que esta linha exista
)
```

### **Passo 3.2: Usar `data_source_id` para Criar Páginas**

**Arquivo**: `src/smart_core_assistant_painel/app/notion_sync/services/notion_service.py`

**Ação**: Em todos os locais onde uma nova página é criada (`pages.create`), certifique-se de que o parâmetro `parent` use `data_source_id`.

**DEPOIS**:
```python
# O jeito correto, usando o data_source_id que deve ser carregado na inicialização do serviço
page_data = {
    "parent": {"type": "data_source_id", "data_source_id": "uuid-do-data-source"}, # ✅ Correto
    "properties": { ... }
}
await self.client.pages.create(**page_data)
```