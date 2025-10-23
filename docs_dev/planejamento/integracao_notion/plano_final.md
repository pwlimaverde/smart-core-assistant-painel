# Plano Final de Integração: Django com Notion (v3.0)

**Versão:** 3.0  
**Data:** Janeiro 2025  
**Status:** Planejamento Detalhado

---

## 📋 Índice

1. [Visão Geral e Objetivos](#1-visão-geral-e-objetivos)
2. [Arquitetura de Integração](#2-arquitetura-de-integração)
3. [Interface de Abstração (Contrato de Serviço)](#3-interface-de-abstração-contrato-de-serviço)
4. [Mapeamento de Modelos Django → Notion](#4-mapeamento-de-modelos-django--notion)
5. [Schemas de Databases no Notion](#5-schemas-de-databases-no-notion)
6. [Detalhamento dos Campos e Integrações](#6-detalhamento-dos-campos-e-integrações)
7. [Fluxos de Sincronização](#7-fluxos-de-sincronização)
8. [Estratégias de Sincronização](#8-estratégias-de-sincronização)
9. [Tratamento de Erros e Resiliência](#9-tratamento-de-erros-e-resiliência)
10. [Plano de Implementação](#10-plano-de-implementação)
11. [Testes e Validação](#11-testes-e-validação)
12. [Monitoramento e Logging](#12-monitoramento-e-logging)

---

## 1. Visão Geral e Objetivos

### 1.1. Objetivo Principal

Criar uma integração bidirecional entre o sistema Django (Smart Core Assistant Painel) e o Notion, permitindo que a equipe de atendimento visualize e gerencie dados através do Notion enquanto mantém a aplicação Django como fonte primária de verdade.

### 1.2. Princípios Fundamentais

- **Desacoplamento Total**: A integração deve ser completamente desacoplada da lógica de negócio principal
- **Substituibilidade**: A arquitetura deve permitir trocar o Notion por outra plataforma sem impacto no core
- **Rastreabilidade**: Todos os objetos sincronizados devem ser rastreáveis bidireccionalmente
- **Resiliência**: Falhas na sincronização não devem impactar as operações principais
- **Auditabilidade**: Todas as operações de sincronização devem ser logadas

### 1.3. Modelos Incluídos na Sincronização

| Modelo Django | Prioridade | Sincronização | Justificativa |
|---------------|-----------|---------------|---------------|
| `Contato` | Alta | Bidirecional | Equipe precisa visualizar e atualizar contatos |
| `Cliente` | Alta | Bidirecional | Informações completas de clientes |
| `Departamento` | Média | Django → Notion | Estrutura organizacional (somente leitura no Notion) |
| `AtendenteHumano` | Alta | Bidirecional | Gerenciamento de equipe |
| `Atendimento` | Crítica | Bidirecional | Core do sistema de atendimento |
| `Mensagem` | Crítica | Django → Notion | Histórico de conversas (somente leitura no Notion) |
| `WhatsAppInstance` | Excluída | Não sincroniza | Dados sensíveis de credenciais |

---

## 2. Arquitetura de Integração

### 2.1. Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    APLICAÇÃO PRINCIPAL                       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Atendimentos │  │   Clientes   │  │  Operacional │     │
│  │    (app)     │  │    (app)     │  │     (app)    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                     ┌──────▼───────┐                        │
│                     │    SIGNALS   │                        │
│                     │  (Interface) │                        │
│                     └──────┬───────┘                        │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             │ Signal Bus
                             │
┌────────────────────────────▼─────────────────────────────────┐
│               APP DE INTEGRAÇÃO (notion_sync)                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           SyncServiceInterface (ABC)                 │  │
│  │  • sync_to_external()                                │  │
│  │  • sync_from_external()                              │  │
│  │  • handle_webhook()                                  │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                      │
│         ┌─────────────┴─────────────┐                       │
│         │                           │                       │
│  ┌──────▼────────┐         ┌───────▼────────┐             │
│  │NotionSyncServ │         │FutureSyncServ  │             │
│  │(Implementação)│         │(Outra API)     │             │
│  └──────┬────────┘         └────────────────┘             │
│         │                                                   │
│  ┌──────▼────────────────────────────────────┐            │
│  │  Receivers (Ouve signals do core)        │            │
│  │  • on_atendimento_created()              │            │
│  │  • on_contato_updated()                  │            │
│  └───────────────────────────────────────────┘            │
│                                                            │
│  ┌──────────────────────────────────────────┐            │
│  │  Webhook Views (Recebe do Notion)        │            │
│  │  • notion_webhook_handler()              │            │
│  └───────────────────────────────────────────┘            │
└────────────────────────┬───────────────────────────────────┘
                         │
                         │ HTTP API
                         │
┌────────────────────────▼───────────────────────────────────┐
│                      NOTION API                             │
│  • Databases & Data Sources                                │
│  • Pages & Properties                                      │
│  • Webhooks                                                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2. Estrutura de Diretórios

```
smart_core_assistant_painel/
└── app/
    ├── ui/
    │   ├── atendimentos/        # App principal
    │   │   ├── models.py
    │   │   └── signals.py       # Emite signals
    │   ├── clientes/
    │   │   ├── models.py
    │   │   └── signals.py
    │   └── operacional/
    │       ├── models.py
    │       └── signals.py
    │
    └── integrations/            # NOVO: Apps de integração
        └── notion_sync/         # NOVO: Integração Notion
            ├── __init__.py
            ├── apps.py
            ├── interfaces.py    # Interface abstrata
            ├── services/
            │   ├── __init__.py
            │   ├── notion_service.py      # Implementação Notion
            │   └── mapper_service.py      # Mapeamento de dados
            ├── receivers.py     # Signal receivers
            ├── signals.py       # Signals personalizados
            ├── models.py        # SyncLog, SyncStatus
            ├── views.py         # Webhook endpoints
            ├── urls.py
            ├── utils/
            │   ├── __init__.py
            │   ├── exceptions.py
            │   └── validators.py
            └── tests/
                ├── test_services.py
                ├── test_receivers.py
                └── test_integration.py
```

---

## 3. Interface de Abstração (Contrato de Serviço)

### 3.1. Interface Principal

```python
# app/integrations/notion_sync/interfaces.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum


class SyncDirection(Enum):
    """Direção da sincronização."""
    TO_EXTERNAL = "to_external"      # Django → External
    FROM_EXTERNAL = "from_external"  # External → Django
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(Enum):
    """Status de sincronização."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class ExternalSyncServiceInterface(ABC):
    """
    Interface abstrata para serviços de sincronização externa.
    
    Esta interface define o contrato que qualquer serviço de sincronização
    (Notion, Airtable, Google Sheets, etc.) deve implementar.
    """

    @abstractmethod
    def sync_model_to_external(
        self,
        model_name: str,
        instance_id: int,
        instance_data: Dict[str, Any],
        operation: str = "create"
    ) -> Dict[str, Any]:
        """
        Sincroniza um modelo Django para a plataforma externa.
        
        Args:
            model_name: Nome do modelo (ex: "Atendimento")
            instance_id: ID do objeto Django
            instance_data: Dados serializados do objeto
            operation: Operação (create, update, delete)
            
        Returns:
            Dict contendo:
                - external_id: ID do objeto na plataforma externa
                - status: Status da operação
                - metadata: Informações adicionais
        """
        pass

    @abstractmethod
    def sync_model_from_external(
        self,
        model_name: str,
        external_id: str,
        external_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sincroniza dados da plataforma externa para Django.
        
        Args:
            model_name: Nome do modelo
            external_id: ID do objeto na plataforma externa
            external_data: Dados da plataforma externa
            
        Returns:
            Dict contendo:
                - instance_id: ID do objeto Django
                - status: Status da operação
                - changes: Lista de campos alterados
        """
        pass

    @abstractmethod
    def handle_webhook_event(
        self,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Processa eventos de webhook da plataforma externa.
        
        Args:
            event_data: Payload do webhook
            
        Returns:
            Dict com resultado do processamento
        """
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Valida se a conexão com a plataforma externa está ativa.
        
        Returns:
            True se conectado, False caso contrário
        """
        pass

    @abstractmethod
    def get_external_object(
        self,
        model_name: str,
        external_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Busca um objeto na plataforma externa.
        
        Args:
            model_name: Nome do modelo
            external_id: ID externo
            
        Returns:
            Dados do objeto ou None se não encontrado
        """
        pass


class DataMapperInterface(ABC):
    """Interface para mapeamento de dados entre Django e plataforma externa."""

    @abstractmethod
    def to_external_format(
        self,
        model_name: str,
        django_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Converte dados Django para formato da plataforma externa.
        
        Args:
            model_name: Nome do modelo
            django_data: Dados do Django
            
        Returns:
            Dados no formato externo
        """
        pass

    @abstractmethod
    def from_external_format(
        self,
        model_name: str,
        external_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Converte dados da plataforma externa para formato Django.
        
        Args:
            model_name: Nome do modelo
            external_data: Dados externos
            
        Returns:
            Dados no formato Django
        """
        pass
```

---

## 4. Mapeamento de Modelos Django → Notion

### 4.1. Estratégia de IDs

Cada modelo Django terá um campo adicional para armazenar o ID do Notion:

```python
# Adicionar a TODOS os models sincronizados:
notion_page_id = models.CharField(
    max_length=36,
    blank=True,
    null=True,
    unique=True,
    db_index=True,
    help_text="ID da página correspondente no Notion"
)
```

No Notion, cada database terá uma propriedade `Django ID` (tipo `number`) para rastreamento reverso.

### 4.2. Tabela Geral de Mapeamento

| Modelo Django | Database Notion | Relações | Sincronização |
|---------------|-----------------|----------|---------------|
| Contato | `📞 Contatos` | → Cliente (N:M) | Bidirecional |
| Cliente | `🏢 Clientes` | → Contato (N:M), → Atendimento (1:N) | Bidirecional |
| Departamento | `🏛️ Departamentos` | → AtendenteHumano (1:N) | Django → Notion |
| AtendenteHumano | `👤 Atendentes` | → Departamento (N:1), → Atendimento (1:N) | Bidirecional |
| Atendimento | `🎫 Atendimentos` | → Contato (N:1), → Cliente (N:1), → Atendente (N:1), → Departamento (N:1), → Mensagem (1:N) | Bidirecional |
| Mensagem | `💬 Mensagens` | → Atendimento (N:1) | Django → Notion |

---

## 5. Schemas de Databases no Notion

### 5.1. Database: 📞 Contatos

**Estrutura no Notion:**

```javascript
{
  "title": [{"text": {"content": "📞 Contatos"}}],
  "properties": {
    // ===== IDENTIFICAÇÃO =====
    "Nome": {
      "title": {}  // OBRIGATÓRIO - Property principal
    },
    "Django ID": {
      "number": {
        "format": "number"
      }
    },
    
    // ===== DADOS DE CONTATO =====
    "Telefone": {
      "phone_number": {}
    },
    "Email": {
      "email": {}
    },
    "Nome WhatsApp": {
      "rich_text": {}
    },
    
    // ===== STATUS E DATAS =====
    "Ativo": {
      "checkbox": {}
    },
    "Data Cadastro": {
      "date": {}
    },
    "Última Interação": {
      "date": {}
    },
    
    // ===== RELAÇÕES =====
    "Clientes": {
      "relation": {
        "database_id": "<CLIENTES_DB_ID>",
        "type": "dual_property"
      }
    },
    "Atendimentos": {
      "relation": {
        "database_id": "<ATENDIMENTOS_DB_ID>",
        "type": "dual_property"
      }
    },
    
    // ===== ROLLUPS =====
    "Qtd Atendimentos": {
      "rollup": {
        "relation_property_name": "Atendimentos",
        "rollup_property_name": "Django ID",
        "function": "count"
      }
    },
    
    // ===== METADADOS =====
    "Observações": {
      "rich_text": {}
    }
  }
}
```

**Mapeamento de Campos:**

| Campo Django | Propriedade Notion | Tipo Notion | Transformação |
|--------------|-------------------|-------------|---------------|
| `id` | `Django ID` | number | Direto |
| `telefone` | `Telefone` | phone_number | Formatar para +55... |
| `nome_contato` | `Nome` | title | Direto ou "Sem nome" |
| `email` | `Email` | email | Direto |
| `nome_perfil_whatsapp` | `Nome WhatsApp` | rich_text | Direto |
| `ativo` | `Ativo` | checkbox | Direto |
| `data_cadastro` | `Data Cadastro` | date | ISO 8601 |
| `ultima_interacao` | `Última Interação` | date | ISO 8601 |
| `metadados` | `Observações` | rich_text | JSON → String |
| N/A | `Clientes` | relation | Via API quando relacionado |
| N/A | `Atendimentos` | relation | Via API quando relacionado |

---

### 5.2. Database: 🏢 Clientes

**Estrutura no Notion:**

```javascript
{
  "title": [{"text": {"content": "🏢 Clientes"}}],
  "properties": {
    // ===== IDENTIFICAÇÃO =====
    "Nome Fantasia": {
      "title": {}
    },
    "Django ID": {
      "number": {"format": "number"}
    },
    
    // ===== DADOS BÁSICOS =====
    "Razão Social": {
      "rich_text": {}
    },
    "Tipo": {
      "select": {
        "options": [
          {"name": "Pessoa Física", "color": "blue"},
          {"name": "Pessoa Jurídica", "color": "green"}
        ]
      }
    },
    
    // ===== DOCUMENTOS =====
    "CNPJ": {
      "rich_text": {}
    },
    "CPF": {
      "rich_text": {}
    },
    
    // ===== CONTATO =====
    "Telefone": {
      "phone_number": {}
    },
    "Email": {
      "email": {}
    },
    "Site": {
      "url": {}
    },
    
    // ===== ENDEREÇO =====
    "CEP": {
      "rich_text": {}
    },
    "Logradouro": {
      "rich_text": {}
    },
    "Número": {
      "rich_text": {}
    },
    "Complemento": {
      "rich_text": {}
    },
    "Bairro": {
      "rich_text": {}
    },
    "Cidade": {
      "rich_text": {}
    },
    "UF": {
      "select": {
        "options": [
          {"name": "SP"}, {"name": "RJ"}, {"name": "MG"},
          // ... todos os estados
        ]
      }
    },
    "País": {
      "rich_text": {}
    },
    "Endereço Completo": {
      "formula": {
        "expression": "concat(prop(\"Logradouro\"), \", \", prop(\"Número\"), \" - \", prop(\"Bairro\"), \", \", prop(\"Cidade\"), \"/\", prop(\"UF\"))"
      }
    },
    
    // ===== NEGÓCIO =====
    "Ramo de Atividade": {
      "rich_text": {}
    },
    "Observações": {
      "rich_text": {}
    },
    
    // ===== STATUS E DATAS =====
    "Ativo": {
      "checkbox": {}
    },
    "Data Cadastro": {
      "date": {}
    },
    "Última Atualização": {
      "date": {}
    },
    
    // ===== RELAÇÕES =====
    "Contatos": {
      "relation": {
        "database_id": "<CONTATOS_DB_ID>",
        "type": "dual_property"
      }
    },
    "Atendimentos": {
      "relation": {
        "database_id": "<ATENDIMENTOS_DB_ID>",
        "type": "dual_property"
      }
    },
    
    // ===== ROLLUPS =====
    "Qtd Contatos": {
      "rollup": {
        "relation_property_name": "Contatos",
        "rollup_property_name": "Django ID",
        "function": "count"
      }
    },
    "Qtd Atendimentos": {
      "rollup": {
        "relation_property_name": "Atendimentos",
        "rollup_property_name": "Django ID",
        "function": "count"
      }
    }
  }
}
```

---

### 5.3. Database: 🏛️ Departamentos

**Estrutura no Notion:**

```javascript
{
  "title": [{"text": {"content": "🏛️ Departamentos"}}],
  "properties": {
    // ===== IDENTIFICAÇÃO =====
    "Nome": {
      "title": {}
    },
    "Django ID": {
      "number": {"format": "number"}
    },
    "Slug": {
      "rich_text": {}
    },
    
    // ===== DESCRIÇÃO =====
    "Descrição": {
      "rich_text": {}
    },
    
    // ===== STATUS =====
    "Ativo": {
      "checkbox": {}
    },
    "Data Criação": {
      "date": {}
    },
    
    // ===== RELAÇÕES =====
    "Atendentes": {
      "relation": {
        "database_id": "<ATENDENTES_DB_ID>",
        "type": "dual_property"
      }
    },
    "Atendimentos": {
      "relation": {
        "database_id": "<ATENDIMENTOS_DB_ID>",
        "type": "dual_property"
      }
    },
    
    // ===== ROLLUPS =====
    "Qtd Atendentes": {
      "rollup": {
        "relation_property_name": "Atendentes",
        "rollup_property_name": "Django ID",
        "function": "count"
      }
    },
    "Qtd Atendimentos": {
      "rollup": {
        "relation_property_name": "Atendimentos",
        "rollup_property_name": "Django ID",
        "function": "count"
      }
    }
  }
}
```

---

### 5.4. Database: 👤 Atendentes

**Estrutura no Notion:**

```javascript
{
  "title": [{"text": {"content": "👤 Atendentes"}}],
  "properties": {
    // ===== IDENTIFICAÇÃO =====
    "Nome": {
      "title": {}
    },
    "Django ID": {
      "number": {"format": "number"}
    },
    
    // ===== DADOS PESSOAIS =====
    "Telefone": {
      "phone_number": {}
    },
    "Email": {
      "email": {}
    },
    "Cargo": {
      "rich_text": {}
    },
    
    // ===== DEPARTAMENTO =====
    "Departamento": {
      "relation": {
        "database_id": "<DEPARTAMENTOS_DB_ID>",
        "type": "dual_property"
      }
    },
    
    // ===== STATUS E DISPONIBILIDADE =====
    "Ativo": {
      "checkbox": {}
    },
    "Disponível": {
      "checkbox": {}
    },
    "Status": {
      "formula": {
        "expression": "if(and(prop(\"Ativo\"), prop(\"Disponível\")), \"🟢 Disponível\", if(prop(\"Ativo\"), \"🟡 Ocupado\", \"🔴 Inativo\"))"
      }
    },
    
    // ===== CAPACIDADE =====
    "Max Atendimentos": {
      "number": {"format": "number"}
    },
    "Última Atribuição": {
      "date": {}
    },
    
    // ===== RELAÇÕES =====
    "Atendimentos Ativos": {
      "relation": {
        "database_id": "<ATENDIMENTOS_DB_ID>",
        "type": "dual_property"
      }
    },
    
    // ===== ROLLUPS =====
    "Qtd Atendimentos Ativos": {
      "rollup": {
        "relation_property_name": "Atendimentos Ativos",
        "rollup_property_name": "Django ID",
        "function": "count"
      }
    },
    "Carga Atual": {
      "formula": {
        "expression": "concat(format(prop(\"Qtd Atendimentos Ativos\")), \"/\", format(prop(\"Max Atendimentos\")))"
      }
    },
    
    // ===== DATAS =====
    "Data Cadastro": {
      "date": {}
    },
    "Última Atividade": {
      "date": {}
    },
    
    // ===== ESPECIALIDADES =====
    "Especialidades": {
      "multi_select": {
        "options": []  // Preenchido dinamicamente
      }
    }
  }
}
```

---

### 5.5. Database: 🎫 Atendimentos

**Estrutura no Notion (PRINCIPAL):**

```javascript
{
  "title": [{"text": {"content": "🎫 Atendimentos"}}],
  "properties": {
    // ===== IDENTIFICAÇÃO =====
    "Assunto": {
      "title": {}
    },
    "Django ID": {
      "number": {"format": "number"}
    },
    
    // ===== STATUS =====
    "Status": {
      "select": {
        "options": [
          {"name": "🕐 Aguardando Inicial", "color": "gray"},
          {"name": "⚡ Em Andamento", "color": "blue"},
          {"name": "⏸️ Aguardando Contato", "color": "yellow"},
          {"name": "👤 Aguardando Atendente", "color": "orange"},
          {"name": "↗️ Transferido", "color": "purple"},
          {"name": "✅ Resolvido", "color": "green"},
          {"name": "❌ Cancelado", "color": "red"}
        ]
      }
    },
    "Prioridade": {
      "select": {
        "options": [
          {"name": "🔴 Alta", "color": "red"},
          {"name": "🟡 Média", "color": "yellow"},
          {"name": "🟢 Baixa", "color": "green"}
        ]
      }
    },
    
    // ===== RELAÇÕES PRINCIPAIS =====
    "Contato": {
      "relation": {
        "database_id": "<CONTATOS_DB_ID>",
        "type": "dual_property"
      }
    },
    "Cliente": {
      "relation": {
        "database_id": "<CLIENTES_DB_ID>",
        "type": "dual_property"
      }
    },
    "Atendente": {
      "relation": {
        "database_id": "<ATENDENTES_DB_ID>",
        "type": "dual_property"
      }
    },
    "Departamento": {
      "relation": {
        "database_id": "<DEPARTAMENTOS_DB_ID>",
        "type": "dual_property"
      }
    },
    
    // ===== INFORMAÇÕES DO CONTATO (ROLLUPS) =====
    "Telefone Contato": {
      "rollup": {
        "relation_property_name": "Contato",
        "rollup_property_name": "Telefone",
        "function": "show_original"
      }
    },
    "Email Contato": {
      "rollup": {
        "relation_property_name": "Contato",
        "rollup_property_name": "Email",
        "function": "show_original"
      }
    },
    
    // ===== CANAL =====
    "Canal": {
      "select": {
        "options": [
          {"name": "💬 WhatsApp", "color": "green"},
          {"name": "📧 Email", "color": "blue"},
          {"name": "📞 Telefone", "color": "orange"},
          {"name": "🌐 Web", "color": "purple"}
        ]
      }
    },
    
    // ===== DATAS E TEMPO =====
    "Data Abertura": {
      "date": {}
    },
    "Data Primeira Resposta": {
      "date": {}
    },
    "Data Finalização": {
      "date": {}
    },
    "Última Mensagem": {
      "date": {}
    },
    
    // ===== MÉTRICAS (FÓRMULAS) =====
    "Tempo Primeira Resposta": {
      "formula": {
        "expression": "dateBetween(prop(\"Data Primeira Resposta\"), prop(\"Data Abertura\"), \"minutes\")"
      }
    },
    "Tempo Total": {
      "formula": {
        "