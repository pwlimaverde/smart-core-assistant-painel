# Mapeamento Completo dos Models Django (v3.0 - Atualizado)

**Data:** Janeiro 2025  
**Status:** ✅ Aprovado e Atualizado  
**Versão:** 3.0 - Inclui modelos do app `notion_sync`

---

## 📋 Índice

1. [Models da Aplicação Principal](#1-models-da-aplicação-principal)
   - [App: clientes](#11-app-clientes)
   - [App: operacional](#12-app-operacional)
   - [App: atendimentos](#13-app-atendimentos)
2. [Models do App de Integração](#2-models-do-app-de-integração-notion_sync)
3. [Grafo de Relacionamentos](#3-grafo-de-relacionamentos)
4. [Mapeamento para Notion](#4-mapeamento-para-notion)
5. [Tabela Resumo](#5-tabela-resumo)

---

## 1. Models da Aplicação Principal

### 1.1. App: `clientes`

#### Modelo: `Contato`

**Tabela:** `oraculo_contato`

```python
class Contato(models.Model):
    # Identificação
    id: AutoField (PK)
    telefone: CharField(20, unique=True, validators=[validate_telefone])
    nome_contato: CharField(100, null=True, blank=True)
    
    # Contato
    email: EmailField(254, null=True, blank=True)
    nome_perfil_whatsapp: CharField(100, null=True, blank=True)
    
    # Status e Timestamps
    ativo: BooleanField(default=True)
    data_cadastro: DateTimeField(auto_now_add=True)
    ultima_interacao: DateTimeField(auto_now=True)
    
    # Extensibilidade
    metadados: JSONField(dict, default={})
```

**Relacionamentos:**
- `clientes` → ManyToMany reverso para `Cliente`
- `atendimentos` → OneToMany reverso para `Atendimento`

**Validações:**
- Telefone normalizado automaticamente para +55XXXXXXXXXXX
- Validação de formato de telefone (10-15 dígitos)

**Meta:**
- Ordering: `['-ultima_interacao']`
- Índices: `telefone` (unique)

**Sincronização Notion:** ✅ Sim - Bidirecional

---

#### Modelo: `Cliente`

**Tabela:** `oraculo_cliente`

```python
class Cliente(models.Model):
    # Identificação
    id: AutoField (PK)
    nome_fantasia: CharField(200, blank=False, null=False)
    razao_social: CharField(200, null=True, blank=True)
    tipo: CharField(20, choices=['fisica', 'juridica'], null=True)
    
    # Documentos
    cnpj: CharField(18, validators=[validate_cnpj], null=True, blank=True)
    cpf: CharField(14, validators=[validate_cpf], null=True, blank=True)
    
    # Contato
    telefone: CharField(20, validators=[validate_telefone], null=True, blank=True)
    site: URLField(null=True, blank=True)
    
    # Negócio
    ramo_atividade: CharField(200, null=True, blank=True)
    observacoes: TextField(null=True, blank=True)
    
    # Endereço Completo
    cep: CharField(10, validators=[validate_cep], null=True, blank=True)
    logradouro: CharField(200, null=True, blank=True)
    numero: CharField(10, null=True, blank=True)
    complemento: CharField(100, null=True, blank=True)
    bairro: CharField(100, null=True, blank=True)
    cidade: CharField(100, null=True, blank=True)
    uf: CharField(2, null=True, blank=True)
    pais: CharField(50, default='Brasil', null=True, blank=True)
    
    # Relacionamentos
    contatos: ManyToManyField('Contato', related_name='clientes')
    
    # Status e Timestamps
    ativo: BooleanField(default=True)
    data_cadastro: DateTimeField(auto_now_add=True)
    ultima_atualizacao: DateTimeField(auto_now=True)
    
    # Extensibilidade
    metadados: JSONField(dict, default={})
```

**Relacionamentos:**
- `contatos` → ManyToMany para `Contato`
- `atendimentos` → Indireto via `Contato`

**Validações:**
- CNPJ formatado automaticamente (XX.XXX.XXX/XXXX-XX)
- CPF formatado automaticamente (XXX.XXX.XXX-XX)
- CEP formatado automaticamente (XXXXX-XXX)
- UF sempre uppercase

**Métodos Úteis:**
- `get_endereco_completo()` → str
- `adicionar_contato(contato: Contato)` → None
- `remover_contato(contato: Contato)` → None
- `atualizar_metadados(chave, valor)` → None
- `get_metadados(chave, padrao)` → Any

**Meta:**
- Ordering: `['nome_fantasia']`
- Índices: `nome_fantasia`

**Sincronização Notion:** ✅ Sim - Bidirecional

---

### 1.2. App: `operacional`

#### Modelo: `Departamento`

**Tabela:** `oraculo_departamento`

```python
class Departamento(models.Model):
    # Identificação
    id: AutoField (PK)
    nome: CharField(100, unique=True)
    slug: SlugField(120, unique=True, blank=True, null=True)
    descricao: TextField(null=True, blank=True)
    
    # Status e Config
    ativo: BooleanField(default=True)
    configuracoes: JSONField(dict, default={})
    
    # Timestamps
    data_criacao: DateTimeField(auto_now_add=True)
    
    # Extensibilidade
    metadados: JSONField(dict, default={})
```

**Relacionamentos:**
- `atendentes` → OneToMany reverso para `AtendenteHumano`
- `whatsapp_instances` → OneToMany reverso para `WhatsAppInstance`
- `atendimentos` → OneToMany reverso para `Atendimento`

**Comportamento:**
- Slug gerado automaticamente via `slugify(nome)` ao salvar

**Meta:**
- Ordering: `['nome']`
- Índices: `slug`, `[ativo, nome]`

**Sincronização Notion:** ✅ Sim - Django → Notion (somente leitura no Notion)

---

#### Modelo: `AtendenteHumano`

**Tabela:** `oraculo_atendentehumano`

```python
class AtendenteHumano(models.Model):
    # Identificação
    id: AutoField (PK)
    nome: CharField(100)
    telefone: CharField(20, unique=True, validators=[validate_telefone], null=True, blank=True)
    cargo: CharField(100)
    
    # Departamento
    departamento: ForeignKey('Departamento', on_delete=SET_NULL, null=True, blank=True, 
                            related_name='atendentes')
    
    # Contato
    email: EmailField(null=True, blank=True)
    
    # Usuário Sistema
    usuario: OneToOneField(User, on_delete=SET_NULL, null=True, blank=True,
                          related_name='atendente_humano')
    usuario_sistema: CharField(50, null=True, blank=True)
    
    # Status e Disponibilidade
    ativo: BooleanField(default=True)
    disponivel: BooleanField(default=True)
    max_atendimentos_simultaneos: PositiveIntegerField(default=5)
    data_ultima_atribuicao: DateTimeField(null=True, blank=True)
    
    # Configurações
    horario_trabalho: JSONField(dict, default={})
    especialidades: JSONField(list, default=[])
    
    # Timestamps
    data_cadastro: DateTimeField(auto_now_add=True)
    ultima_atividade: DateTimeField(auto_now=True)
    
    # Extensibilidade
    metadados: JSONField(dict, default={})
```

**Relacionamentos:**
- `departamento` → ManyToOne para `Departamento`
- `whatsapp_instance` → OneToOne reverso para `WhatsAppInstance`
- `atendimentos` → OneToMany reverso para `Atendimento`
- `usuario` → OneToOne para `django.contrib.auth.User`

**Validações:**
- Telefone normalizado para +55XXXXXXXXXXX

**Métodos Úteis:**
- `get_atendimentos_ativos()` → int
- `is_available()` → bool
- `current_load()` → int

**Meta:**
- Ordering: `['nome']`
- Índices: `[departamento, disponivel]`, `[disponivel, max_atendimentos_simultaneos]`, `[data_ultima_atribuicao]`

**Sincronização Notion:** ✅ Sim - Bidirecional

---

#### Modelo: `WhatsAppInstance`

**Tabela:** `oraculo_whatsapp_instance`

```python
class WhatsAppInstance(models.Model):
    # Identificação
    id: AutoField (PK)
    phone_number: CharField(20, unique=True, validators=[validate_telefone_instancia],
                           null=True, blank=True)
    instance_id: CharField(100, unique=True, null=True, blank=True)
    
    # Credenciais (SENSÍVEL)
    api_key: CharField(100, unique=True, validators=[validate_api_key])
    provider: CharField(30, choices=[('evolution', 'Evolution'), ('other', 'Other')],
                       default='evolution')
    
    # Relacionamentos
    departamento: ForeignKey('Departamento', on_delete=CASCADE, null=True, blank=True,
                            related_name='whatsapp_instances')
    owner: OneToOneField('AtendenteHumano', on_delete=SET_NULL, null=True, blank=True,
                        related_name='whatsapp_instance')
    
    # Status
    ativo: BooleanField(default=True)
    
    # Timestamps
    data_criacao: DateTimeField(auto_now_add=True)
    ultima_validacao: DateTimeField(null=True, blank=True)
    
    # Extensibilidade
    metadados: JSONField(dict, default={})
```

**Relacionamentos:**
- `departamento` → ManyToOne para `Departamento`
- `owner` → OneToOne para `AtendenteHumano`

**Métodos Úteis:**
- `validar_api_key(data: dict)` → Optional[WhatsAppInstance] (classmethod)
- `selecionar_proximo_atendente()` → Optional[AtendenteHumano]
- `atendentes` → Property que retorna QuerySet

**Meta:**
- Ordering: `['-data_criacao']`
- Índices: `api_key`, `phone_number`, `instance_id`, `provider`

**Sincronização Notion:** ❌ **NÃO** - Contém credenciais sensíveis

---

### 1.3. App: `atendimentos`

#### Enums

```python
class StatusAtendimento(TextChoices):
    FILA = 'fila', 'Fila'
    EM_ATENDIMENTO = 'em_atendimento', 'Em Atendimento'
    AGUARDANDO_RETORNO = 'aguardando_retorno', 'Aguardando Retorno'
    RESOLVIDO = 'resolvido', 'Resolvido'
    CANCELADO = 'cancelado', 'Cancelado'

class TipoMensagem(TextChoices):
    TEXTO_FORMATADO = 'extendedTextMessage', 'Texto com formatação'
    IMAGEM = 'imageMessage', 'Imagem'
    VIDEO = 'videoMessage', 'Vídeo'
    AUDIO = 'audioMessage', 'Áudio'
    DOCUMENTO = 'documentMessage', 'Documento'
    STICKER = 'stickerMessage', 'Sticker'
    LOCALIZACAO = 'locationMessage', 'Localização'
    CONTATO = 'contactMessage', 'Contato (vCard)'
    LISTA = 'listMessage', 'Lista Interativa'
    BOTOES = 'buttonsMessage', 'Botões'
    ENQUETE = 'pollMessage', 'Enquete'
    REACAO = 'reactMessage', 'Reação (emoji)'

class TipoRemetente(TextChoices):
    CONTATO = 'contato', 'Contato'
    BOT = 'bot', 'Bot/Sistema'
    ATENDENTE_HUMANO = 'atendente_humano', 'Atendente Humano'
```

---

#### Modelo: `Atendimento`

**Tabela:** `oraculo_atendimento`

```python
class Atendimento(models.Model):
    # Identificação
    id: AutoField (PK)
    assunto: CharField(200, null=True, blank=True)
    
    # Relacionamentos Principais
    contato: ForeignKey('clientes.Contato', on_delete=CASCADE, related_name='atendimentos')
    departamento: ForeignKey('operacional.Departamento', on_delete=SET_NULL, 
                            null=True, blank=True, related_name='atendimentos')
    atendente_humano: ForeignKey('operacional.AtendenteHumano', on_delete=SET_NULL,
                                 null=True, blank=True, related_name='atendimentos')
    
    # Status e Prioridade
    status: CharField(20, choices=StatusAtendimento.choices, default=StatusAtendimento.FILA)
    prioridade: CharField(10, choices=[('baixa','Baixa'), ('normal','Normal'),
                                        ('alta','Alta'), ('urgente','Urgente')],
                         default='normal')
    
    # Canal de Origem (NOVO)
    canal: CharField(20, choices=[('whatsapp','WhatsApp'), ('email','E-mail'),
                                  ('telefone','Telefone'), ('web','Website')],
                    default='whatsapp')
    
    # Timestamps
    data_inicio: DateTimeField(auto_now_add=True)
    data_fim: DateTimeField(null=True, blank=True)
    data_ultima_mensagem: DateTimeField(null=True, blank=True)
    data_primeira_resposta: DateTimeField(null=True, blank=True)  # NOVO
    
    # Contexto e Histórico
    contexto_conversa: JSONField(dict, default={})
    historico_status: JSONField(list[dict], default=[])
    tags: JSONField(list[str], default=[])
    
    # Avaliação
    avaliacao: IntegerField(choices=[(i,str(i)) for i in range(1,6)], null=True, blank=True)
    feedback: TextField(null=True, blank=True)
```

**Property Calculada:**
```python
@property
def cliente(self) -> Optional[Cliente]:
    """Retorna o cliente principal vinculado ao contato."""
    return self.contato.clientes.first() if self.contato.clientes.exists() else None
```

**Relacionamentos:**
- `contato` → ManyToOne para `Contato` (obrigatório)
- `departamento` → ManyToOne para `Departamento` (opcional)
- `atendente_humano` → ManyToOne para `AtendenteHumano` (opcional)
- `mensagens` → OneToMany reverso para `Mensagem`
- `cliente` → Property computada via `contato.clientes`

**Métodos Úteis:**
- `finalizar_atendimento(novo_status='resolvido')` → None
- `change_status(novo_status, observacao='')` → None
- `adicionar_historico_status(status, observacao)` → None
- `assign_to_agent(agente, observacao='')` → None
- `unassign_agent(observacao='')` → None
- `transfer_to_department(departamento)` → None
- `touch_last_message()` → None
- `atualizar_contexto(chave, valor)` → None
- `get_contexto(chave, default=None)` → Any
- `transferir_para_humano(agente, observacao='')` → None
- `carregar_historico_mensagens(limite=50, pagina=1)` → dict

**Meta:**
- Ordering: `['-data_inicio']`
- Índices: `[status, departamento]`, `[departamento, data_ultima_mensagem]`, `[atendente_humano, status]`

**Sincronização Notion:** ✅ Sim - Bidirecional (CRÍTICO)

---

#### Modelo: `Mensagem`

**Tabela:** `oraculo_mensagem`

```python
class Mensagem(models.Model):
    # Identificação
    id: AutoField (PK)
    message_id_whatsapp: CharField(null=True, blank=True)
    
    # Relacionamento
    atendimento: ForeignKey('Atendimento', on_delete=CASCADE, related_name='mensagens')
    
    # Tipo e Conteúdo
    tipo: CharField(choices=TipoMensagem.choices, default=TipoMensagem.TEXTO_FORMATADO)
    conteudo: TextField()
    remetente: CharField(choices=TipoRemetente.choices, default='contato')
    
    # Timestamp
    timestamp: DateTimeField(auto_now_add=True)
    
    # Bot/IA
    respondida: BooleanField(default=False)
    resposta_bot: TextField(null=True, blank=True)
    intent_detectado: JSONField(list[dict], default=[])
    entidades_extraidas: JSONField(list[dict], default=[])
    confianca_resposta: FloatField(null=True, blank=True)
    
    # Extensibilidade
    metadados: JSONField(dict, default={})  # URL de mídia, etc.
```

**Relacionamentos:**
- `atendimento` → ManyToOne para `Atendimento` (obrigatório)

**Métodos Úteis:**
- `registrar_resposta_bot(resposta, intent, entidades, confianca)` → None

**Meta:**
- Ordering: `['timestamp']`
- Índices: `timestamp`

**Sincronização Notion:** ✅ Sim - Django → Notion (somente leitura no Notion)

---

## 2. Models do App de Integração (`notion_sync`)

### 2.1. Modelo: `NotionObjectMapping`

**Tabela:** `notion_sync_object_mapping`

**Objetivo:** Mapear objetos Django ↔ Notion (substitui campos notion_page_id nos models principais)

```python
class NotionObjectMapping(models.Model):
    # Identificação
    id: AutoField (PK)
    
    # Django Object
    content_type: ForeignKey(ContentType, on_delete=CASCADE)
    object_id: PositiveIntegerField()
    content_object: GenericForeignKey('content_type', 'object_id')
    
    # Notion Reference
    notion_page_id: CharField(36, unique=True, db_index=True)
    notion_database_id: CharField(36, db_index=True)
    
    # Sync Status
    sync_status: CharField(20, choices=[
        ('pending', 'Pendente'),
        ('synced', 'Sincronizado'),
        ('error', 'Erro'),
        ('outdated', 'Desatualizado')
    ], default='pending')
    
    # Timestamps
    created_at: DateTimeField(auto_now_add=True)
    last_synced_at: DateTimeField(null=True, blank=True)
    
    # Metadata
    sync_metadata: JSONField(dict, default={})
```

**Relacionamentos:**
- Generic relation para qualquer modelo Django
- Índice composto em `[content_type, object_id]`

**Meta:**
- Unique together: `[content_type, object_id]`
- Índices: `notion_page_id`, `[content_type, object_id]`, `sync_status`

---

### 2.2. Modelo: `SyncLog`

**Tabela:** `notion_sync_log`

**Objetivo:** Registrar todas as operações de sincronização

```python
class SyncLog(models.Model):
    # Identificação
    id: AutoField (PK)
    
    # Operation
    model_name: CharField(100)
    instance_id: PositiveIntegerField()
    external_id: CharField(100, null=True, blank=True)  # notion_page_id
    
    # Sync Details
    direction: CharField(20, choices=[
        ('to_external', 'Django → External'),
        ('from_external', 'External → Django')
    ])
    operation: CharField(20)  # create, update, delete
    status: CharField(20, choices=[
        ('pending', 'Pendente'),
        ('in_progress', 'Em Progresso'),
        ('success', 'Sucesso'),
        ('failed', 'Falha'),
        ('partial', 'Parcial')
    ], default='pending')
    
    # Error Tracking
    error_message: TextField(null=True, blank=True)
    error_trace: TextField(null=True, blank=True)
    retry_count: IntegerField(default=0)
    max_retries: IntegerField(default=3)
    
    # Data
    request_data: JSONField(null=True, blank=True)
    response_data: JSONField(null=True, blank=True)
    
    # Timestamps
    created_at: DateTimeField(auto_now_add=True)
    updated_at: DateTimeField(auto_now=True)
    completed_at: DateTimeField(null=True, blank=True)
```

**Meta:**
- Ordering: `['-created_at']`
- Índices: `[model_name, instance_id]`, `[status, created_at]`, `external_id`

---

### 2.3. Modelo: `SyncConfig`

**Tabela:** `notion_sync_config`

**Objetivo:** Configuração dinâmica da sincronização

```python
class SyncConfig(models.Model):
    # Identificação
    id: AutoField (PK)
    key: CharField(100, unique=True)
    
    # Config
    value: JSONField()
    description: TextField(null=True, blank=True)
    
    # Control
    active: BooleanField(default=True)
    
    # Timestamps
    created_at: DateTimeField(auto_now_add=True)
    updated_at: DateTimeField(auto_now=True)
```

**Exemplos de Configurações:**
```python
# Habilitar/desabilitar sincronização global
{key: 'NOTION_SYNC_ENABLED', value: True}

# Habilitar/desabilitar sincronização assíncrona
{key: 'NOTION_SYNC_ASYNC', value: True}

# Configurar modelos a sincronizar
{key: 'NOTION_SYNC_MODELS', value: ['Contato', 'Cliente', 'Atendimento']}

# Rate limiting
{key: 'NOTION_RATE_LIMIT', value: {'requests_per_second': 3}}

# Retry configuration
{key: 'NOTION_RETRY_CONFIG', value: {'max_retries': 3, 'backoff_factor': 2}}
```

**Meta:**
- Índices: `key`, `active`

---

### 2.4. Modelo: `SyncQueue`

**Tabela:** `notion_sync_queue`

**Objetivo:** Fila de sincronização para processamento assíncrono

```python
class SyncQueue(models.Model):
    # Identificação
    id: AutoField (PK)
    
    # Task
    model_name: CharField(100)
    instance_id: PositiveIntegerField()
    operation: CharField(20)  # create, update, delete
    
    # Priority
    priority: IntegerField(default=0)  # Maior = maior prioridade
    
    # Status
    status: CharField(20, choices=[
        ('queued', 'Na Fila'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou')
    ], default='queued')
    
    # Retry
    attempts: IntegerField(default=0)
    max_attempts: IntegerField(default=3)
    next_retry_at: DateTimeField(null=True, blank=True)
    
    # Data
    payload: JSONField()
    
    # Timestamps
    created_at: DateTimeField(auto_now_add=True)
    updated_at: DateTimeField(auto_now=True)
    processed_at: DateTimeField(null=True, blank=True)
```

**Meta:**
- Ordering: `['-priority', 'created_at']`
- Índices: `[status, priority]`, `[model_name, instance_id]`, `next_retry_at`

---

## 3. Grafo de Relacionamentos

### 3.1. Aplicação Principal

```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │ M:N
       ▼
┌─────────────┐        ┌──────────────┐
│   Contato   │◄───────│  Atendimento │
└─────────────┘  1:N   └──────┬───────┘
                              │ 1:N
                              ▼
                       ┌─────────────┐
                       │  Mensagem   │
                       └─────────────┘

┌──────────────┐
│ Departamento │
└──────┬───────┘
       │ 1:N
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌─────────────┐ ┌──────────────┐ ┌──────────────┐
│ Atendente   │ │   WhatsApp   │ │ Atendimento  │
│   Humano    │ │   Instance   │ │              │
└──────┬──────┘ └──────────────┘ └──────────────┘
       │ 1:N
       ▼
┌──────────────┐
│ Atendimento  │
└──────────────┘
```

### 3.2. Integração Notion

```
┌──────────────────────┐
│  Django Model        │
│  (qualquer tipo)     │
└──────────┬───────────┘
           │
           │ GenericForeignKey
           ▼
┌──────────────────────┐
│ NotionObjectMapping  │
└──────────┬───────────┘
           │
           │ notion_page_id
           ▼
┌──────────────────────┐
│  Notion Page         │
└──────────────────────┘

           ┌──────────────────────┐
           │     SyncQueue        │
           └──────────┬───────────┘
                      │
                      ▼
           ┌──────────────────────┐
           │      SyncLog         │
           └──────────────────────┘
```

---

## 4. Mapeamento para Notion

### 4.1. Status do Django → Notion

```python
# Em notion_sync/constants.py
STATUS_NOTION_MAPPING = {
    'fila': '🕐 Aguardando Inicial',
    'em_atendimento': '⚡ Em Andamento',
    'aguardando_retorno': '⏸️ Aguardando Contato',
    'resolvido': '✅ Resolvido',
    'cancelado': '❌ Cancelado'
}

PRIORIDADE_NOTION_MAPPING = {
    'baixa': '🟢 Baixa',
    'normal': '🟡 Média',
    'alta': '🔴 Alta',
    'urgente': '🔥 Urgente'
}

CANAL_NOTION_MAPPING = {
    'whatsapp': '💬 WhatsApp',
    'email': '📧 Email',
    'telefone': '📞 Telefone',
    'web': '🌐 Web'
}

TIPO_MENSAGEM_NOTION_MAPPING = {
    'extendedTextMessage': '📝 Texto',
    'imageMessage': '🖼️ Imagem',
    'videoMessage': '🎥 Vídeo',
    'audioMessage': '🎵 Áudio',
    'documentMessage': '📄 Documento',
    'stickerMessage': '📎 Sticker',
    'locationMessage': '📍 Localização',
    'contactMessage': '👤 Contato',
    'listMessage': '📋 Lista',
    'buttonsMessage': '🔘 Botões',
    'pollMessage': '📊 Enquete',
    'reactMessage': '😀 Reação'
}

REMETENTE_NOTION_MAPPING = {
    'contato': '👤 Cliente',
    'bot': '🤖 Bot',
    'atendente_humano': '👨‍💼 Atendente'
}
```

### 4.2. Databases Notion

| Modelo Django | Database Notion | Notion ID Env Var | Sincronização |
|---------------|-----------------|-------------------|---------------|
| Contato | 📞 Contatos | `NOTION_CONTATOS_DB_ID` | Bidirecional |
| Cliente | 🏢 Clientes | `NOTION_CLIENTES_DB_ID` | Bidirecional |
| Departamento | 🏛️ Departamentos | `NOTION_DEPARTAMENTOS_DB_ID` | Django → Notion |
| AtendenteHumano | 👤 At