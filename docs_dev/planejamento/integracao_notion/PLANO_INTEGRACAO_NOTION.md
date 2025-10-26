# Plano Completo de Integração Django ↔ Notion

**Versão:** 5.0  
**Status:** ✅ Planejamento Consolidado - Pronto para Execução  
**Última Atualização:** Janeiro 2025

---

## 📋 Visão Geral

Este documento consolida o plano completo de implementação da integração entre o **Smart Core Assistant Painel** e a plataforma **Notion**, focando na finalização dos models pendentes seguindo o padrão já estabelecido por `ContatoSync` e `ClienteSync`.

### 🎯 Situação Atual

- ✅ **Implementado**: `ContatoSync`, `ClienteSync` (com shadow models completos)
- ✅ **Estrutura Base**: App `notion_sync` configurado com models de apoio
- 🔄 **Pendente**: `DepartamentoSync`, `AtendenteSync`, `AtendimentoSync`, `MensagemSync`
- 🔄 **Pendente**: Mappers, Serviços, Tasks, Webhooks

---

## 🏗️ Arquitetura Consolidada

### Fluxo Principal Django → Notion
```
Django Model → Signal → Shadow Model → SyncLog → Celery Task → NotionService → Notion API
```

### Fluxo Retorno Notion → Django
```
Notion Webhook → Validation → Mapper → Django Model (skip_sync=True) → Shadow Model Update
```

---

## 📊 Status dos Models

### ✅ Models Implementados (Padrão Referência)

#### 1. ContatoSync
- **Arquivo**: `models.py#L657-1002`
- **Features**:
  - Manager customizado com queries específicas
  - Preparação de dados para Notion
  - Formatação de telefones
  - Detecção de contato principal
  - Métodos de sincronização completos
  - Controle de status (synced, failed, pending)

#### 2. ClienteSync  
- **Arquivo**: `models.py#L1005-1271`
- **Features**:
  - Similar ao ContatoSync
  - Formatação de CNPJ
  - Preparação de dados específicos de cliente
  - Métodos de sincronização

---

## 🔄 Models Pendentes (Padrão a Seguir)

### 1. DepartamentoSync

**Status**: ⚠️ Implementação Parcial  
**Arquivo**: `models.py#L1275-1332`

**O que falta implementar**:
```python
class DepartamentoSyncManager(models.Manager):
    """Manager customizado para DepartamentoSync"""
    
    def pending_sync(self) -> QuerySet['DepartamentoSync']:
        """Departamentos pendentes de sincronização"""
        return self.filter(
            Q(external_id__isnull=True) |
            Q(last_sync__lt=timezone.now() - timezone.timedelta(hours=1)),
            is_active=True
        )
    
    def with_sync_errors(self) -> QuerySet['DepartamentoSync']:
        """Departamentos com erros de sincronização"""
        return self.filter(
            sync_errors__gt=0,
            last_error__isnull=False
        )
    
    def needs_sync(self) -> QuerySet['DepartamentoSync']:
        """Departamentos que precisam ser sincronizados"""
        return self.filter(needs_sync=True, is_active=True)

class DepartamentoSync(models.Model):
    # ... campos existentes ...
    
    # Métodos a implementar:
    def prepare_notion_data(self) -> dict:
        """Prepara dados para envio ao Notion"""
        return {
            "Nome": self.departamento.nome,
            "Descrição": self.departamento.descricao or "",
            "Ativo": self.departamento.is_ativo,
            "Data Criação": self.departamento.created_at.isoformat() if self.departamento.created_at else None,
            "Última Atualização": self.departamento.updated_at.isoformat() if self.departamento.updated_at else None,
        }
    
    def needs_sync(self) -> bool:
        """Verifica se precisa sincronizar"""
        if not self.external_id:
            return True
        
        # Se houve mudança no departamento
        if self.departamento.updated_at and self.last_sync:
            if self.departamento.updated_at > self.last_sync:
                return True
        
        return False
    
    def mark_as_synced(self, external_id: str) -> None:
        """Marca como sincronizado com sucesso"""
        self.external_id = external_id
        self.last_sync = timezone.now()
        self.sync_errors = 0
        self.last_error = None
        self.save(update_fields=['external_id', 'last_sync', 'sync_errors', 'last_error'])
    
    def mark_as_failed(self, error_message: str) -> None:
        """Marca como falha na sincronização"""
        self.sync_errors = F('sync_errors') + 1
        self.last_error = error_message
        self.save(update_fields=['sync_errors', 'last_error'])
```

### 2. AtendenteSync

**Status**: ⚠️ Implementação Parcial  
**Arquivo**: `models.py#L1335-1392`

**O que falta implementar**:
```python
class AtendenteSyncManager(models.Manager):
    """Manager customizado para AtendenteSync"""
    
    def pending_sync(self) -> QuerySet['AtendenteSync']:
        """Atendentes pendentes de sincronização"""
        return self.filter(
            Q(external_id__isnull=True) |
            Q(last_sync__lt=timezone.now() - timezone.timedelta(hours=1)),
            is_active=True
        )
    
    def with_sync_errors(self) -> QuerySet['AtendenteSync']:
        """Atendentes com erros de sincronização"""
        return self.filter(
            sync_errors__gt=0,
            last_error__isnull=False
        )
    
    def needs_sync(self) -> QuerySet['AtendenteSync']:
        """Atendentes que precisam ser sincronizados"""
        return self.filter(needs_sync=True, is_active=True)

class AtendenteSync(models.Model):
    # ... campos existentes ...
    
    # Métodos a implementar:
    def prepare_notion_data(self) -> dict:
        """Prepara dados para envio ao Notion"""
        return {
            "Nome": self.atendente.usuario.get_full_name() or self.atendente.usuario.username,
            "Email": self.atendente.usuario.email,
            "Departamento": self.atendente.departamento.nome if self.atendente.departamento else None,
            "Ativo": self.atendente.is_ativo,
            "Cargo": self.atendente.cargo or "",
            "Data Criação": self.atendente.created_at.isoformat() if self.atendente.created_at else None,
            "Última Atualização": self.atendente.updated_at.isoformat() if self.atendente.updated_at else None,
        }
    
    def needs_sync(self) -> bool:
        """Verifica se precisa sincronizar"""
        if not self.external_id:
            return True
        
        # Se houve mudança no atendente
        if self.atendente.updated_at and self.last_sync:
            if self.atendente.updated_at > self.last_sync:
                return True
        
        return False
    
    def mark_as_synced(self, external_id: str) -> None:
        """Marca como sincronizado com sucesso"""
        self.external_id = external_id
        self.last_sync = timezone.now()
        self.sync_errors = 0
        self.last_error = None
        self.save(update_fields=['external_id', 'last_sync', 'sync_errors', 'last_error'])
    
    def mark_as_failed(self, error_message: str) -> None:
        """Marca como falha na sincronização"""
        self.sync_errors = F('sync_errors') + 1
        self.last_error = error_message
        self.save(update_fields=['sync_errors', 'last_error'])
```

### 3. MensagemSync

**Status**: ⚠️ Implementação Parcial  
**Arquivo**: `models.py#L1395-1452`

**O que falta implementar**:
```python
class MensagemSyncManager(models.Manager):
    """Manager customizado para MensagemSync"""
    
    def pending_sync(self) -> QuerySet['MensagemSync']:
        """Mensagens pendentes de sincronização"""
        return self.filter(
            Q(external_id__isnull=True) |
            Q(last_sync__lt=timezone.now() - timezone.timedelta(hours=1)),
            is_active=True
        )
    
    def with_sync_errors(self) -> QuerySet['MensagemSync']:
        """Mensagens com erros de sincronização"""
        return self.filter(
            sync_errors__gt=0,
            last_error__isnull=False
        )
    
    def needs_sync(self) -> QuerySet['MensagemSync']:
        """Mensagens que precisam ser sincronizadas"""
        return self.filter(needs_sync=True, is_active=True)

class MensagemSync(models.Model):
    # ... campos existentes ...
    
    # Métodos a implementar:
    def prepare_notion_data(self) -> dict:
        """Prepara dados para envio ao Notion"""
        # Obter informações relacionadas
        atendimento_nome = ""
        if self.mensagem.atendimento:
            atendimento_nome = f"#{self.mensagem.atendimento.id}"
        
        remetente = ""
        if self.mensagem.remetente_tipo == 'cliente':
            remetente = self.mensagem.atendimento.cliente.nome_fantasia if self.mensagem.atendimento and self.mensagem.atendimento.cliente else "Cliente"
        elif self.mensagem.remetente_tipo == 'atendente':
            remetente = self.mensagem.atendente.usuario.get_full_name() if self.mensagem.atendente and self.mensagem.atendente.usuario else "Atendente"
        elif self.mensagem.remetente_tipo == 'sistema':
            remetente = "Sistema"
        
        return {
            "Conteúdo": self.mensagem.conteudo[:2000],  # Limite do Notion
            "Tipo": self.mensagem.tipo,
            "Remetente Tipo": self.mensagem.remetente_tipo,
            "Remetente": remetente,
            "Atendimento": atendimento_nome,
            "Data Envio": self.mensagem.data_envio.isoformat() if self.mensagem.data_envio else None,
            "Lida": self.mensagem.lida,
            "Data Leitura": self.mensagem.data_leitura.isoformat() if self.mensagem.data_leitura else None,
        }
    
    def needs_sync(self) -> bool:
        """Verifica se precisa sincronizar"""
        if not self.external_id:
            return True
        
        # Mensagens geralmente não são atualizadas após criação
        return False
    
    def mark_as_synced(self, external_id: str) -> None:
        """Marca como sincronizado com sucesso"""
        self.external_id = external_id
        self.last_sync = timezone.now()
        self.sync_errors = 0
        self.last_error = None
        self.save(update_fields=['external_id', 'last_sync', 'sync_errors', 'last_error'])
    
    def mark_as_failed(self, error_message: str) -> None:
        """Marca como falha na sincronização"""
        self.sync_errors = F('sync_errors') + 1
        self.last_error = error_message
        self.save(update_fields=['sync_errors', 'last_error'])
```

### 4. AtendimentoSync

**Status**: ⚠️ Apenas definição básica  
**Arquivo**: `MODELS_REDEFINIDOS.md#L387-535`

**Implementação completa necessária**:
```python
class AtendimentoSyncManager(models.Manager):
    """Manager customizado para AtendimentoSync"""
    
    def pending_sync(self) -> QuerySet['AtendimentoSync']:
        """Atendimentos pendentes de sincronização"""
        return self.filter(
            Q(external_id__isnull=True) |
            Q(last_sync__lt=timezone.now() - timezone.timedelta(hours=1)),
            is_active=True
        )
    
    def with_sync_errors(self) -> QuerySet['AtendimentoSync']:
        """Atendimentos com erros de sincronização"""
        return self.filter(
            sync_errors__gt=0,
            last_error__isnull=False
        )
    
    def needs_sync(self) -> QuerySet['AtendimentoSync']:
        """Atendimentos que precisam ser sincronizados"""
        return self.filter(needs_sync=True, is_active=True)

class AtendimentoSync(models.Model):
    """Model de sincronização para Atendimento"""
    
    # Campos básicos
    atendimento = models.OneToOneField(
        'central_atendimento.Atendimento',
        on_delete=models.CASCADE,
        related_name='sync_metadata'
    )
    external_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID da página no Notion"
    )
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data da última sincronização"
    )
    sync_errors = models.PositiveIntegerField(
        default=0,
        help_text="Número de erros de sincronização"
    )
    last_error = models.TextField(
        null=True,
        blank=True,
        help_text="Último erro ocorrido"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Se está ativo para sincronização"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = AtendimentoSyncManager()
    
    class Meta:
        db_table = 'notion_sync_atendimento'
        verbose_name = 'Sincronização de Atendimento'
        verbose_name_plural = 'Sincronizações de Atendimentos'
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['last_sync']),
            models.Index(fields=['sync_errors']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self) -> str:
        return f"Atendimento #{self.atendimento.id} - {self.external_id or 'Pendente'}"
    
    def prepare_notion_data(self) -> dict:
        """Prepara dados para envio ao Notion"""
        return {
            "Protocolo": self.atendimento.protocolo,
            "Cliente": self.atendimento.cliente.nome_fantasia if self.atendimento.cliente else None,
            "Contato": self.atendimento.contato.nome_contato if self.atendimento.contato else None,
            "Departamento": self.atendimento.departamento.nome if self.atendimento.departamento else None,
            "Atendente": self.atendente.atendente.usuario.get_full_name() if self.atendimento.atendente and self.atendente.atendente.usuario else None,
            "Status": self.atendimento.get_status_display(),
            "Prioridade": self.atendimento.get_prioridade_display(),
            "Canal": self.atendimento.get_canal_display(),
            "Assunto": self.atendimento.assunto or "",
            "Descrição": (self.atendimento.descricao or "")[:2000],  # Limite do Notion
            "Data Abertura": self.atendimento.data_abertura.isoformat() if self.atendimento.data_abertura else None,
            "Data Fechamento": self.atendimento.data_fechamento.isoformat() if self.atendimento.data_fechamento else None,
            "SLA": self._calculate_sla_status(),
        }
    
    def _calculate_sla_status(self) -> str:
        """Calcula status do SLA"""
        if not self.atendimento.data_abertura:
            return "N/A"
        
        from datetime import datetime, timedelta
        import pytz
        
        agora = datetime.now(pytz.UTC)
        diff = agora - self.atendimento.data_abertura
        
        # SLA padrão: 24 horas
        sla_limit = timedelta(hours=24)
        
        if diff > sla_limit and self.atendimento.status != 'finalizado':
            return "Vencido"
        elif diff > (sla_limit * 0.8):
            return "Próximo"
        else:
            return "OK"
    
    def needs_sync(self) -> bool:
        """Verifica se precisa sincronizar"""
        if not self.external_id:
            return True
        
        # Se houve mudança no atendimento
        if self.atendimento.updated_at and self.last_sync:
            if self.atendimento.updated_at > self.last_sync:
                return True
        
        return False
    
    def mark_as_synced(self, external_id: str) -> None:
        """Marca como sincronizado com sucesso"""
        self.external_id = external_id
        self.last_sync = timezone.now()
        self.sync_errors = 0
        self.last_error = None
        self.save(update_fields=['external_id', 'last_sync', 'sync_errors', 'last_error'])
    
    def mark_as_failed(self, error_message: str) -> None:
        """Marca como falha na sincronização"""
        self.sync_errors = F('sync_errors') + 1
        self.last_error = error_message
        self.save(update_fields=['sync_errors', 'last_error'])
    
    @property
    def is_synced(self) -> bool:
        """Retorna se está sincronizado"""
        return bool(self.external_id and self.last_sync)
    
    @property
    def sync_age_hours(self) -> int:
        """Idade da última sincronização em horas"""
        if not self.last_sync:
            return 999
        
        from datetime import datetime
        import pytz
        
        agora = datetime.now(pytz.UTC)
        diff = agora - self.last_sync
        return int(diff.total_seconds() / 3600)
    
    @property
    def has_sync_errors(self) -> bool:
        """Retorna se tem erros de sincronização"""
        return self.sync_errors > 0
    
    @property
    def notion_url(self) -> str:
        """URL da página no Notion"""
        if not self.external_id:
            return ""
        
        import os
        database_id = os.getenv('NOTION_DATABASE_ATENDIMENTO_ID', '')
        return f"https://www.notion.so/{database_id}?p={self.external_id.replace('-', '')}"
```

---

## 🎯 Mappers (Pendentes)

Seguindo o padrão de `ContatoMapper` e `ClienteMapper`:

### 1. DepartamentoMapper

```python
class DepartamentoMapper:
    """Mapper para transformação Departamento ↔ Notion"""
    
    @staticmethod
    def to_notion_properties(departamento: 'Departamento') -> dict:
        """Converte model Django para propriedades Notion"""
        return {
            "Nome": {
                "title": [
                    {"text": {"content": departamento.nome}}
                ]
            },
            "Descrição": {
                "rich_text": [
                    {"text": {"content": departamento.descricao or ""}}
                ]
            },
            "Ativo": {
                "checkbox": departamento.is_ativo
            },
            "Data Criação": {
                "date": {
                    "start": departamento.created_at.isoformat() if departamento.created_at else None
                }
            },
            "Última Atualização": {
                "date": {
                    "start": departamento.updated_at.isoformat() if departamento.updated_at else None
                }
            },
            "ID Django": {
                "number": departamento.id
            }
        }
    
    @staticmethod
    def from_notion_properties(page_data: dict) -> dict:
        """Converte propriedades Notion para dados Django"""
        properties = page_data.get('properties', {})
        
        return {
            'nome': properties.get('Nome', {}).get('title', [{}])[0].get('text', {}).get('content', ''),
            'descricao': properties.get('Descrição', {}).get('rich_text', [{}])[0].get('text', {}).get('content', ''),
            'is_ativo': properties.get('Ativo', {}).get('checkbox', False),
        }
```

### 2. AtendenteMapper

```python
class AtendenteMapper:
    """Mapper para transformação Atendente ↔ Notion"""
    
    @staticmethod
    def to_notion_properties(atendente: 'Atendente') -> dict:
        """Converte model Django para propriedades Notion"""
        departamento_nome = atendente.departamento.nome if atendente.departamento else ""
        
        return {
            "Nome": {
                "title": [
                    {"text": {"content": atendente.usuario.get_full_name() or atendente.usuario.username}}
                ]
            },
            "Email": {
                "email": atendente.usuario.email
            },
            "Departamento": {
                "select": {
                    "name": departamento_nome
                } if departamento_nome else None
            },
            "Ativo": {
                "checkbox": atendente.is_ativo
            },
            "Cargo": {
                "rich_text": [
                    {"text": {"content": atendente.cargo or ""}}
                ]
            },
            "Data Criação": {
                "date": {
                    "start": atendente.created_at.isoformat() if atendente.created_at else None
                }
            },
            "Última Atualização": {
                "date": {
                    "start": atendente.updated_at.isoformat() if atendente.updated_at else None
                }
            },
            "ID Django": {
                "number": atendente.id
            }
        }
    
    @staticmethod
    def from_notion_properties(page_data: dict) -> dict:
        """Converte propriedades Notion para dados Django"""
        properties = page_data.get('properties', {})
        
        return {
            # Nota: Atendente requer tratamento especial devido ao relacionamento com User
            'is_ativo': properties.get('Ativo', {}).get('checkbox', True),
            'cargo': properties.get('Cargo', {}).get('rich_text', [{}])[0].get('text', {}).get('content', ''),
        }
```

### 3. MensagemMapper

```python
class MensagemMapper:
    """Mapper para transformação Mensagem ↔ Notion"""
    
    @staticmethod
    def to_notion_properties(mensagem: 'Mensagem') -> dict:
        """Converte model Django para propriedades Notion"""
        # Montar informações contextuais
        atendimento_nome = ""
        if mensagem.atendimento:
            atendimento_nome = f"#{mensagem.atendimento.id}"
        
        remetente = ""
        if mensagem.remetente_tipo == 'cliente':
            remetente = mensagem.atendimento.cliente.nome_fantasia if mensagem.atendimento and mensagem.atendimento.cliente else "Cliente"
        elif mensagem.remetente_tipo == 'atendente':
            remetente = mensagem.atendente.usuario.get_full_name() if mensagem.atendimento and mensagem.atendente.usuario else "Atendente"
        elif mensagem.remetente_tipo == 'sistema':
            remetente = "Sistema"
        
        return {
            "Conteúdo": {
                "rich_text": [
                    {"text": {"content": mensagem.conteudo[:2000]}}  # Limite do Notion
                ]
            },
            "Tipo": {
                "select": {
                    "name": mensagem.tipo
                }
            },
            "Remetente Tipo": {
                "select": {
                    "name": mensagem.remetente_tipo
                }
            },
            "Remetente": {
                "rich_text": [
                    {"text": {"content": remetente}}
                ]
            },
            "Atendimento": {
                "rich_text": [
                    {"text": {"content": atendimento_nome}}
                ]
            },
            "Data Envio": {
                "date": {
                    "start": mensagem.data_envio.isoformat() if mensagem.data_envio else None
                }
            },
            "Lida": {
                "checkbox": mensagem.lida
            },
            "Data Leitura": {
                "date": {
                    "start": mensagem.data_leitura.isoformat() if mensagem.data_leitura else None
                }
            },
            "ID Django": {
                "number": mensagem.id
            }
        }
    
    @staticmethod
    def from_notion_properties(page_data: dict) -> dict:
        """Converte propriedades Notion para dados Django"""
        properties = page_data.get('properties', {})
        
        return {
            'conteudo': properties.get('Conteúdo', {}).get('rich_text', [{}])[0].get('text', {}).get('content', ''),
            'tipo': properties.get('Tipo', {}).get('select', {}).get('name', 'texto'),
            'remetente_tipo': properties.get('Remetente Tipo', {}).get('select', {}).get('name', 'cliente'),
            'lida': properties.get('Lida', {}).get('checkbox', False),
        }
```

### 4. AtendimentoMapper

```python
class AtendimentoMapper:
    """Mapper para transformação Atendimento ↔ Notion"""
    
    @staticmethod
    def to_notion_properties(atendimento: 'Atendimento') -> dict:
        """Converte model Django para propriedades Notion"""
        cliente_nome = atendimento.cliente.nome_fantasia if atendimento.cliente else ""
        contato_nome = atendimento.contato.nome_contato if atendimento.contato else ""
        departamento_nome = atendimento.departamento.nome if atendimento.departamento else ""
        atendente_nome = ""
        if atendimento.atendente and atendimento.atendente.usuario:
            atendente_nome = atendimento.atendente.usuario.get_full_name()
        
        # Calcular SLA
        sla_status = "OK"
        if atendimento.data_abertura:
            from datetime import datetime, timedelta
            import pytz
            
            agora = datetime.now(pytz.UTC)
            diff = agora - atendimento.data_abertura
            sla_limit = timedelta(hours=24)
            
            if diff > sla_limit and atendimento.status != 'finalizado':
                sla_status = "Vencido"
            elif diff > (sla_limit * 0.8):
                sla_status = "Próximo"
        
        return {
            "Protocolo": {
                "rich_text": [
                    {"text": {"content": atendimento.protocolo}}
                ]
            },
            "Cliente": {
                "relation": [
                    {"id": atendimento.cliente.sync_metadata.external_id}
                ] if atendimento.cliente and hasattr(atendimento.cliente, 'sync_metadata') and atendimento.cliente.sync_metadata.external_id else []
            },
            "Contato": {
                "relation": [
                    {"id": atendimento.contato.sync_metadata.external_id}
                ] if atendimento.contato and hasattr(atendimento.contato, 'sync_metadata') and atendimento.contato.sync_metadata.external_id else []
            },
            "Departamento": {
                "select": {
                    "name": departamento_nome
                } if departamento_nome else None
            },
            "Atendente": {
                "select": {
                    "name": atendente_nome
                } if atendente_nome else None
            },
            "Status": {
                "select": {
                    "name": atendimento.get_status_display()
                }
            },
            "Prioridade": {
                "select": {
                    "name": atendimento.get_prioridade_display()
                }
            },
            "Canal": {
                "select": {
                    "name": atendimento.get_canal_display()
                }
            },
            "Assunto": {
                "rich_text": [
                    {"text": {"content": atendimento.assunto or ""}}
                ]
            },
            "Descrição": {
                "rich_text": [
                    {"text": {"content": (atendimento.descricao or "")[:2000]}}  # Limite do Notion
                ]
            },
            "Data Abertura": {
                "date": {
                    "start": atendimento.data_abertura.isoformat() if atendimento.data_abertura else None
                }
            },
            "Data Fechamento": {
                "date": {
                    "start": atendimento.data_fechamento.isoformat() if atendimento.data_fechamento else None
                }
            },
            "SLA": {
                "select": {
                    "name": sla_status
                }
            },
            "ID Django": {
                "number": atendimento.id
            }
        }
    
    @staticmethod
    def from_notion_properties(page_data: dict) -> dict:
        """Converte propriedades Notion para dados Django"""
        properties = page_data.get('properties', {})
        
        # Mapear selects para choices
        status_map = {
            'Aberto': 'aberto',
            'Em Andamento': 'em_andamento',
            'Aguardando Cliente': 'aguardando_cliente',
            'Finalizado': 'finalizado',
            'Cancelado': 'cancelado'
        }
        
        prioridade_map = {
            'Baixa': 'baixa',
            'Normal': 'normal',
            'Alta': 'alta',
            'Urgente': 'urgente'
        }
        
        canal_map = {
            'WhatsApp': 'whatsapp',
            'Email': 'email',
            'Telefone': 'telefone',
            'Chat': 'chat'
        }
        
        status_display = properties.get('Status', {}).get('select', {}).get('name', '')
        prioridade_display = properties.get('Prioridade', {}).get('select', {}).get('name', '')
        canal_display = properties.get('Canal', {}).get('select', {}).get('name', '')
        
        return {
            'protocolo': properties.get('Protocolo', {}).get('rich_text', [{}])[0].get('text', {}).get('content', ''),
            'assunto': properties.get('Assunto', {}).get('rich_text', [{}])[0].get('text', {}).get('content', ''),
            'descricao': properties.get('Descrição', {}).get('rich_text', [{}])[0].get('text', {}).get('content', ''),
            'status': status_map.get(status_display, 'aberto'),
            'prioridade': prioridade_map.get(prioridade_display, 'normal'),
            'canal': canal_map.get(canal_display, 'chat'),
            'data_abertura': properties.get('Data Abertura', {}).get('date', {}).get('start'),
            'data_fechamento': properties.get('Data Fechamento', {}).get('date', {}).get('start'),
        }
```

---

## 🚀 Plano de Implementação

### Fase 1: Finalizar Models (3-4 dias)

**Objetivo**: Completar implementação dos shadow models pendentes

#### Tarefas:
1. **DepartamentoSync**
   - [ ] Implementar `DepartamentoSyncManager`
   - [ ] Adicionar métodos `prepare_notion_data`, `needs_sync`, `mark_as_synced`, `mark_as_failed`
   - [ ] Adicionar properties `is_synced`, `sync_age_hours`, `has_sync_errors`, `notion_url`
   - [ ] Criar migração

2. **AtendenteSync**
   - [ ] Implementar `AtendenteSyncManager`
   - [ ] Adicionar métodos completos de sincronização
   - [ ] Adicionar properties auxiliares
   - [ ] Criar migração

3. **MensagemSync**
   - [ ] Implementar `MensagemSyncManager`
   - [ ] Adicionar métodos completos de sincronização
   - [ ] Adicionar properties auxiliares
   - [ ] Criar migração

4. **AtendimentoSync**
   - [ ] Implementar model completo (não existe ainda)
   - [ ] Implementar `AtendimentoSyncManager`
   - [ ] Adicionar todos os métodos de sincronização
   - [ ] Criar migração

#### Testes:
- [ ] Testar criação automática via signals
- [ ] Testar managers customizados
- [ ] Testar métodos de preparação de dados
- [ ] Testar properties auxiliares

---

### Fase 2: Implementar Mappers (2-3 dias)

**Objetivo**: Criar classes de transformação para todos os models

#### Tarefas:
1. **Criar módulo `services/mappers/`**
   - [ ] `__init__.py` - Expor mappers públicos
   - [ ] `departamento_mapper.py`
   - [ ] `atendente_mapper.py`
   - [ ] `mensagem_mapper.py`
   - [ ] `atendimento_mapper.py`

2. **Implementar métodos de cada mapper**
   - [ ] `to_notion_properties` - Django → Notion
   - [ ] `from_notion_properties` - Notion → Django
   - [ ] Validações específicas

3. **Criar mapper base**
   - [ ] Classe base com métodos comuns
   - [ ] Utilitários de formatação
   - [ ] Tratamento de erros

#### Testes:
- [ ] Testar transformação Django → Notion
- [ ] Testar transformação Notion → Django
- [ ] Testar validações
- [ ] Testar edge cases (campos nulos, textos longos, etc)

---

### Fase 3: Signals Adicionais (2 dias)

**Objetivo**: Implementar signals para os novos models

#### Tarefas:
1. **Criar signals em `signals.py`**
   - [ ] `departamento_saved` - post_save do Departamento
   - [ ] `departamento_deleted` - post_delete do Departamento
   - [ ] `atendente_saved` - post_save do AtendenteHumano
   - [ ] `atendente_deleted` - post_delete do AtendenteHumano
   - [ ] `mensagem_saved` - post_save da Mensagem
   - [ ] `atendimento_saved` - post_save do Atendimento
   - [ ] `atendimento_deleted` - post_delete do Atendimento

2. **Lógica de cada signal**
   - [ ] Criar/atualizar shadow model correspondente
   - [ ] Logar operação em `SyncLog`
   - [ ] Disparar task do Celery (quando implementado)

#### Testes:
- [ ] Testar criação de shadow models
- [ ] Testar atualização de shadow models
- [ ] Testar exclusão de shadow models
- [ ] Testar logs

---

### Fase 4: Serviços Notion (3-4 dias)

**Objetivo**: Implementar serviços completos de integração

#### Tarefas:
1. **Criar `services/notion_service.py`**
   - [ ] Implementar `NotionSyncService` (herda interface)
   - [ ] Métodos CRUD para cada model
   - [ ] Tratamento de erros e retries
   - [ ] Validação de conexão

2. **Métodos do serviço**
   - [ ] `sync_departamento`
   - [ ] `sync_atendente`
   - [ ] `sync_mensagem`
   - [ ] `sync_atendimento`
   - [ ] `delete_departamento`
   - [ ] `delete_atendente`
   - [ ] `delete_atendimento`

3. **Configuração**
   - [ ] Configurar IDs dos databases no Notion
   - [ ] Configurar schema das propriedades
   - [ ] Implementar validação de schema

#### Testes:
- [ ] Testar conexão com API do Notion
- [ ] Testar criação de registros
- [ ] Testar atualização de registros
- [ ] Testar exclusão de registros
- [ ] Testar tratamento de erros

---

### Fase 5: Celery Tasks (2-3 dias)

**Objetivo**: Implementar tarefas assíncronas de sincronização

#### Tarefas:
1. **Criar módulo `tasks.py`**
   - [ ] `sync_departamento_task`
   - [ ] `sync_atendente_task`
   - [ ] `sync_mensagem_task`
   - [ ] `sync_atendimento_task`
   - [ ] `delete_record_task`

2. **Configuração das tasks**
   - [ ] Retry com backoff exponencial
   - [ ] Rate limiting para respeitar limites da API
   - [ ] Circuit breaker para falhas em cascata
   - [ ] Logging detalhado

3. **Integração com signals**
   - [ ] Modificar signals para disparar tasks
   - [ ] Configurar prioridades das tasks
   - [ ] Implementar fila dedicada para Notion

#### Testes:
- [ ] Testar execução assíncrona
- [ ] Testar retry automático
- [ ] Testar rate limiting
- [ ] Testar circuit breaker

---

### Fase 6: Webhook Handler (2 dias)

**Objetivo**: Implementar endpoint para receber eventos do Notion

#### Tarefas:
1. **Criar view em `views.py`**
   - [ ] `notion_webhook` - endpoint principal
   - [ ] Validação de assinatura
   - [ ] Processamento de eventos
   - [ ] Respostas adequadas

2. **Configurar URLs**
   - [ ] Adicionar rota `/webhooks/notion/`
   - [ ] Configurar middleware CSRF se necessário
   - [ ] Documentar endpoint

3. **Processamento de eventos**
   - [ ] `handle_page_updated`
   - [ ] `handle_page_created`
   - [ ] `handle_page_deleted`
   - [ ] Atualizar Django com `skip_sync=True`

#### Testes:
- [ ] Testar validação de assinatura
- [ ] Testar processamento de eventos
- [ ] Testar atualização sem loop infinito
- [ ] Testar segurança

---

### Fase 7: Admin e Monitoramento (1-2 dias)

**Objetivo**: Melhorar interface de administração e monitoramento

#### Tarefas:
1. **Melhorar `admin.py`**
   - [ ] Registrar novos models
   - [ ] Adicionar actions customizadas
   - [ ] Filtros e buscas
   - [ ] Display de status

2. **Dashboard básico**
   - [ ] View com métricas de sincronização
   - [ ] Lista de erros recentes
   - [ ] Status dos serviços
   - [ ] Logs em tempo real

#### Testes:
- [ ] Testar interface admin
- [ ] Testar actions
- [ ] Testar dashboard
- [ ] Testar permissões

---

### Fase 8: Testes e Documentação (2 dias)

**Objetivo**: Completar testes e documentação

#### Tarefas:
1. **Testes unitários**
   - [ ] Testar todos os models
   - [ ] Testar todos os mappers
   - [ ] Testar todos os serviços
   - [ ] Cobertura mínima 80%

2. **Testes de integração**
   - [ ] Testar fluxo completo Django → Notion
   - [ ] Testar fluxo completo Notion → Django
   - [ ] Testar cenários de erro
   - [ ] Testar performance

3. **Documentação**
   - [ ] Atualizar README do app
   - [ ] Documentar novos models
   - [ ] Documentar mappers
   - [ ] Criar guia de troubleshooting

---

## 📊 Configurações Necessárias

### 1. Environment Variables (.env)

```bash
# Notion Configuration
NOTION_TOKEN=secret_your_token_here
NOTION_DATABASE_DEPARTAMENTO_ID=your_database_id
NOTION_DATABASE_ATENDENTE_ID=your_database_id
NOTION_DATABASE_MENSAGEM_ID=your_database_id
NOTION_DATABASE_ATENDIMENTO_ID=your_database_id

# Webhook Configuration
NOTION_WEBHOOK_SECRET=your_webhook_secret
NOTION_WEBHOOK_URL=https://yourdomain.com/webhooks/notion/

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 2. Settings Updates

```python
# Adicionar em settings.py
NOTION_SYNC_CONFIG = {
    'TOKEN': os.getenv('NOTION_TOKEN'),
    'DATABASE_IDS': {
        'Departamento': os.getenv('NOTION_DATABASE_DEPARTAMENTO_ID'),
        'Atendente': os.getenv('NOTION_DATABASE_ATENDENTE_ID'),
        'Mensagem': os.getenv('NOTION_DATABASE_MENSAGEM_ID'),
        'Atendimento': os.getenv('NOTION_DATABASE_ATENDIMENTO_ID'),
    },
    'WEBHOOK_SECRET': os.getenv('NOTION_WEBHOOK_SECRET'),
    'RATE_LIMIT': 10,  # requests per second
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 60,  # seconds
}

# Celery Configuration
CELERY_BEAT_SCHEDULE = {
    'sync-pending-records': {
        'task': 'notion_sync.tasks.sync_pending_records',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'cleanup-old-logs': {
        'task': 'notion_sync.tasks.cleanup_old_logs',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

---

## 🧪 Estratégia de Testes

### 1. Testes Unitários

```python
# tests/app/notion_sync/test_models.py
class TestDepartamentoSync(TestCase):
    def test_prepare_notion_data(self):
        """Testa preparação de dados para Notion"""
        departamento = Departamento.objects.create(nome="TI")
        sync = DepartamentoSync.objects.create(departamento=departamento)
        
        data = sync.prepare_notion_data()
        
        self.assertEqual(data['Nome'], "TI")
        self.assertIn('Data Criação', data)
    
    def test_needs_sync(self):
        """Testa detecção de necessidade de sincronização"""
        departamento = Departamento.objects.create(nome="TI")
        sync = DepartamentoSync.objects.create(departamento=departamento)
        
        # Sem external_id, precisa sincronizar
        self.assertTrue(sync.needs_sync())
        
        # Com external_id e sem mudanças, não precisa sincronizar
        sync.external_id = "test-id"
        sync.last_sync = timezone.now()
        sync.save()
        self.assertFalse(sync.needs_sync())

# tests/app/notion_sync/test_mappers.py
class TestDepartamentoMapper(TestCase):
    def test_to_notion_properties(self):
        """Testa conversão Django → Notion"""
        departamento = Departamento.objects.create(nome="TI", descricao="Departamento de TI")
        
        properties = DepartamentoMapper.to_notion_properties(departamento)
        
        self.assertEqual(properties['Nome']['title'][0]['text']['content'], "TI")
        self.assertEqual(properties['Descrição']['rich_text'][0]['text']['content'], "Departamento de TI")
        self.assertTrue(properties['Ativo']['checkbox'])
    
    def test_from_notion_properties(self):
        """Testa conversão Notion → Django"""
        page_data = {
            'properties': {
                'Nome': {'title': [{'text': {'content': 'TI'}}]},
                'Descrição': {'rich_text': [{'text': {'content': 'Departamento de TI'}}]},
                'Ativo': {'checkbox': True}
            }
        }
        
        data = DepartamentoMapper.from_notion_properties(page_data)
        
        self.assertEqual(data['nome'], "TI")
        self.assertEqual(data['descricao'], "Departamento de TI")
        self.assertTrue(data['is_ativo'])
```

### 2. Testes de Integração

```python
# tests/app/notion_sync/test_integration.py
class TestNotionIntegration(TransactionTestCase):
    def setUp(self):
        """Configura ambiente de teste"""
        self.notion_service = NotionSyncService()
        self.department = Departamento.objects.create(nome="Test Department")
    
    @patch('notion_sync.services.notion_service.NotionService')
    def test_sync_departamento_success(self, mock_notion):
        """Testa sincronização completa de departamento"""
        # Mock da API do Notion
        mock_page = Mock()
        mock_page.id = "test-page-id"
        mock_notion.return_value.create_page.return_value = mock_page
        
        # Executar sincronização
        sync = DepartamentoSync.objects.create(departamento=self.department)
        result = self.notion_service.sync_departamento(sync)
        
        # Verificar resultado
        self.assertTrue(result)
        self.assertEqual(sync.external_id, "test-page-id")
        self.assertTrue(sync.is_synced)
    
    @patch('notion_sync.services.notion_service.NotionService')
    def test_sync_departamento_failure(self, mock_notion):
        """Testa tratamento de erro na sincronização"""
        # Mock de erro da API
        mock_notion.return_value.create_page.side_effect = Exception("API Error")
        
        # Executar sincronização
        sync = DepartamentoSync.objects.create(departamento=self.department)
        result = self.notion_service.sync_departamento(sync)
        
        # Verificar tratamento de erro
        self.assertFalse(result)
        self.assertIsNone(sync.external_id)
        self.assertGreater(sync.sync_errors, 1)
        self.assertIsNotNone(sync.last_error)
```

---

## 📈 Monitoramento e Métricas

### 1. Métricas Essenciais

```python
# Em analytics.py
def get_sync_metrics() -> dict:
    """Retorna métricas de sincronização"""
    return {
        'total_records': {
            'Contato': ContatoSync.objects.count(),
            'Cliente': ClienteSync.objects.count(),
            'Departamento': DepartamentoSync.objects.count(),
            'Atendente': AtendenteSync.objects.count(),
            'Mensagem': MensagemSync.objects.count(),
            'Atendimento': AtendimentoSync.objects.count(),
        },
        'synced_records': {
            'Contato': ContatoSync.objects.filter(external_id__isnull=False).count(),
            'Cliente': ClienteSync.objects.filter(external_id__isnull=False).count(),
            'Departamento': DepartamentoSync.objects.filter(external_id__isnull=False).count(),
            'Atendente': AtendenteSync.objects.filter(external_id__isnull=False).count(),
            'Mensagem': MensagemSync.objects.filter(external_id__isnull=False).count(),
            'Atendimento': AtendimentoSync.objects.filter(external_id__isnull=False).count(),
        },
        'error_records': {
            'Contato': ContatoSync.objects.filter(sync_errors__gt=0).count(),
            'Cliente': ClienteSync.objects.filter(sync_errors__gt=0).count(),
            'Departamento': DepartamentoSync.objects.filter(sync_errors__gt=0).count(),
            'Atendente': AtendenteSync.objects.filter(sync_errors__gt=0).count(),
            'Mensagem': MensagemSync.objects.filter(sync_errors__gt=0).count(),
            'Atendimento': AtendimentoSync.objects.filter(sync_errors__gt=0).count(),
        },
        'last_24h_syncs': SyncLog.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count(),
    }
```

### 2. Health Checks

```python
# Em health_checks.py
def check_notion_connection() -> dict:
    """Verifica conexão com Notion"""
    try:
        service = NotionSyncService()
        is_connected = service.validate_connection()
        
        return {
            'status': 'healthy' if is_connected else 'unhealthy',
            'message': 'Connected to Notion API' if is_connected else 'Failed to connect to Notion API',
            'timestamp': timezone.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }

def check_pending_syncs() -> dict:
    """Verifica registros pendentes de sincronização"""
    pending_count = (
        DepartamentoSync.objects.pending_sync().count() +
        AtendenteSync.objects.pending_sync().count() +
        MensagemSync.objects.pending_sync().count() +
        AtendimentoSync.objects.pending_sync().count()
    )
    
    return {
        'status': 'warning' if pending_count > 50 else 'healthy',
        'pending_count': pending_count,
        'message': f'{pending_count} records pending sync',
        'timestamp': timezone.now().isoformat()
    }
```

---

## 🔧 Management Commands

### 1. Comandos de Manutenção

```python
# Em management/commands/sync_all.py
class Command(BaseCommand):
    help = 'Sincroniza todos os registros pendentes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            help='Model específico para sincronizar (contato, cliente, departamento, atendente, mensagem, atendimento)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força sincronização de todos os registros'
        )
    
    def handle(self, *args, **options):
        # Implementação do comando
        pass

# Em management/commands/resync_failed.py
class Command(BaseCommand):
    help = 'Reprocessa registros com erro de sincronização'
    
    def handle(self, *args, **options):
        # Implementação do comando
        pass

# Em management/commands/validate_sync.py
class Command(BaseCommand):
    help = 'Valida consistência da sincronização'
    
    def handle(self, *args, **options):
        # Implementação do comando
        pass
```

---

## ✅ Checklist Final

### Antes de ir para produção:

- [ ] Todos os models implementados com managers completos
- [ ] Todos os mappers implementados e testados
- [ ] Serviços Notion funcionando com tratamento de erros
- [ ] Tasks Celery configuradas com retry
- [ ] Webhook endpoint seguro e funcional
- [ ] Admin interface completa e funcional
- [ ] Testes com cobertura ≥ 80%
- [ ] Documentação atualizada
- [ ] Configurações de ambiente documentadas
- [ ] Health checks implementados
- [ ] Métricas e monitoramento funcionando
- [ ] Management commands disponíveis
- [ ] Performance otimizada (índices, queries)
- [ ] Segurança revisada (tokens, webhooks)
- [ ] Backup e recovery plan definido

---

## 📝 Conclusão

Este plano estabelece um caminho claro para finalizar a integração com Notion seguindo o padrão já estabelecido. A abordagem incremental garante que cada fase seja validada antes de prosseguir, minimizando riscos e facilitando debugging.

### Principais Benefícios:

1. **Consistência**: Todos os models seguem o mesmo padrão
2. **Manutenibilidade**: Código modular e bem documentado
3. **Resiliência**: Tratamento robusto de erros e retries
4. **Performance**: Otimizado com índices e assincronia
5. **Monitoramento**: Métricas e health checks completos

### Estimativa Total: **15-20 dias úteis**

Com este plano, a equipe poderá implementar a integração completa de forma organizada e eficiente, mantendo a qualidade e consistência do código.

---

**Próximos Passos:**
1. Aprovação deste plano
2. Atribuição de tarefas por fase
3. Configuração inicial do ambiente
4. Início da Fase 1 (Finalizar Models)

**Contato para dúvidas:** Equipe de Desenvolvimento Smart Core

---