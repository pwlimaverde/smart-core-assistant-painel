# Planejamento Técnico para Integração com ClickUp

## Visão Geral

Este documento detalha os aspectos técnicos da implementação da integração entre o sistema de atendimento e o ClickUp, incluindo arquitetura, fluxo de dados, autenticação e considerações de desenvolvimento.

## Arquitetura da Integração

### Componentes Principais

1. **Módulo de Sincronização** (`clickup_sync`)
   - Responsável pela comunicação com a API do ClickUp
   - Implementa lógica de sincronização bidirecional
   - Gerencia transformação de dados entre os sistemas

2. **Sistema de Eventos**
   - Utiliza sinais do Django para detectar mudanças nos modelos
   - Dispara processos de sincronização assíncronos
   - Implementa fila de tarefas para processamento em background

3. **Mapeamento de Campos**
   - Configuração flexível dos campos personalizados
   - Sistema de templates para transformação de dados
   - Suporte a validações cruzadas

### Fluxo de Arquitetura

```
Sistema de Atendimento
   ├── Models (Django)
   ├── Signals (Eventos)
   └── Services (Lógica de Negócio)
           ↓
Módulo de Sincronização
   ├── Transformers (Conversão de Dados)
   ├── API Client (Comunicação ClickUp)
   └── Queue Manager (Fila de Processamento)
           ↓
ClickUp API
   ├── Tasks (Tarefas)
   ├── Custom Fields (Campos Personalizados)
   └── Webhooks (Notificações)
```

## Configuração e Autenticação

### Variáveis de Ambiente

```python
# .env.example
CLICKUP_API_TOKEN=seu_token_aqui
CLICKUP_TEAM_ID=id_da_equipe
CLICKUP_SPACE_ID=id_do_space_central
CLICKUP_WEBHOOK_SECRET=seu_secreto_webhook
CLICKUP_SYNC_ENABLED=true
CLICKUP_BATCH_SIZE=50
CLICKUP_RATE_LIMIT=100
```

### Configurações do Django

```python
# settings.py
CLICKUP_CONFIG = {
    "api_token": env("CLICKUP_API_TOKEN"),
    "team_id": env("CLICKUP_TEAM_ID"),
    "space_id": env("CLICKUP_SPACE_ID"),
    "webhook_secret": env("CLICKUP_WEBHOOK_SECRET"),
    "batch_size": int(env("CLICKUP_BATCH_SIZE", 50)),
    "rate_limit": int(env("CLICKUP_RATE_LIMIT", 100)),
    "enabled": env.bool("CLICKUP_SYNC_ENABLED", False),
}
```

## Estrutura do Módulo de Sincronização

```
src/smart_core_assistant_painel/app/clickup_sync/
├── __init__.py
├── models.py
├── admin.py
├── apps.py
├── management/
│   └── commands/
│       ├── setup_clickup.py
│       ├── sync_initial_data.py
│       └── test_connection.py
├── migrations/
├── services/
│   ├── __init__.py
│   ├── api_client.py
│   ├── sync_manager.py
│   ├── field_mapper.py
│   └── webhook_handler.py
├── transformers/
│   ├── __init__.py
│   ├── atendimento_to_task.py
│   └── task_to_atendimento.py
├── utils/
│   ├── __init__.py
│   ├── rate_limiter.py
│   └── retry_handler.py
├── tests/
│   ├── test_api_client.py
│   ├── test_transformers.py
│   └── test_sync_manager.py
└── urls.py
```

## Implementação dos Componentes

### 1. Cliente de API do ClickUp

```python
# services/api_client.py
import requests
from typing import Dict, List, Optional, Any
from django.conf import settings
from .utils.rate_limiter import RateLimiter

class ClickUpAPIClient:
    def __init__(self):
        self.api_token = settings.CLICKUP_CONFIG["api_token"]
        self.team_id = settings.CLICKUP_CONFIG["team_id"]
        self.base_url = "https://api.clickup.com/api/v2"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        })
        self.rate_limiter = RateLimiter(limit=settings.CLICKUP_CONFIG["rate_limit"])
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Executa uma requisição à API com controle de rate limiting."""
        self.rate_limiter.wait()
        response = self.session.request(
            method, 
            f"{self.base_url}/{endpoint.lstrip('/')}", 
            **kwargs
        )
        response.raise_for_status()
        return response.json()
    
    def get_team_folders(self) -> List[Dict]:
        """Obtém as pastas do time no ClickUp."""
        return self._request("GET", f"team/{self.team_id}/folder").get("folders", [])
    
    def get_folder_lists(self, folder_id: str) -> List[Dict]:
        """Obtém as listas de uma pasta."""
        return self._request("GET", f"folder/{folder_id}/list").get("lists", [])
    
    def create_task(self, list_id: str, task_data: Dict) -> Dict:
        """Cria uma nova tarefa no ClickUp."""
        return self._request("POST", f"list/{list_id}/task", json=task_data)
    
    def update_task(self, task_id: str, task_data: Dict) -> Dict:
        """Atualiza uma tarefa existente."""
        return self._request("PUT", f"task/{task_id}", json=task_data)
    
    def get_task(self, task_id: str) -> Dict:
        """Obtém detalhes de uma tarefa."""
        return self._request("GET", f"task/{task_id}")
    
    def get_list_custom_fields(self, list_id: str) -> List[Dict]:
        """Obtém os campos personalizados de uma lista."""
        return self._request("GET", f"list/{list_id}/field").get("fields", [])
    
    def create_custom_field(self, list_id: str, field_data: Dict) -> Dict:
        """Cria um campo personalizado em uma lista."""
        return self._request("POST", f"list/{list_id}/field", json=field_data)
    
    def create_webhook(self, team_id: str, webhook_data: Dict) -> Dict:
        """Cria um webhook para notificações."""
        return self._request("POST", f"team/{team_id}/webhook", json=webhook_data)
```

### 2. Mapeador de Campos

```python
# services/field_mapper.py
from typing import Dict, Any, Optional
from django.conf import settings

class ClickUpFieldMapper:
    """Responsável pelo mapeamento entre campos do sistema e do ClickUp."""
    
    def __init__(self, list_id: str):
        self.list_id = list_id
        self.field_mappings = self._load_field_mappings()
    
    def _load_field_mappings(self) -> Dict[str, str]:
        """Carrega o mapeamento de campos do banco de dados ou configuração."""
        # Implementar busca das configurações salvas
        return {
            # Mapeamento: campo_sistema -> id_campo_clickup
            "departamento": "dep_abc123",
            "prioridade": "prio_def456",
            "canal": "can_ghi789",
            "assunto": "ass_jkl012",
            "data_inicio": "ini_mno345",
            "atendente_humano": "att_pqr678",
            "avaliacao": "ava_stu901",
            "feedback": "feed_vwx234",
            # ... outros mapeamentos
        }
    
    def map_to_clickup(self, atendimento_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma dados do atendimento para formato do ClickUp."""
        clickup_data = {
            "name": f"#{atendimento_data.get('id')} - {atendimento_data.get('assunto', 'Sem assunto')}",
            "description": self._generate_description(atendimento_data),
        }
        
        # Mapeamento de campos personalizados
        custom_fields = []
        
        # Departamento
        if "departamento" in atendimento_data and atendimento_data["departamento"]:
            dept_id = self._get_department_option_id(atendimento_data["departamento"])
            custom_fields.append({
                "id": self.field_mappings.get("departamento"),
                "value": dept_id
            })
        
        # Prioridade
        if "prioridade" in atendimento_data:
            prio_id = self._get_priority_option_id(atendimento_data["prioridade"])
            custom_fields.append({
                "id": self.field_mappings.get("prioridade"),
                "value": prio_id
            })
        
        # Canal
        if "canal" in atendimento_data:
            canal_ids = self._get_canal_label_ids(atendimento_data["canal"])
            custom_fields.append({
                "id": self.field_mappings.get("canal"),
                "value": canal_ids
            })
        
        # Data de início
        if "data_inicio" in atendimento_data:
            timestamp = int(atendimento_data["data_inicio"].timestamp() * 1000)
            custom_fields.append({
                "id": self.field_mappings.get("data_inicio"),
                "value": timestamp
            })
        
        # Adicionar todos os campos mapeados
        clickup_data["custom_fields"] = custom_fields
        
        # Atribuição a usuários
        if "atendente_humano_id" in atendimento_data:
            clickup_data["assignees"] = [atendimento_data["atendente_humano_id"]]
        
        return clickup_data
    
    def map_from_clickup(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma dados do ClickUp para formato do sistema."""
        atendimento_data = {
            "id": task_data.get("custom_id"),
            "assunto": task_data.get("name", "").replace("#", "").split(" - ", 1)[-1],
        }
        
        # Extrair dados dos campos personalizados
        for field in task_data.get("custom_fields", []):
            field_id = field.get("id")
            
            if field_id == self.field_mappings.get("departamento"):
                atendimento_data["departamento"] = self._get_department_name_from_option(field.get("value"))
            
            elif field_id == self.field_mappings.get("prioridade"):
                atendimento_data["prioridade"] = self._get_priority_name_from_option(field.get("value"))
            
            elif field_id == self.field_mappings.get("canal"):
                atendimento_data["canal"] = self._get_canal_names_from_labels(field.get("value", []))
            
            elif field_id == self.field_mappings.get("data_inicio"):
                timestamp = field.get("value")
                if timestamp:
                    from datetime import datetime
                    atendimento_data["data_inicio"] = datetime.fromtimestamp(timestamp / 1000)
            
            elif field_id == self.field_mappings.get("atendente_humano"):
                atendimento_data["atendente_humano_id"] = field.get("value")[0] if field.get("value") else None
            
            elif field_id == self.field_mappings.get("avaliacao"):
                atendimento_data["avaliacao"] = field.get("value")
            
            elif field_id == self.field_mappings.get("feedback"):
                atendimento_data["feedback"] = field.get("value")
        
        # Status da tarefa para etapa_atual
        if "status" in task_data:
            atendimento_data["etapa_atual"] = task_data["status"]["status"]
        
        # Usuários atribuídos
        if "assignees" in task_data and task_data["assignees"]:
            atendimento_data["atendente_humano_id"] = task_data["assignees"][0]["id"]
        
        return atendimento_data
    
    def _generate_description(self, atendimento_data: Dict[str, Any]) -> str:
        """Gera a descrição da tarefa no ClickUp."""
        contato_info = atendimento_data.get("contato_info", {})
        descricao = f"**Contato:** {contato_info.get('nome_contato', 'N/A')} ({contato_info.get('telefone', 'N/A')})\n"
        
        if "mensagens_recentes" in atendimento_data:
            descricao += "\n**Últimas Mensagens:**\n"
            for msg in atendimento_data["mensagens_recentes"][-3:]:  # Últimas 3 mensagens
                remetente = "Cliente" if msg.get("remetente") == "CONTATO" else "Atendente"
                descricao += f"- {remetente}: {msg.get('conteudo', '')[:100]}...\n"
        
        return descricao
    
    def _get_department_option_id(self, dept_name: str) -> str:
        """Retorna o ID da opção de departamento no campo dropdown."""
        dept_options = {
            "Vendas": "dept_vendas",
            "Suporte Técnico": "dept_suporte", 
            "Financeiro": "dept_financeiro",
            "Outros": "dept_outros"
        }
        return dept_options.get(dept_name, "dept_outros")
    
    def _get_priority_option_id(self, prio_name: str) -> str:
        """Retorna o ID da opção de prioridade no campo dropdown."""
        prio_options = {
            "baixa": "prio_baixa",
            "normal": "prio_normal",
            "alta": "prio_alta",
            "urgente": "prio_urgente"
        }
        return prio_options.get(prio_name.lower(), "prio_normal")
    
    def _get_canal_label_ids(self, canal_name: str) -> List[str]:
        """Retorna os IDs das labels de canal."""
        canal_mapping = {
            "whatsapp": ["canal_whatsapp"],
            "email": ["canal_email"],
            "telefone": ["canal_telefone"],
            "web": ["canal_web"]
        }
        return canal_mapping.get(canal_name.lower(), [])
```

### 3. Gerenciador de Sincronização

```python
# services/sync_manager.py
import logging
from typing import Optional, Dict, Any, List
from django.db import transaction
from django.utils import timezone
from .api_client import ClickUpAPIClient
from .field_mapper import ClickUpFieldMapper
from ..models import Atendimento, SyncLog

logger = logging.getLogger(__name__)

class ClickUpSyncManager:
    """Gerencia o processo de sincronização entre atendimentos e tasks do ClickUp."""
    
    def __init__(self):
        self.api_client = ClickUpAPIClient()
        self.setup_complete = False
    
    def setup_initial_structure(self) -> Dict[str, Any]:
        """Configura a estrutura inicial no ClickUp (spaces, folders, lists)."""
        try:
            # Criar ou obter pasta principal
            folders = self.api_client.get_team_folders()
            central_folder = next(
                (f for f in folders if f.get("name") == "Central de Atendimento"), 
                None
            )
            
            if not central_folder:
                central_folder = self.api_client.create_folder(
                    self.api_client.team_id,
                    {"name": "Central de Atendimento"}
                )
            
            # Criar listas para cada departamento
            from operacional.models import Departamento
            list_ids = {}
            
            for dept in Departamento.objects.filter(ativo=True):
                lists = self.api_client.get_folder_lists(central_folder["id"])
                dept_list = next(
                    (l for l in lists if l.get("name") == dept.nome),
                    None
                )
                
                if not dept_list:
                    dept_list = self.api_client.create_list(
                        central_folder["id"],
                        {"name": dept.nome}
                    )
                
                list_ids[dept.slug] = dept_list["id"]
                
                # Criar campos personalizados
                self._create_custom_fields(dept_list["id"])
            
            self.setup_complete = True
            return {"status": "success", "list_ids": list_ids}
            
        except Exception as e:
            logger.error(f"Erro ao configurar estrutura inicial: {e}")
            return {"status": "error", "message": str(e)}
    
    def _create_custom_fields(self, list_id: str) -> None:
        """Cria os campos personalizados necessários na lista."""
        fields_to_create = [
            {
                "name": "Departamento",
                "type": "drop_down",
                "type_config": {
                    "options": [
                        {"id": "dept_vendas", "name": "Vendas", "color": "#00BCD4"},
                        {"id": "dept_suporte", "name": "Suporte Técnico", "color": "#FF9800"},
                        {"id": "dept_financeiro", "name": "Financeiro", "color": "#4CAF50"},
                        {"id": "dept_outros", "name": "Outros", "color": "#9E9E9E"}
                    ]
                }
            },
            {
                "name": "Prioridade",
                "type": "drop_down",
                "type_config": {
                    "default": 1,
                    "options": [
                        {"id": "prio_baixa", "name": "Baixa", "color": "#4CAF50"},
                        {"id": "prio_normal", "name": "Normal", "color": "#2196F3"},
                        {"id": "prio_alta", "name": "Alta", "color": "#FF9800"},
                        {"id": "prio_urgente", "name": "Urgente", "color": "#F44336"}
                    ]
                }
            },
            {
                "name": "Canal de Origem",
                "type": "labels",
                "type_config": {
                    "options": [
                        {"id": "canal_whatsapp", "label": "WhatsApp", "color": "#25D366"},
                        {"id": "canal_email", "label": "E-mail", "color": "#7289DA"},
                        {"id": "canal_telefone", "label": "Telefone", "color": "#37474F"},
                        {"id": "canal_web", "label": "Website", "color": "#2196F3"}
                    ]
                }
            },
            {
                "name": "Início do Atendimento",
                "type": "date"
            },
            {
                "name": "Última Interação",
                "type": "date"
            },
            {
                "name": "Avaliação do Cliente",
                "type": "emoji",
                "type_config": {
                    "code_point": "2b50",
                    "count": 5
                }
            }
        ]
        
        for field_data in fields_to_create:
            try:
                self.api_client.create_custom_field(list_id, field_data)
            except Exception as e:
                logger.warning(f"Campo {field_data['name']} pode já existir: {e}")
    
    def sync_atendimento_to_clickup(self, atendimento_id: int) -> Optional[Dict[str, Any]]:
        """Sincroniza um atendimento do sistema para o ClickUp."""
        try:
            atendimento = Atendimento.objects.select_related(
                'contato', 'departamento', 'atendente_humano'
            ).get(id=atendimento_id)
            
            # Obter o ID da lista correspondente ao departamento
            list_id = self._get_list_id_for_department(atendimento.departamento)
            if not list_id:
                logger.error(f"Departamento {atendimento.departamento.nome} não possui lista no ClickUp")
                return None
            
            # Preparar dados para o ClickUp
            mapper = ClickUpFieldMapper(list_id)
            atendimento_data = self._extract_atendimento_data(atendimento)
            task_data = mapper.map_to_clickup(atendimento_data)
            
            # Verificar se já existe uma task para este atendimento
            clickup_task_id = getattr(atendimento, 'clickup_task_id', None)
            
            if clickup_task_id:
                # Atualizar task existente
                result = self.api_client.update_task(clickup_task_id, task_data)
                action = "updated"
            else:
                # Criar nova task
                result = self.api_client.create_task(list_id, task_data)
                clickup_task_id = result["id"]
                atendimento.clickup_task_id = clickup_task_id
                atendimento.save(update_fields=['clickup_task_id'])
                action = "created"
            
            # Registrar log de sincronização
            SyncLog.objects.create(
                atendimento=atendimento,
                action=action,
                clickup_task_id=clickup_task_id,
                success=True,
                timestamp=timezone.now()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar atendimento {atendimento_id}: {e}")
            
            # Registrar erro no log
            SyncLog.objects.create(
                atendimento_id=atendimento_id,
                action="sync_error",
                success=False,
                error_message=str(e),
                timestamp=timezone.now()
            )
            
            return None
    
    def sync_clickup_task_to_atendimento(self, task_id: str) -> bool:
        """Sincroniza uma task do ClickUp para o sistema."""
        try:
            # Obter dados da task
            task_data = self.api_client.get_task(task_id)
            
            # Encontrar atendimento correspondente pelo custom_id
            custom_id = task_data.get("custom_id")
            if not custom_id:
                logger.error(f"Task {task_id} não possui custom_id")
                return False
            
            # Buscar atendimento
            try:
                atendimento = Atendimento.objects.get(id=int(custom_id))
            except Atendimento.DoesNotExist:
                logger.error(f"Atendimento {custom_id} não encontrado")
                return False
            
            # Mapear dados do ClickUp para o formato do sistema
            list_id = task_data["list"]["id"]
            mapper = ClickUpFieldMapper(list_id)
            atendimento_data = mapper.map_from_clickup(task_data)
            
            # Atualizar atendimento
            self._update_atendimento_from_clickup_data(atendimento, atendimento_data)
            
            # Registrar log
            SyncLog.objects.create(
                atendimento=atendimento,
                action="updated_from_clickup",
                clickup_task_id=task_id,
                success=True,
                timestamp=timezone.now()
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar task {task_id}: {e}")
            return False
    
    def _get_list_id_for_department(self, departamento) -> Optional[str]:
        """Retorna o ID da lista do ClickUp correspondente ao departamento."""
        if not departamento:
            return None
            
        # Implementar cache de IDs de lista para otimização
        # Por enquanto, busca direta na API
        folders = self.api_client.get_team_folders()
        central_folder = next(
            (f for f in folders if f.get("name") == "Central de Atendimento"), 
            None
        )
        
        if not central_folder:
            return None
            
        lists = self.api_client.get_folder_lists(central_folder["id"])
        dept_list = next(
            (l for l in lists if l.get("name") == departamento.nome),
            None
        )
        
        return dept_list["id"] if dept_list else None
    
    def _extract_atendimento_data(self, atendimento) -> Dict[str, Any]:
        """Extrai dados relevantes do objeto de atendimento."""
        data = {
            "id": atendimento.id,
            "assunto": atendimento.assunto,
            "prioridade": atendimento.prioridade,
            "canal": atendimento.canal,
            "data_inicio": atendimento.data_inicio,
            "data_fim": atendimento.data_fim,
            "atendente_humano_id": (
                atendimento.atendente_humano.usuario.id 
                if atendimento.atendente_humano and atendimento.atendente_humano.usuario 
                else None
            ),
            "avaliacao": atendimento.avaliacao,
            "feedback": atendimento.feedback,
        }
        
        if atendimento.departamento:
            data["departamento"] = atendimento.departamento.nome
        
        if atendimento.contato:
            data["contato_info"] = {
                "id": atendimento.contato.id,
                "nome_contato": atendimento.contato.nome_contato,
                "telefone": atendimento.contato.telefone,
            }
        
        # Obter mensagens recentes
        mensagens = atendimento.mensagens.order_by("-timestamp")[:3]
        data["mensagens_recentes"] = [
            {
                "conteudo": msg.conteudo,
                "remetente": msg.remetente,
                "timestamp": msg.timestamp,
            }
            for msg in mensagens
        ]
        
        return data
    
    def _update_atendimento_from_clickup_data(self, atendimento, atendimento_data):
        """Atualiza o objeto de atendimento com dados do ClickUp."""
        from operacional.models import Atendente
        
        if "departamento" in atendimento_data:
            # Mapear nome do departamento para objeto
            from operacional.models import Departamento
            try:
                departamento = Departamento.objects.get(nome=atendimento_data["departamento"])
                atendimento.departamento = departamento
            except Departamento.DoesNotExist:
                pass
        
        if "prioridade" in atendimento_data:
            atendimento.prioridade = atendimento_data["prioridade"]
        
        if "atendente_humano_id" in atendimento_data:
            try:
                atendente = Atendente.objects.get(usuario__id=atendimento_data["atendente_humano_id"])
                atendimento.atendente_humano = atendente
            except Atendente.DoesNotExist:
                pass
        
        if "avaliacao" in atendimento_data:
            atendimento.avaliacao = atendimento_data["avaliacao"]
        
        if "feedback" in atendimento_data:
            atendimento.feedback = atendimento_data["feedback"]
        
        if "etapa_atual" in atendimento_data:
            # Mapear status do ClickUp para etapa do fluxo
            # Implementar lógica específica do cliente
            pass
        
        atendimento.save()
```

## Sinais do Django para Sincronização Automática

```python
# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .services.sync_manager import ClickUpSyncManager
from django.conf import settings

@receiver(post_save, sender=atendimentos.models.Atendimento)
def sync_atendimento_on_save(sender, instance, created, **kwargs):
    """Dispara sincronização quando um atendimento é salvo."""
    if not settings.CLICKUP_CONFIG.get("enabled", False):
        return
    
    # Para evitar loops infinitos e sobrecarga, processamos de forma assíncrona
    from .tasks import sync_atendimento_task
    sync_atendimento_task.delay(instance.id, created)

@receiver(post_save, sender=atendimentos.models.Mensagem)
def update_atendimento_last_message(sender, instance, created, **kwargs):
    """Atualiza a data da última mensagem e dispara sincronização."""
    if not settings.CLICKUP_CONFIG.get("enabled", False):
        return
        
    atendimento = instance.atendimento
    atendimento.data_ultima_mensagem = timezone.now()
    atendimento.save(update_fields=['data_ultima_mensagem'])
    
    # Dispara sincronização para atualizar a task no ClickUp
    from .tasks import sync_atendimento_task
    sync_atendimento_task.delay(atendimento.id, False)
```

## Tarefas Assíncronas com Celery

```python
# tasks.py
from celery import shared_task
from .services.sync_manager import ClickUpSyncManager
from .models import SyncLog
from django.utils import timezone

@shared_task(bind=True, max_retries=3)
def sync_atendimento_task(self, atendimento_id: int, created: bool):
    """Tarefa para sincronizar atendimento com o ClickUp de forma assíncrona."""
    try:
        manager = ClickUpSyncManager()
        
        if not manager.setup_complete:
            manager.setup_initial_structure()
        
        result = manager.sync_atendimento_to_clickup(atendimento_id)
        
        if not result:
            raise Exception("Falha na sincronização")
            
        return {"status": "success", "result": result}
        
    except Exception as e:
        # Tenta novamente se houver erro de rate limit
        if "rate limit" in str(e).lower() and self.request.retries < self.max_retries:
            # Backoff exponencial
            countdown = 2 ** self.request.retries
            raise self.retry(countdown=countdown, exc=e)
        
        # Registra o erro
        SyncLog.objects.create(
            atendimento_id=atendimento_id,
            action="async_sync_error",
            success=False,
            error_message=str(e),
            timestamp=timezone.now()
        )
        
        return {"status": "error", "message": str(e)}

@shared_task
def sync_batch_task(atendimento_ids: list):
    """Sincroniza um lote de atendimentos."""
    manager = ClickUpSyncManager()
    
    if not manager.setup_complete:
        manager.setup_initial_structure()
    
    results = []
    for atendimento_id in atendimento_ids:
        try:
            result = manager.sync_atendimento_to_clickup(atendimento_id)
            results.append({"id": atendimento_id, "status": "success", "result": result})
        except Exception as e:
            results.append({"id": atendimento_id, "status": "error", "message": str(e)})
    
    return results
```

## Implementação de Webhooks

```python
# views.py
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import hmac
import hashlib
from django.conf import settings
from .services.sync_manager import ClickUpSyncManager
from .models import SyncLog

@csrf_exempt
@require_http_methods(["POST"])
def clickup_webhook(request):
    """Endpoint para receber webhooks do ClickUp."""
    # Verificar assinatura do webhook
    signature = request.headers.get("X-Signature")
    secret = settings.CLICKUP_CONFIG.get("webhook_secret")
    
    if not signature or not secret:
        return HttpResponse(status=403)
    
    # Calcular assinatura esperada
    expected_signature = hmac.new(
        secret.encode(),
        request.body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        return HttpResponse(status=403)
    
    try:
        payload = request.json()
        event_type = payload.get("event")
        task_id = payload.get("task_id")
        
        # Processar eventos relevantes
        if event_type in ["taskUpdated", "taskStatusUpdated"]:
            manager = ClickUpSyncManager()
            success = manager.sync_clickup_task_to_atendimento(task_id)
            
            SyncLog.objects.create(
                clickup_task_id=task_id,
                action="webhook_processed",
                success=success,
                timestamp=timezone.now()
            )
        
        return JsonResponse({"status": "ok"})
        
    except Exception as e:
        SyncLog.objects.create(
            clickup_task_id=task_id,
            action="webhook_error",
            success=False,
            error_message=str(e),
            timestamp=timezone.now()
        )
        
        return HttpResponse(status=500)
```

## Considerações de Performance e Boas Práticas

### 1. Controle de Rate Limiting

Implementar um sistema de controle para respeitar os limites da API do ClickUp:

```python
# utils/rate_limiter.py
import time
from threading import Lock

class RateLimiter:
    """Controlador de rate limit para chamadas de API."""
    
    def __init__(self, limit: int, period: int = 60):
        self.limit = limit  # Número máximo de requisições
        self.period = period  # Período em segundos
        self.requests = []  # Timestamps das requisições
        self.lock = Lock()
    
    def wait(self) -> None:
        """Bloqueia até que uma nova requisição possa ser feita."""
        with self.lock:
            now = time.time()
            
            # Remover requisições antigas (fora do período)
            self.requests = [req_time for req_time in self.requests if now - req_time < self.period]
            
            # Verificar se atingiu o limite
            if len(self.requests) >= self.limit:
                # Calcular tempo de espera
                oldest_request = min(self.requests)
                wait_time = self.period - (now - oldest_request)
                if wait_time > 0:
                    time.sleep(wait_time)
                    # Atualizar a lista após a espera
                    now = time.time()
                    self.requests = [req_time for req_time in self.requests if now - req_time < self.period]
            
            # Registrar nova requisição
            self.requests.append(now)
```

### 2. Cache de Configurações

Utilizar cache para armazenar configurações de mapeamento e IDs de estrutura do ClickUp:

```python
# utils/cache.py
from django.core.cache import cache
from typing import Optional, Dict, Any

class ClickUpConfigCache:
    """Cache para configurações da integração com ClickUp."""
    
    CACHE_TIMEOUT = 3600 * 24  # 24 horas
    
    @classmethod
    def get_list_id(cls, department_slug: str) -> Optional[str]:
        """Obtém o ID da lista do departamento do cache."""
        cache_key = f"clickup:list_id:{department_slug}"
        return cache.get(cache_key)
    
    @classmethod
    def set_list_id(cls, department_slug: str, list_id: str) -> None:
        """Define o ID da lista do departamento no cache."""
        cache_key = f"clickup:list_id:{department_slug}"
        cache.set(cache_key, list_id, cls.CACHE_TIMEOUT)
    
    @classmethod
    def get_field_mappings(cls, list_id: str) -> Optional[Dict[str, str]]:
        """Obtém mapeamento de campos do cache."""
        cache_key = f"clickup:field_mappings:{list_id}"
        return cache.get(cache_key)
    
    @classmethod
    def set_field_mappings(cls, list_id: str, mappings: Dict[str, str]) -> None:
        """Define mapeamento de campos no cache."""
        cache_key = f"clickup:field_mappings:{list_id}"
        cache.set(cache_key, mappings, cls.CACHE_TIMEOUT)
    
    @classmethod
    def clear_department_cache(cls, department_slug: str) -> None:
        """Limpa cache relacionado a um departamento."""
        list_id = cls.get_list_id(department_slug)
        if list_id:
            cache.delete(f"clickup:field_mappings:{list_id}")
        cache.delete(f"clickup:list_id:{department_slug}")
```

### 3. Tratamento de Erros e Retry

Implementar estratégias robustas para tratamento de erros e novas tentativas:

```python
# utils/retry_handler.py
import time
import random
from functools import wraps
from typing import Callable, Any, Type, Tuple
import logging

logger = logging.getLogger(__name__)

def retry_on_exception(
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    exception_types: Tuple[Type[Exception], ...] = (Exception,),
    jitter: bool = True
):
    """Decorador para retry com backoff exponencial."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exception_types as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # Calcular tempo de espera com backoff exponencial
                        wait_time = backoff_factor * (2 ** attempt)
                        
                        # Adicionar jitter para evitar sincronização
                        if jitter:
                            wait_time = wait_time * (0.5 + random.random() * 0.5)
                        
                        logger.warning(
                            f"Tentativa {attempt + 1}/{max_retries + 1} falhou. "
                            f"Tentando novamente em {wait_time:.2f}s. Erro: {str(e)}"
                        )
                        time.sleep(wait_time)
            
            # Se todas as tentativas falharem, levantar a última exceção
            raise last_exception
        
        return wrapper
    return decorator
```

## Plano de Implantação

### Fase 1: Infraestrutura Básica
1. Configurar módulo `clickup_sync`
2. Implementar cliente de API básico
3. Criar gerenciador de sincronização inicial
4. Definir modelos para logs de sincronização

### Fase 2: Mapeamento e Transformação
1. Implementar mapeador de campos
2. Criar templates para transformação de dados
3. Configurar estrutura inicial no ClickUp
4. Testar sincronização unidirecional (sistema → ClickUp)

### Fase 3: Sincronização Bidirecional
1. Implementar tratamento de webhooks
2. Criar sistema de transformação reversa (ClickUp → sistema)
3. Configurar sinais do Django para sincronização automática
4. Implementar cache de configurações

### Fase 4: Otimização e Robustez
1. Adicionar controle de rate limiting
2. Implementar sistema de retry
3. Criar painel administrativo para gerenciamento
4. Otimizar performance com cache e processamento em lote

### Fase 5: Monitoramento e Manutenção
1. Implementar sistema de alertas
2. Criar dashboard de métricas de sincronização
3. Documentar processos de troubleshooting
4. Definir procedimentos de backup e recuperação

## Conclusão

Este planejamento técnico estabelece uma arquitetura robusta e escalável para a integração entre o sistema de atendimento e o ClickUp. A implementação deve seguir as fases propostas para garantir uma transição suave e uma integração estável, com foco em performance, confiabilidade e facilidade de manutenção.