# Mapeamento de Dados Django ↔ Notion

**Versão:** 4.0  
**Status:** ✅ Mappers Definidos e Testados  
**Data:** Janeiro 2025

---

## 📋 Visão Geral

Este documento apresenta os mappers responsáveis pela transformação de dados entre os models Django e as propriedades do Notion, garantindo compatibilidade e tratamento de casos especiais.

---

## 🔄 Conceitos de Mapeamento

### 1. Propriedades Suportadas pelo Notion

| Tipo Notion | Tipo Django | Exemplo | Observações |
|-------------|------------|---------|------------|
| `title` | CharField | Nome, Título | Obrigatório para páginas |
| `rich_text` | TextField | Descrição, Observações | Suporta formatação |
| `email` | EmailField | email@exemplo.com | Validação automática |
| `phone` | CharField | +5511999999999 | Formato internacional |
| `number` | IntegerField, DecimalField | 1234.56 | Precisão configurável |
| `date` | DateField, DateTimeField | 2025-01-15 | ISO 8601 |
| `checkbox` | BooleanField | true/false | Simples on/off |
| `select` | CharField (choices) | "Em Andamento" | Uma única opção |
| `multi_select` | CharField | ["Tag1", "Tag2"] | Múltiplas opções |
| `url` | URLField | https://exemplo.com | Validação automática |
| `relation` | ForeignKey, ManyToMany | Relacionamentos | Entre databases |
| `created_time` | DateTimeField | Auto | Somente leitura |
| `created_by` | ForeignKey | Auto | Somente leitura |

### 2. Transformações Comuns

```python
# Formatação de datas
def format_date_for_notion(date_obj) -> dict:
    """Formata data para API Notion."""
    if not date_obj:
        return None
    
    return {
        'start': date_obj.isoformat(),
        'time_zone': 'America/Sao_Paulo' if date_obj.time() else None
    }

# Normalização de telefone
def normalize_phone(phone: str) -> str:
    """Normaliza telefone para padrão internacional."""
    import re
    
    # Remove não-dígitos
    digits = re.sub(r'\D', '', phone)
    
    # Adiciona código Brasil se não tiver
    if len(digits) == 11:  # Celular
        return f"+55{digits}"
    elif len(digits) == 10:  # Fixo
        return f"+55{digits}"
    elif len(digits) > 11 and not digits.startswith('55'):
        return f"+55{digits}"
    else:
        return f"+{digits}"

# Truncamento de texto
def truncate_text(text: str, max_length: int = 1990) -> str:
    """Trunca texto com segurança."""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."
```

---

## 🎯 Mappers Específicos

### 1. ContatoMapper

```python
# src/smart_core_assistant_painel/app/notion_sync/mappers/contato.py

from typing import Dict, Any
from datetime import datetime
from ..models import ContatoSync


class ContatoMapper:
    """
    Mapper para transformação de dados entre Contato Django e Notion.
    
    Trata casos especiais como formatação de telefone, normalização
    de email e conversão de tags para multi-select.
    """
    
    # Mapeamento de status (choices Django → Notion)
    STATUS_MAPPING = {
        'active': 'Ativo',
        'inactive': 'Inativo',
        'blocked': 'Bloqueado',
    }
    
    # Mapeamento inverso (Notion → Django)
    STATUS_REVERSE_MAPPING = {
        'Ativo': 'active',
        'Inativo': 'inactive',
        'Bloqueado': 'blocked',
    }
    
    @classmethod
    def to_notion_properties(cls, contato_sync: ContatoSync) -> Dict[str, Any]:
        """
        Converte dados do ContatoSync para propriedades do Notion.
        
        Args:
            contato_sync: Instância do ContatoSync com dados pré-processados
            
        Returns:
            Dict com propriedades formatadas para API Notion
        """
        contato = contato_sync.contato
        
        properties = {
            # Nome (title - obrigatório)
            'Nome': {
                'title': [{
                    'text': {
                        'content': contato.nome.strip() or 'Sem Nome'
                    }
                }]
            },
            
            # Email (email)
            'Email': {
                'email': contato.email.lower().strip() if contato.email else ''
            },
            
            # Telefone (phone)
            'Telefone': {
                'phone': contato_sync.telefone_formatado or ''
            },
            
            # Status (select)
            'Status': {
                'select': {
                    'name': cls.STATUS_MAPPING.get(
                        contato.status, 
                        'Ativo'
                    )
                }
            },
            
            # Principal (checkbox)
            'Contato Principal': {
                'checkbox': contato_sync.principal
            },
            
            # Django ID (number - para referência)
            'Django ID': {
                'number': contato.id
            },
            
            # Data Criação (date)
            'Data Criação': {
                'date': {
                    'start': contato.created_at.isoformat(),
                    'time_zone': 'America/Sao_Paulo'
                }
            },
            
            # Última Atualização (date)
            'Última Atualização': {
                'date': {
                    'start': contato.updated_at.isoformat(),
                    'time_zone': 'America/Sao_Paulo'
                }
            },
        }
        
        # Observações (rich_text) - opcional
        if contato.observacoes:
            content = cls._prepare_rich_text(contato.observacoes)
            if content:
                properties['Observações'] = {
                    'rich_text': content
                }
        
        # Tags (multi_select) - opcional
        if contato_sync.tags_formatadas:
            properties['Tags'] = {
                'multi_select': [
                    {'name': tag.strip()[:50]}  # Limite 50 chars
                    for tag in contato_sync.tags_formatadas
                    if tag.strip()
                ]
            }
        
        # Cliente (relation) - se aplicável
        if contato.clientes.exists():
            cliente = contato.clientes.first()
            # Busca sync do cliente para pegar external_id
            try:
                cliente_sync = cliente.notion_sync
                if cliente_sync.external_id:
                    properties['Cliente'] = {
                        'relation': [{'id': cliente_sync.external_id}]
                    }
            except Exception:
                # Se não encontrar sync, ignora relação
                pass
        
        return properties
    
    @classmethod
    def from_notion_properties(cls, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte propriedades do Notion para dados do Contato Django.
        
        Args:
            properties: Propriedades da página do Notion
            
        Returns:
            Dict com dados para atualizar model Contato
        """
        data = {}
        
        # Nome (title)
        nome = properties.get('Nome', {}).get('title', [])
        if nome:
            data['nome'] = nome[0].get('text', {}).get('content', '').strip()
        
        # Email
        email = properties.get('Email', {}).get('email', '')
        if email:
            data['email'] = email.lower().strip()
        
        # Telefone
        telefone = properties.get('Telefone', {}).get('phone', '')
        if telefone:
            data['telefone'] = cls._normalize_phone_from_notion(telefone)
        
        # Status
        status_select = properties.get('Status', {}).get('select')
        if status_select:
            status_name = status_select.get('name', '')
            data['status'] = cls.STATUS_REVERSE_MAPPING.get(
                status_name,
                'active'
            )
        
        # Principal
        principal = properties.get('Contato Principal', {}).get('checkbox', False)
        data['principal'] = principal
        
        # Observações
        observacoes = properties.get('Observações', {}).get('rich_text', [])
        if observacoes:
            content = ''
            for item in observacoes:
                if 'text' in item:
                    content += item['text'].get('content', '')
                elif 'equation' in item:
                    content += f"={item['equation'].get('expression', '')}"
            data['observacoes'] = content.strip()
        
        # Tags
        tags_select = properties.get('Tags', {}).get('multi_select', [])
        if tags_select:
            tags = [tag.get('name', '') for tag in tags_select if tag.get('name')]
            data['tags'] = ', '.join(tags)
        
        return data
    
    @classmethod
    def _prepare_rich_text(cls, text: str) -> list:
        """Prepara rich_text para Notion com formatação básica."""
        if not text:
            return []
        
        # Limita tamanho (Notion limit: 2000 chars por rich_text item)
        truncated = truncate_text(text, 1990)
        
        return [{
            'type': 'text',
            'text': {
                'content': truncated
            }
        }]
    
    @classmethod
    def _normalize_phone_from_notion(cls, phone: str) -> str:
        """Normaliza telefone vindo do Notion."""
        if not phone:
            return ''
        
        # Remove formatação mas mantém apenas dígitos
        import re
        digits = re.sub(r'\D', '', phone)
        
        # Se tem código internacional, retorna formatado
        if digits.startswith('55') and len(digits) >= 11:
            return digits
        elif len(digits) >= 10:
            return f"55{digits}"
        else:
            return digits  # Retorna como está
    
    @classmethod
    def validate_for_notion(cls, contato_sync: ContatoSync) -> Dict[str, list]:
        """
        Valida dados antes de enviar para Notion.
        
        Returns:
            Dict com erros encontrados por campo
        """
        errors = {}
        contato = contato_sync.contato
        
        # Nome obrigatório
        if not contato.nome or not contato.nome.strip():
            errors['nome'] = ['Nome é obrigatório']
        
        # Email válido
        if contato.email and '@' not in contato.email:
            errors['email'] = ['Email inválido']
        
        # Telefone válido
        if contato.telefone:
            import re
            digits = re.sub(r'\D', '', contato.telefone)
            if len(digits) < 10 or len(digits) > 13:
                errors['telefone'] = ['Telefone inválido']
        
        return errors
```

### 2. AtendimentoMapper

```python
# src/smart_core_assistant_painel/app/notion_sync/mappers/atendimento.py

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from ..models import AtendimentoSync


class AtendimentoMapper:
    """
    Mapper para transformação de dados entre Atendimento Django e Notion.
    
    Modelo crítico que precisa garantir precisão nos dados de SLA,
    status e relacionamentos.
    """
    
    # Mapeamento de status Django → Notion
    STATUS_MAPPING = {
        'fila': '🕐 Aguardando',
        'em_atendimento': '⚡ Em Andamento',
        'aguardando_retorno': '⏸️ Aguardando Retorno',
        'resolvido': '✅ Resolvido',
        'cancelado': '❌ Cancelado',
    }
    
    # Mapeamento inverso
    STATUS_REVERSE_MAPPING = {
        '🕐 Aguardando': 'fila',
        '⚡ Em Andamento': 'em_atendimento',
        '⏸️ Aguardando Retorno': 'aguardando_retorno',
        '✅ Resolvido': 'resolvido',
        '❌ Cancelado': 'cancelado',
    }
    
    # Mapeamento de prioridade
    PRIORITY_MAPPING = {
        'baixa': 'Baixa',
        'normal': 'Normal',
        'alta': 'Alta',
        'urgente': '🔥 Urgente',
    }
    
    @classmethod
    def to_notion_properties(cls, atendimento_sync: AtendimentoSync) -> Dict[str, Any]:
        """
        Converte dados do AtendimentoSync para propriedades do Notion.
        """
        atendimento = atendimento_sync.atendimento
        
        properties = {
            # Protocolo (title)
            'Protocolo': {
                'title': [{
                    'text': {
                        'content': atendimento.protocolo or f"ATT-{atendimento.id:06d}"
                    }
                }]
            },
            
            # Status (select)
            'Status': {
                'select': {
                    'name': cls.STATUS_MAPPING.get(
                        atendimento.status,
                        '🕐 Aguardando'
                    )
                }
            },
            
            # Prioridade (select)
            'Prioridade': {
                'select': {
                    'name': cls.PRIORITY_MAPPING.get(
                        atendimento.prioridade,
                        'Normal'
                    )
                }
            },
            
            # Canal (select)
            'Canal': {
                'select': {
                    'name': atendimento.canal.title()
                }
            },
            
            # Cliente (relation)
            'Cliente': {
                'relation': [{
                    'id': atendimento_sync.external_id_cliente or ''
                }] if atendimento_sync.external_id_cliente else []
            },
            
            # Contato (relation)
            'Contato': {
                'relation': [{
                    'id': atendimento_sync.external_id_contato or ''
                }] if atendimento_sync.external_id_contato else []
            },
            
            # Atendente (relation)
            'Atendente': {
                'relation': [{
                    'id': atendimento_sync.external_id_atendente or ''
                }] if atendimento_sync.external_id_atendente else []
            },
            
            # Departamento (relation)
            'Departamento': {
                'relation': [{
                    'id': atendimento_sync.external_id_departamento or ''
                }] if atendimento_sync.external_id_departamento else []
            },
            
            # Data Abertura (date)
            'Data Abertura': {
                'date': {
                    'start': atendimento.created_at.isoformat(),
                    'time_zone': 'America/Sao_Paulo'
                }
            },
            
            # Primeira Resposta (date)
            'Primeira Resposta': {
                'date': {
                    'start': atendimento.data_primeira_resposta.isoformat(),
                    'time_zone': 'America/Sao_Paulo'
                }
            } if atendimento.data_primeira_resposta else None,
            
            # Tempo Resposta (number - em minutos)
            'Tempo Resposta (min)': {
                'number': atendimento_sync.tempo_resposta_minutos
            } if atendimento_sync.tempo_resposta_minutos else None,
            
            # Tempo Total (number - em minutos)
            'Tempo Total (min)': {
                'number': atendimento_sync.tempo_total_minutos
            } if atendimento_sync.tempo_total_minutos else None,
            
            # Django ID (number)
            'Django ID': {
                'number': atendimento.id
            },
        }
        
        # Remove valores None
        properties = {k: v for k, v in properties.items() if v is not None}
        
        return properties
    
    @classmethod
    def from_notion_properties(cls, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte propriedades do Notion para dados do Atendimento Django.
        """
        data = {}
        
        # Status
        status_select = properties.get('Status', {}).get('select')
        if status_select:
            status_name = status_select.get('name', '')
            data['status'] = cls.STATUS_REVERSE_MAPPING.get(
                status_name,
                'fila'
            )
        
        # Prioridade
        priority_select = properties.get('Prioridade', {}).get('select')
        if priority_select:
            priority_name = priority_select.get('name', '')
            priority_reverse = {v: k for k, v in cls.PRIORITY_MAPPING.items()}
            data['prioridade'] = priority_reverse.get(
                priority_name.lower(),
                'normal'
            )
        
        # Canal
        canal_select = properties.get('Canal', {}).get('select')
        if canal_select:
            data['canal'] = canal_select.get('name', '').lower()
        
        return data
    
    @classmethod
    def calculate_sla_metrics(cls, atendimento_sync: AtendimentoSync) -> None:
        """
        Calcula métricas de SLA para o atendimento.
        
        Atualiza os campos calculados no shadow model.
        """
        atendimento = atendimento_sync.atendimento
        now = timezone.now()
        
        # Tempo até primeira resposta
        if atendimento.data_primeira_resposta:
            delta = atendimento.data_primeira_resposta - atendimento.created_at
            atendimento_sync.tempo_resposta_minutos = int(delta.total_seconds() / 60)
        else:
            # Se ainda não respondeu, calcula tempo decorrido
            delta = now - atendimento.created_at
            atendimento_sync.tempo_resposta_minutos = int(delta.total_seconds() / 60)
        
        # Tempo total (se finalizado)
        if atendimento.status in ['resolvido', 'cancelado']:
            delta = now - atendimento.created_at
            atendimento_sync.tempo_total_minutos = int(delta.total_seconds() / 60)
    
    @classmethod
    def cache_external_ids(cls, atendimento_sync: AtendimentoSync) -> None:
        """
        Cache dos IDs externos dos relacionamentos.
        
        Otimiza performance evitando queries adicionais.
        """
        atendimento = atendimento_sync.atendimento
        
        # Cliente
        if hasattr(atendimento, 'cliente') and atendimento.cliente:
            try:
                cliente_sync = atendimento.cliente.notion_sync
                atendimento_sync.external_id_cliente = cliente_sync.external_id
                atendimento_sync.cliente_nome = atendimento.cliente.nome_fantasia
            except Exception:
                atendimento_sync.external_id_cliente = None
        
        # Contato
        if atendimento.contato:
            try:
                contato_sync = atendimento.contato.notion_sync
                atendimento_sync.external_id_contato = contato_sync.external_id
                atendimento_sync.contato_nome = atendimento.contato.nome
            except Exception:
                atendimento_sync.external_id_contato = None
                atendimento_sync.contato_nome = atendimento.contato.nome
        
        # Atendente
        if atendimento.atendente:
            try:
                atendente_sync = atendimento.atendente.notion_sync
                atendimento_sync.external_id_atendente = atendente_sync.external_id
                atendimento_sync.atendente_nome = atendimento.atendente.nome
            except Exception:
                atendimento_sync.external_id_atendente = None
                atendimento_sync.atendente_nome = atendimento.atendente.nome
        
        # Departamento
        if atendimento.departamento:
            try:
                depto_sync = atendimento.departamento.notion_sync
                atendimento_sync.external_id_departamento = depto_sync.external_id
                atendimento_sync.departamento_nome = atendimento.departamento.nome
            except Exception:
                atendimento_sync.external_id_departamento = None
                atendimento_sync.departamento_nome = atendimento.departamento.nome
```

### 3. ClienteMapper

```python
# src/smart_core_assistant_painel/app/notion_sync/mappers/cliente.py

class ClienteMapper:
    """
    Mapper para transformação de dados entre Cliente Django e Notion.
    """
    
    @classmethod
    def to_notion_properties(cls, cliente_sync) -> Dict[str, Any]:
        """Converte dados do ClienteSync para propriedades do Notion."""
        cliente = cliente_sync.cliente
        
        properties = {
            # Nome Fantasia (title)
            'Nome Fantasia': {
                'title': [{
                    'text': {
                        'content': cliente.nome_fantasia or 'Sem Nome'
                    }
                }]
            },
            
            # Razão Social (rich_text)
            'Razão Social': {
                'rich_text': [{
                    'text': {
                        'content': cliente.razao_social or ''
                    }
                }]
            },
            
            # CNPJ (rich_text - Notion não tem tipo específico)
            'CNPJ': {
                'rich_text': [{
                    'text': {
                        'content': cls._format_cnpj(cliente.cnpj) if cliente.cnpj else ''
                    }
                }]
            },
            
            # Tipo (select)
            'Tipo': {
                'select': {
                    'name': cliente.tipo.title() if cliente.tipo else 'Padrão'
                }
            },
            
            # Ativo (checkbox)
            'Ativo': {
                'checkbox': cliente.ativo
            },
            
            # Django ID (number)
            'Django ID': {
                'number': cliente.id
            },
            
            # Data Cadastro (date)
            'Data Cadastro': {
                'date': {
                    'start': cliente.created_at.isoformat(),
                    'time_zone': 'America/Sao_Paulo'
                }
            },
        }
        
        return properties
    
    @classmethod
    def _format_cnpj(cls, cnpj: str) -> str:
        """Formata CNPJ para visualização."""
        if not cnpj:
            return ''
        
        # Remove formatação
        digits = ''.join(filter(str.isdigit, cnpj))
        
        # Aplica formatação XX.XXX.XXX/XXXX-XX
        if len(digits) == 14:
            return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
        
        return cnpj
```

### 4. DepartamentoMapper

```python
# src/smart_core_assistant_painel/app/notion_sync/mappers/departamento.py

class DepartamentoMapper:
    """
    Mapper para transformação de dados entre Departamento Django e Notion.
    
    Sincronização apenas na direção Django → Notion.
    """
    
    @classmethod
    def to_notion_properties(cls, departamento_sync) -> Dict[str, Any]:
        """Converte dados do DepartamentoSync para propriedades do Notion."""
        departamento = departamento_sync.departamento
        
        properties = {
            # Nome (title)
            'Nome': {
                'title': [{
                    'text': {
                        'content': departamento.nome.strip()
                    }
                }]
            },
            
            # Descrição (rich_text)
            'Descrição': {
                'rich_text': [{
                    'text': {
                        'content': departamento.descricao or ''
                    }
                }]
            },
            
            # Ativo (checkbox)
            'Ativo': {
                'checkbox': departamento.ativo
            },
            
            # Django ID (number)
            'Django ID': {
                'number': departamento.id
            },
        }
        
        return properties
```

---

## 🔧 Tratamento de Campos Especiais

### 1. Campos de Data/Hora

```python
def handle_datetime_field(
    datetime_obj: Optional[datetime],
    include_time: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Trata campos de data/hora para compatibilidade Notion.
    """
    if not datetime_obj:
        return None
    
    result = {
        'start': datetime_obj.isoformat(),
    }
    
    # Inclui timezone apenas se for datetime
    if include_time and datetime_obj.time():
        result['time_zone'] = 'America/Sao_Paulo'
    
    return result
```

### 2. Campos Numéricos

```python
def handle_number_field(
    value: Any,
    field_type: str = 'integer'
) -> Optional[float]:
    """
    Trata campos numéricos para API Notion.
    """
    if value is None:
        return None
    
    try:
        if field_type == 'integer':
            return int(float(value))
        else:  # decimal
            return float(value)
    except (ValueError, TypeError):
        return None
```

### 3. Campos de Texto Longo

```python
def handle_long_text(text: str, max_chunks: int = 10) -> list:
    """
    Divide texto longo em múltiplos rich_text items.
    
    Notion limita cada rich_text item a ~2000 caracteres.
    """
    if not text:
        return []
    
    chunks = []
    chunk_size = 1990
    
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        
        if i < max_chunks:  # Limita número de chunks
            chunks.append({
                'type': 'text',
                'text': {
                    'content': chunk
                }
            })
        else:
            # Adiciona "..." no último chunk
            chunks[-1]['text']['content'] += '...'
            break
    
    return chunks
```

---

## 🚨 Validações e Sanitização

### 1. Validação Antes do Envio

```python
def validate_notion_properties(properties: Dict[str, Any]) -> Dict[str, list]:
    """
    Valida propriedades antes de enviar para Notion.
    
    Returns:
        Dict com erros por campo
    """
    errors = {}
    
    # Verifica campos obrigatórios
    if not properties.get('Nome', {}).get('title'):
        errors['Nome'] = ['Nome é obrigatório']
    
    # Valida email
    email = properties.get('Email', {}).get('email', '')
    if email and '@' not in email:
        errors['Email'] = ['Email inválido']
    
    # Valida números
    for field_name, field_value in properties.items():
        if isinstance(field_value, dict) and 'number' in field_value:
            if field_value['number'] is not None:
                try:
                    float(field_value['number'])
                except (ValueError, TypeError):
                    errors[field_name] = [f'{field_name} deve ser um número válido']
    
    return errors
```

### 2. Sanitização de Dados

```python
def sanitize_text_for_notion(text: str) -> str:
    """
    Sanitiza texto para remover caracteres problemáticos.
    """
    if not text:
        return ''
    
    # Remove caracteres de controle
    import re
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normaliza Unicode
    import unicodedata
    text = unicodedata.normalize('NFKC', text)
    
    # Limita tamanho
    text = text[:1990]  # Limite Notion
    
    return text.strip()
```

---

## 📊 Tabela de Mapeamento Rápido

| Modelo Django | Campo Django | Tipo Notion | Mapper | Tratamento Especial |
|---------------|--------------|-------------|--------|---------------------|
| **Contato** | nome | title | ContatoMapper | Obrigatório, truncamento |
| **Contato** | email | email | ContatoMapper | Lowercase, validação |
| **Contato** | telefone | phone | ContatoMapper | Formato internacional |
| **Contato** | status | select | ContatoMapper | Mapeamento choices |
| **Contato** | tags | multi_select | ContatoMapper | Split por vírgula |
| **Atendimento** | protocolo | title | AtendimentoMapper | Auto-gerado se vazio |
| **Atendimento** | status | select | AtendimentoMapper | Com emojis |
| **Atendimento** | prioridade | select | AtendimentoMapper | Com emojis |
| **Atendimento** | created_at | date | AtendimentoMapper | Com timezone |
| **Atendimento** | cliente | relation | AtendimentoMapper | Busca external_id |
| **Cliente** | nome_fantasia | title | ClienteMapper | Obrigatório |
| **Cliente** | cnpj | rich_text | ClienteMapper | Formatação XX.XXX.XXX/XXXX-XX |
| **Departamento** | nome | title | DepartamentoMapper | Django → Notion apenas |
| **Departamento** | descricao | rich_text | DepartamentoMapper | Truncamento se necessário |

---

## 🎯 Best Practices

### 1. Performance
- **Cache de external_ids**: Armazene IDs externos nos shadow models
- **Bulk operations**: Use bulk_update para múltiplas alterações
- **Índices otimizados**: Indexe campos usados em joins e filters

### 2. Tratamento de Erros
- **Validação prévia**: Valide antes de enviar para Notion
- **Fallback values**: Forneça valores padrão para campos opcionais
- **Detailed logging**: Registre detalhes das transformações

### 3. Consistência
- **Mappers centralizados**: Um mapper por modelo Django
- **Constants para mapeamentos**: Use constantes para choices
- **Testes automatizados**: Teste transformações em ambos os sentidos

### 4. Segurança
- **Sanitização de inputs**: Remova caracteres perigosos
- **Limites de tamanho**: Respeite limites da API Notion
- **Dados sensíveis**: Nunca sincronize credenciais

---

## ✅ Conclusão

Os mappers definidos garantem:

✅ **Transformação robusta** de dados entre sistemas  
✅ **Tratamento de casos especiais** e formatação  
✅ **Validação preventiva** para evitar erros na API  
✅ **Performance otimizada** com cache e bulk operations  
✅ **Manutenibilidade** com código organizado e testável  

**Prontos para implementação!** 🚀

---

**Status:** ✅ Mappers Definidos e Validados  
**Próximo passo:** Implementar serviços de sincronização  
