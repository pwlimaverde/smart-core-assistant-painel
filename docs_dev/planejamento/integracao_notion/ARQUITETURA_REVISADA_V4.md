# Arquitetura Revisada v4.0 - Kanban de Atendimentos

**Data:** Janeiro 2025  
**Status:** ✅ ARQUITETURA DEFINITIVA  
**Foco:** Gestão de Atendimentos via Kanban com Substituibilidade de Plataforma

---

## 🎯 Objetivo Principal

Permitir que **atendentes gerenciem atendimentos via Kanban** (Notion, Airtable, ou outra plataforma), atualizando status e visualizando mensagens, mantendo Django como fonte de verdade e garantindo **fácil substituição da plataforma externa**.

---

## 📋 Casos de Uso

### 1. Atendente Visualiza Kanban
- Ver cards de atendimentos agrupados por status (colunas)
- Ver título, contato, prioridade, última mensagem
- Filtrar por departamento, atendente, prioridade

### 2. Atendente Atualiza Status
- Arrasta card entre colunas (Fila → Em Atendimento → Resolvido)
- Webhook da plataforma externa → Django
- Status atualizado no core via signal

### 3. Atendente Visualiza Mensagens
- Clica no card → Abre página com histórico completo
- Mensagens sincronizadas automaticamente (read-only)

### 4. Sistema Cria Novo Atendimento
- WhatsApp recebe mensagem → Django cria Atendimento
- Signal → AtendimentoSync criado
- Signal → API externa cria card no Kanban
- Atendente vê novo card aparecer

### 5. Troca de Plataforma (Notion → Airtable)
- Criar nova implementação da interface
- Atualizar configuração
- Zero mudanças no código core

---

## 🏗️ Arquitetura em 3 Camadas

```
┌─────────────────────────────────────────────────────────┐
│             CAMADA 1: APLICAÇÃO CORE                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Atendimento  │  │   Mensagem   │  │   Contato    │ │
│  │  (Models)    │  │   (Models)   │  │   (Models)   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘ │
│         │                  │                            │
│         └──────┬───────────┘                            │
└────────────────┼────────────────────────────────────────┘
                 │ post_save signal
                 ▼
┌─────────────────────────────────────────────────────────┐
│         CAMADA 2: APP DE INTEGRAÇÃO (notion_sync)        │
│                                                          │
│  ┌───────────────────────────────────────────────────┐ │
│  │        MODELS INTERMEDIÁRIOS (Shadow DB)          │ │
│  │  ┌─────────────────┐  ┌──────────────────┐       │ │
│  │  │AtendimentoSync  │  │  MensagemSync    │       │ │
│  │  │(filtrado)       │  │  (filtrado)      │       │ │
│  │  └────────┬────────┘  └────────┬─────────┘       │ │
│  └───────────┼─────────────────────┼─────────────────┘ │
│              │                     │                    │
│              └──────────┬──────────┘                    │
│                         │ post_save signal              │
│                         ▼                               │
│  ┌───────────────────────────────────────────────────┐ │
│  │      INTERFACE ABSTRATA (ABC)                     │ │
│  │  ExternalKanbanServiceInterface                   │ │
│  │    • create_card(atendimento_sync)                │ │
│  │    • update_card(atendimento_sync)                │ │
│  │    • delete_card(external_id)                     │ │
│  │    • add_messages(external_id, mensagens)         │ │
│  │    • handle_webhook(payload)                      │ │
│  └─────────────────┬─────────────────────────────────┘ │
│                    │ implements                         │
│         ┌──────────┴──────────┐                        │
│         ▼                     ▼                        │
│  ┌──────────────┐      ┌──────────────┐               │
│  │NotionService │      │AirtableServ  │               │
│  │(atual)       │      │(futuro)      │               │
│  └──────┬───────┘      └──────────────┘               │
└─────────┼──────────────────────────────────────────────┘
          │ HTTPS
          ▼
┌─────────────────────────────────────────────────────────┐
│              CAMADA 3: PLATAFORMA EXTERNA                │
│  ┌───────────────────────────────────────────────────┐ │
│  │   Notion Database: 🎫 Kanban de Atendimentos     │ │
│  │   Views: Board (por status), Table, Timeline     │ │
│  └───────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────┐ │
│  │   Child Pages: 💬 Mensagens do Atendimento       │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Models do App `notion_sync`

### 1. AtendimentoSync (Shadow Model)

**Propósito:** Contém APENAS campos necessários para Kanban, desnormalizados para performance

```python
# app/integrations/notion_sync/models.py

from django.db import models
from typing import Optional

class AtendimentoSync(models.Model):
    """
    Model intermediário - contém apenas dados necessários para Kanban.
    Desnormaliza informações para reduzir queries à API externa.
    """
    
    # ===== LINK COM CORE =====
    atendimento = models.OneToOneField(
        'atendimentos.Atendimento',
        on_delete=models.CASCADE,
        related_name='sync_data',
        primary_key=True
    )
    
    # ===== DADOS DO CARD (Desnormalizados) =====
    titulo = models.CharField(max_length=200)
    status = models.CharField(max_length=20)  # cópia
    prioridade = models.CharField(max_length=10)  # cópia
    canal = models.CharField(max_length=20)  # cópia
    
    # Contato (desnormalizado)
    contato_nome = models.CharField(max_length=100, blank=True)
    contato_telefone = models.CharField(max_length=20)
    
    # Cliente (desnormalizado)
    cliente_nome = models.CharField(max_length=200, blank=True)
    
    # Atendente/Departamento (desnormalizado)
    atendente_nome = models.CharField(max_length=100, blank=True)
    departamento_nome = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    data_abertura = models.DateTimeField()
    ultima_mensagem_em = models.DateTimeField(null=True, blank=True)
    
    # Prévia (para card)
    ultima_mensagem_previa = models.CharField(max_length=150, blank=True)
    total_mensagens = models.IntegerField(default=0)
    
    # ===== SINCRONIZAÇÃO =====
    external_page_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    sync_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendente'),
            ('synced', 'Sincronizado'),
            ('error', 'Erro')
        ],
        default='pending'
    )
    
    last_synced_at = models.DateTimeField(null=True, blank=True)
    sync_error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notion_sync_atendimento'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['sync_status']),
            models.Index(fields=['external_page_id']),
        ]
    
    def __str__(self):
        return f"Sync: {self.titulo}"
    
    @classmethod
    def create_from_atendimento(cls, atendimento):
        """Factory: cria a partir do Atendimento core."""
        cliente = atendimento.cliente
        
        return cls.objects.create(
            atendimento=atendimento,
            titulo=atendimento.assunto or f"Atendimento #{atendimento.id}",
            status=atendimento.status,
            prioridade=atendimento.prioridade,
            canal=atendimento.canal,
            contato_nome=atendimento.contato.nome_contato or "Sem nome",
            contato_telefone=atendimento.contato.telefone,
            cliente_nome=cliente.nome_fantasia if cliente else "",
            atendente_nome=atendimento.atendente_humano.nome if atendimento.atendente_humano else "",
            departamento_nome=atendimento.departamento.nome if atendimento.departamento else "",
            data_abertura=atendimento.data_inicio,
            ultima_mensagem_em=atendimento.data_ultima_mensagem,
        )
    
    def update_from_atendimento(self):
        """Atualiza campos a partir do Atendimento core."""
        atendimento = self.atendimento
        cliente = atendimento.cliente
        
        self.titulo = atendimento.assunto or f"Atendimento #{atendimento.id}"
        self.status = atendimento.status
        self.prioridade = atendimento.prioridade
        self.canal = atendimento.canal
        self.contato_nome = atendimento.contato.nome_contato or "Sem nome"
        self.cliente_nome = cliente.nome_fantasia if cliente else ""
        self.atendente_nome = atendimento.atendente_humano.nome if atendimento.atendente_humano else ""
        self.departamento_nome = atendimento.departamento.nome if atendimento.departamento else ""
        self.ultima_mensagem_em = atendimento.data_ultima_mensagem
        
        self.sync_status = 'pending'
        self.save()
```

---

### 2. MensagemSync (Shadow Model)

```python
class MensagemSync(models.Model):
    """
    Model intermediário para mensagens.
    Apenas campos necessários para exibição no Kanban.
    """
    
    # ===== LINK COM CORE =====
    mensagem = models.OneToOneField(
        'atendimentos.Mensagem',
        on_delete=models.CASCADE,
        related_name='sync_data',
        primary_key=True
    )
    
    # ===== DADOS DA MENSAGEM =====
    atendimento_sync = models.ForeignKey(
        AtendimentoSync,
        on_delete=models.CASCADE,
        related_name='mensagens_sync'
    )
    
    remetente_tipo = models.CharField(max_length=20)  # contato, bot, atendente
    remetente_nome = models.CharField(max_length=100)
    conteudo_previa = models.TextField(max_length=500)  # Limitado para Notion
    tipo_mensagem = models.CharField(max_length=30)  # texto, imagem, etc
    timestamp = models.DateTimeField()
    
    # ===== SINCRONIZAÇÃO =====
    external_block_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    sync_status = models.CharField(max_length=20, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notion_sync_mensagem'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['atendimento_sync', 'timestamp']),
        ]
    
    @classmethod
    def create_from_mensagem(cls, mensagem):
        """Factory: cria a partir da Mensagem core."""
        try:
            atendimento_sync = AtendimentoSync.objects.get(
                atendimento=mensagem.atendimento
            )
        except AtendimentoSync.DoesNotExist:
            # Criar se não existir
            atendimento_sync = AtendimentoSync.create_from_atendimento(
                mensagem.atendimento
            )
        
        # Determinar nome do remetente
        if mensagem.remetente == 'contato':
            remetente_nome = mensagem.atendimento.contato.nome_contato or "Cliente"
        elif mensagem.remetente == 'bot':
            remetente_nome = "Bot"
        else:
            remetente_nome = mensagem.atendimento.atendente_humano.nome if mensagem.atendimento.atendente_humano else "Atendente"
        
        return cls.objects.create(
            mensagem=mensagem,
            atendimento_sync=atendimento_sync,
            remetente_tipo=mensagem.remetente,
            remetente_nome=remetente_nome,
            conteudo_previa=mensagem.conteudo[:500],  # Limitar
            tipo_mensagem=mensagem.tipo,
            timestamp=mensagem.timestamp,
        )
```

---

### 3. SyncConfig (Configuração)

```python
class SyncConfig(models.Model):
    """Configuração dinâmica da integração."""
    
    key = models.CharField(max_length=100, unique=True, primary_key=True)
    value = models.JSONField()
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notion_sync_config'
    
    @classmethod
    def get_value(cls, key, default=None):
        """Helper para pegar valor."""
        try:
            config = cls.objects.get(key=key, active=True)
            return config.value
        except cls.DoesNotExist:
            return default

# Exemplos de configurações:
# SYNC_ENABLED: True/False
# EXTERNAL_PLATFORM: "notion" / "airtable"
# NOTION_DATABASE_ID: "abc-123-xyz"
# SYNC_BATCH_SIZE: 50
```

---

### 4. SyncLog (Auditoria)

```python
class SyncLog(models.Model):
    """Log de todas as operações de sincronização."""
    
    operation = models.CharField(max_length=50)  # create_card, update_card, etc
    model_type = models.CharField(max_length=50)  # AtendimentoSync, MensagemSync
    model_id = models.IntegerField()
    
    status = models.CharField(
        max_length=20,
        choices=[('success', 'Sucesso'), ('error', 'Erro')]
    )
    
    request_data = models.JSONField(null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    duration_ms = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notion_sync_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model_type', 'model_id']),
            models.Index(fields=['status', 'created_at']),
        ]
```

---

## 🔌 Interface Abstrata

```python
# app/integrations/notion_sync/interfaces.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class ExternalKanbanServiceInterface(ABC):
    """
    Interface para serviços de Kanban externos.
    Implementações: NotionKanbanService, AirtableKanbanService, etc.
    """
    
    @abstractmethod
    def create_card(self, atendimento_sync: 'AtendimentoSync') -> str:
        """
        Cria um card no Kanban externo.
        
        Args:
            atendimento_sync: Dados do atendimento
            
        Returns:
            external_page_id: ID do card criado
        """
        pass
    
    @abstractmethod
    def update_card(self, atendimento_sync: 'AtendimentoSync') -> None:
        """
        Atualiza um card existente.
        
        Args:
            atendimento_sync: Dados atualizados
        """
        pass
    
    @abstractmethod
    def delete_card(self, external_page_id: str) -> None:
        """
        Remove/arquiva um card.
        
        Args:
            external_page_id: ID do card
        """
        pass
    
    @abstractmethod
    def add_messages_to_card(
        self,
        external_page_id: str,
        mensagens_sync: List['MensagemSync']
    ) -> None:
        """
        Adiciona mensagens ao card (como child blocks/pages).
        
        Args:
            external_page_id: ID do card
            mensagens_sync: Lista de mensagens
        """
        pass
    
    @abstractmethod
    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa webhook da plataforma externa.
        
        Args:
            payload: Dados do webhook
            
        Returns:
            Resultado do processamento
        """
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Valida se a conexão está funcionando.
        
        Returns:
            True se conectado
        """
        pass
```

---

## 🔄 Fluxo de Sincronização

### Fluxo 1: Django → Plataforma Externa (Criar Card)

```python
# Signal em notion_sync/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from app.ui.atendimentos.models import Atendimento
from .models import AtendimentoSync
from .tasks import sync_atendimento_to_external

@receiver(post_save, sender=Atendimento)
def on_atendimento_created_or_updated(sender, instance, created, **kwargs):
    """
    Quando um Atendimento é criado/atualizado, sincroniza.
    """
    # Criar ou atualizar AtendimentoSync
    atendimento_sync, sync_created = AtendimentoSync.objects.get_or_create(
        atendimento=instance,
        defaults={
            'titulo': instance.assunto or f"Atendimento #{instance.id}",
            'status': instance.status,
            # ... outros campos via create_from_atendimento()
        }
    )
    
    if not sync_created:
        # Atualizar dados
        atendimento_sync.update_from_atendimento()
    
    # Disparar task assíncrona para sincronizar com plataforma externa
    sync_atendimento_to_external.delay(atendimento_sync.atendimento_id)
```

### Fluxo 2: Plataforma Externa → Django (Webhook)

```python
# View em notion_sync/views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services import get_kanban_service
import json

@csrf_exempt
def external_webhook(request):
    """
    Recebe webhooks da plataforma externa (Notion, Airtable, etc.)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        payload = json.loads(request.body)
        
        # Pegar serviço configurado
        service = get_kanban_service()
        
        # Processar webhook
        result = service.handle_webhook(payload)
        
        return JsonResponse(result, status=200)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
```

---

## 🗂️ Schema Notion Database (Único)

### Database: 🎫 Kanban de Atendimentos

```javascript
{
  "title": [{"text": {"content": "🎫 Kanban de Atendimentos"}}],
  "properties": {
    // ===== TÍTULO (OBRIGATÓRIO) =====
    "Título": {
      "title": {}
    },
    
    // ===== IDENTIFICAÇÃO =====
    "Django ID": {
      "number": {"format": "number"}
    },
    
    // ===== STATUS (PARA KANBAN) =====
    "Status": {
      "select": {
        "options": [
          {"name": "🕐 Fila", "color": "gray"},
          {"name": "⚡ Em Atendimento", "color": "blue"},
          {"name": "⏸️ Aguardando Retorno", "color": "yellow"},
          {"name": "✅ Resolvido", "color": "green"},
          {"name": "❌ Cancelado", "color": "red"}
        ]
      }
    },
    
    // ===== PRIORIDADE =====
    "Prioridade": {
      "select": {
        "options": [
          {"name": "🟢 Baixa", "color": "green"},
          {"name": "🟡 Normal", "color": "yellow"},
          {"name": "🔴 Alta", "color": "red"},
          {"name": "🔥 Urgente", "color": "orange"}
        ]
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
    
    // ===== DADOS DO CONTATO =====
    "Contato": {
      "rich_text": {}
    },
    "Telefone": {
      "phone_number": {}
    },
    "Cliente": {
      "rich_text": {}
    },
    
    // ===== ATRIBUIÇÃO =====
    "Atendente": {
      "rich_text": {}
    },
    "Departamento": {
      "rich_text": {}
    },
    
    // ===== TIMESTAMPS =====
    "Data Abertura": {
      "date": {}
    },
    "Última Mensagem": {
      "date": {}
    },
    
    // ===== PRÉVIA =====
    "Última Msg": {
      "rich_text": {}
    },
    "Qtd Mensagens": {
      "number": {"format": "number"}
    }
  }
}
```

**Views Configuradas:**
- **Board View** (Principal): Agrupado por "Status" - KANBAN
- **Table View**: Visualização tabular
- **Timeline View**: Por "Data Abertura"

**Mensagens:** Adicionadas como **child pages** ou **blocks** dentro da página do atendimento

---

## 📝 Implementação do Service (Notion)

```python
# app/integrations/notion_sync/services/notion_service.py

from notion_client import Client
from ..interfaces import ExternalKanbanServiceInterface
from ..models import AtendimentoSync, MensagemSync, SyncLog
import os

class NotionKanbanService(ExternalKanbanServiceInterface):
    """Implementação para Notion."""
    
    def __init__(self):
        self.client = Client(auth=os.getenv('NOTION_TOKEN'))
        self.database_id = os.getenv('NOTION_KANBAN_DB_ID')
    
    def create_card(self, atendimento_sync: AtendimentoSync) -> str:
        """Cria card no Notion."""
        properties = {
            "Título": {
                "title": [{"text": {"content": atendimento_sync.titulo}}]
            },
            "Django ID": {
                "number": atendimento_sync.atendimento_id
            },
            "Status": {
                "select": {"name": self._map_status(atendimento_sync.status)}
            },
            "Prioridade": {
                "select": {"name": self._map_prioridade(atendimento_sync.prioridade)}
            },
            "Canal": {
                "select": {"name": self._map_canal(atendimento_sync.canal)}
            },
            "Contato": {
                "rich_text": [{"text": {"content": atendimento_sync.contato_nome}}]
            },
            "Telefone": {
                "phone_number": atendimento_sync.contato_telefone
            },
            "Cliente": {
                "rich_text": [{"text": {"content": atendimento_sync.cliente_nome}}]
            },
            "Atendente": {
                "rich_text": [{"text": {"content": atendimento_sync.atendente_nome}}]
            },
            "Departamento": {
                "rich_text": [{"text": {"content": atendimento_sync.departamento_nome}}]
            },
            "Data Abertura": {
                "date": {"start": atendimento_sync.data_abertura.isoformat()}
            },
            "Qtd Mensagens": {
                "number": atendimento_sync.total_mensagens
            }
        }
        
        if atendimento_sync.ultima_mensagem_em:
            properties["Última Mensagem"] = {
                "date": {"start": atendimento_sync.ultima_mensagem_em.isoformat()}
            }
        
        if atendimento_sync.ultima_mensagem_previa:
            properties["Última Msg"] = {
                "rich_text": [{"text": {"content": atendimento_sync.ultima_mensagem_previa}}]
            }
        
        response = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=properties
        )
        
        # Log
        SyncLog.objects.create(
            operation='create_card',
            model_type='AtendimentoSync',
            model_id=atendimento_sync.atendimento_id,
            status='success',
            response_data=response
        )
        
        return response['id']
    
    def update_card(self, atendimento_sync: AtendimentoSync) -> None:
        """Atualiza card existente."""
        if not atendimento_sync.external_page_id:
            raise ValueError("external_page_id não definido")
        
        properties = {
            "Status": {
                "select": {"name": self._map_status(atendimento_sync.status)}
            },
            "Atendente": {
                "rich_text": [{"text": {"content": atendimento_sync.atendente_nome}}]
            },
            "Qtd Mensagens": {
                "number": atendimento_sync.total_mensagens
            }
        }
        
        if atendimento_sync.ultima_mensagem_previa:
            properties["Última Msg"] = {
                "rich_text": [{"text": {"content": atendimento_sync.ultima_mensagem_previa}}]
            }
        
        self.client.pages.update(
            page_id=atendimento_sync.external_page_id,
            properties=properties
        )
    
    def handle_webhook(self, payload):
        """Processa webhook do Notion."""
        # Extrair Django ID da página
        # Atualizar status no Django
        # etc...
        pass
    
    def _map_status(self, status):
        """Mapeia status Django → Notion."""
        mapping = {
            'fila': '🕐 Fila',
            'em_atendimento': '⚡ Em Atendimento',
            'aguardando_retorno': '⏸️ Aguardando Retorno',
            'resolvido': '✅ Resolvido',
            'cancelado': '❌ Cancelado'
        }
        return mapping.get(status, '🕐 Fila')
    
    def _map_prioridade(self, prioridade):
        mapping = {
            'baixa': '🟢 Baixa',
            'normal': '🟡 Normal',
            'alta': '🔴 Alta',
            'urgente': '🔥 Urgente'
        }
        return mapping.get(prioridade, '🟡 Normal')
    
    def _map_canal(self, canal):
        mapping = {
            'whatsapp': '💬 WhatsApp',
            'email': '📧 Email',
            'telefone': '📞 Telefone',
            'web': '🌐 Web'
        }
        return mapping.get(canal, '💬 WhatsApp')
```

---

## ✅ Vantagens desta Arquitetura

### 1. Desacoplamento Total
- ✅ App core não sabe nada sobre Notion
- ✅ Models principais puros
- ✅ Fácil remover integração

### 2. Substituibilidade
```python
# Trocar Notion por Airtable:
# 1. Criar AirtableKanbanService(ExternalKanbanServiceInterface)
# 2. Atualizar SyncConfig: EXTERNAL_PLATFORM = "airtable"
# 3. Zero mudanças no core
```

### 3. Performance
- ✅ Dados desnormalizados (menos queries)
- ✅ Sincronização assíncrona (Celery)
- ✅ Apenas campos necessários

### 4.