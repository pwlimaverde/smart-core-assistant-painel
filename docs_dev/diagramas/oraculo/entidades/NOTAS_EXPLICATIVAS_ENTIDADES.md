# 📚 Notas Explicativas Detalhadas - Diagrama de Relacionamento de Entidades

## 🎯 Visão Geral do Sistema

Este documento complementa o diagrama de relacionamento de entidades, fornecendo explicações detalhadas sobre cada campo, relacionamento e regra de negócio do sistema de atendimento inteligente.

---

## 🧠 1. ENTIDADE: TREINAMENTOS

### 📝 **Descrição**
**Modelo para armazenar informações de treinamento de IA.**

Este modelo gerencia documentos de treinamento organizados por tags e grupos, permitindo armazenar e recuperar documentos LangChain serializados.

### 🔧 **Campos Detalhados**

#### `tag` (STRING, PK) 
- **Tipo**: CharField(max_length=40)
- **Função**: Identificador único do treinamento
- **Validação**: `validate_tag()` - minúsculo, sem espaços, apenas letras/números/underscore
- **Exemplo**: `"atendimento_basico"`, `"produtos_linha_a"`
- **Índice**: PRIMARY KEY
- **Obrigatório**: ✅

#### `grupo` (STRING)
- **Tipo**: CharField(max_length=40)
- **Função**: Categorização organizacional dos treinamentos
- **Validação**: Mesma regra da tag
- **Exemplo**: `"vendas"`, `"suporte_tecnico"`, `"financeiro"`
- **Uso**: Permite agrupar treinamentos por departamento/área
- **Obrigatório**: ✅

#### `documentos` (JSON)
- **Tipo**: JSONField(default=list)
- **Função**: Armazena documentos LangChain serializados
- **Estrutura**: Lista de objetos Document serializados
- **Privado**: Campo interno `_documentos` com métodos de acesso
- **Métodos Relacionados**: `set_documentos()`, `get_documentos()`
- **Obrigatório**: ❌

#### `treinamento_finalizado` (BOOLEAN)
- **Tipo**: BooleanField(default=False)
- **Função**: Indica se o treinamento foi concluído e está pronto para uso
- **Estados**: `False` = Em progresso, `True` = Finalizado
- **Impacto**: Treinamentos não finalizados podem não estar disponíveis para IA
- **Obrigatório**: ✅ (com default)

#### `data_criacao` (DATETIME)
- **Tipo**: DateTimeField(auto_now_add=True)
- **Função**: Timestamp automático de criação
- **Comportamento**: Preenchido automaticamente na criação
- **Imutável**: ✅ (não muda após criação)
- **Uso**: Auditoria e ordenação cronológica

### � **Métodos Importantes**

#### `save(self, *args, **kwargs)`
**Salva o modelo executando validação completa antes do salvamento.**

Args:
- *args: Argumentos posicionais do método save
- **kwargs: Argumentos nomeados do método save

#### `clean(self)`
**Validação personalizada do modelo.**

Valida que a tag não seja igual ao grupo e executa outras validações customizadas do modelo.

Raises:
- ValidationError: Se houver violação das regras de validação

#### `get_conteudo_unificado(self) -> str`
**Retorna todos os page_content da lista de documentos concatenados.**

Processa a lista de documentos LangChain serializados e extrai o conteúdo de texto (page_content) de cada documento, concatenando tudo em uma única string.

Returns:
- str: Conteúdo unificado de todos os documentos, separados por quebras de linha duplas

Note: Se não houver documentos ou se houver erro no processamento, retorna uma string vazia.

#### `set_documentos(self, documentos: List[Document]) -> None`
**Define uma lista de documentos LangChain, serializando-os para JSON.**

Este método processa uma lista de objetos Document do LangChain e os serializa adequadamente para armazenamento no campo JSONField do modelo.

Args:
- documentos: Lista de objetos Document do LangChain a serem armazenados

Raises:
- TypeError: Se algum item da lista não for um objeto Document válido
- ValueError: Se houver erro na serialização dos dados

Example:
```python
from langchain.docstore.document import Document
docs = [
    Document(page_content="Texto 1", metadata={"source": "doc1.txt"}),
    Document(page_content="Texto 2", metadata={"source": "doc2.txt"})
]
treinamento.set_documentos(docs)
```

#### `get_documentos(self) -> List[Document]`
**Processa e converte documentos JSON para objetos Document.**

Desserializa a lista de documentos armazenados no campo JSONField e converte cada item para um objeto Document do LangChain.

Returns:
- List[Document]: Lista de documentos processados. Retorna lista vazia se não houver documentos ou se houver erro no processamento.

Note: Em caso de erro na desserialização, o erro é logado e uma lista vazia é retornada para manter a estabilidade da aplicação.

### �🔗 **Relacionamentos**
- **Nenhum relacionamento direto**: Entidade independente usada pela IA

---

## 👤 2. ENTIDADE: CLIENTE

### 📝 **Descrição**
**Modelo para armazenar informações dos clientes.**

Representa um cliente do sistema com informações básicas como telefone, nome e metadados. O telefone é usado como identificador único.

### 🔧 **Campos Detalhados**

#### `telefone` (STRING, PK)
- **Tipo**: CharField(max_length=20, unique=True)
- **Função**: Identificador único do cliente
- **Formato**: Internacional com +55 (ex: +5511999999999)
- **Validação**: `validate_telefone()` - 10-15 dígitos
- **Normalização**: Automática na criação/edição
- **Índice**: PRIMARY KEY + UNIQUE
- **Obrigatório**: ✅

#### `nome` (STRING)
- **Tipo**: CharField(max_length=100, blank=True, null=True)
- **Função**: Nome do cliente para personalização
- **Origem**: Extraído das mensagens ou fornecido diretamente
- **Privacidade**: Dados pessoais - tratamento conforme LGPD
- **Obrigatório**: ❌

#### `data_cadastro` (DATETIME)
- **Tipo**: DateTimeField(auto_now_add=True)
- **Função**: Primeira interação do cliente no sistema
- **Comportamento**: Preenchido automaticamente
- **Uso**: Métricas de crescimento, análise temporal
- **Imutável**: ✅

#### `ultima_interacao` (DATETIME)
- **Tipo**: DateTimeField(auto_now=True)
- **Função**: Última atividade do cliente
- **Comportamento**: Atualizado automaticamente a cada interação
- **Uso**: Análise de engajamento, clientes inativos
- **Automático**: ✅

#### `metadados` (JSON)
- **Tipo**: JSONField(default=dict)
- **Função**: Informações adicionais flexíveis
- **Exemplos**: 
  ```json
  {
    "origem": "whatsapp",
    "primeira_mensagem": "Olá, preciso de ajuda",
    "tags_interesse": ["produto_a", "desconto"],
    "historico_compras": [],
    "preferencias": {"horario_contato": "manhã"}
  }
  ```
- **Extensível**: ✅ (permite novos campos sem migração)

### � **Métodos Importantes**

#### `__str__(self)`
**Retorna representação string do cliente.**

Returns:
- str: Nome do cliente (ou 'Cliente') seguido do telefone

#### `save(self, *args, **kwargs)`
**Salva o cliente normalizando o número de telefone.**

Normaliza o telefone para formato internacional (+55...) antes de salvar no banco de dados.

Args:
- *args: Argumentos posicionais do método save
- **kwargs: Argumentos nomeados do método save

### �🔗 **Relacionamentos**
- **1:N com ATENDIMENTO**: Um cliente pode ter múltiplos atendimentos
- **Cascade**: Atendimentos são deletados se cliente for removido

---

## 👨‍💼 3. ENTIDADE: ATENDENTE_HUMANO

### 📝 **Descrição**
**Modelo para armazenar informações dos atendentes humanos.**

Representa um atendente humano do sistema com informações completas incluindo dados de contato, credenciais e metadados profissionais.

### 🔧 **Campos Detalhados**

#### `id` (INTEGER, PK)
- **Tipo**: AutoField
- **Função**: Identificador único interno
- **Geração**: Automática e sequencial
- **Relacionamentos**: Usado em FKs de outras entidades

#### `telefone` (STRING, UK)
- **Tipo**: CharField(max_length=20, unique=True)
- **Função**: Identificação única do atendente
- **Formato**: Similar ao cliente (+5511999999999)
- **Uso**: Sessão de login, identificação em conversas
- **Validação**: `validate_telefone()`
- **Obrigatório**: ✅

#### `nome` (STRING)
- **Tipo**: CharField(max_length=100)
- **Função**: Nome completo para identificação
- **Uso**: Interface, relatórios, comunicação
- **Obrigatório**: ✅

#### `cargo` (STRING)
- **Tipo**: CharField(max_length=100)
- **Função**: Função/posição na empresa
- **Exemplos**: "Analista de Suporte", "Supervisor de Vendas"
- **Uso**: Hierarquia, especialização, relatórios
- **Obrigatório**: ✅

#### `departamento` (STRING)
- **Tipo**: CharField(max_length=100, blank=True, null=True)
- **Função**: Departamento organizacional
- **Exemplos**: "Vendas", "Suporte Técnico", "Financeiro"
- **Uso**: Roteamento especializado, relatórios departamentais
- **Obrigatório**: ❌

#### `email` (EMAIL)
- **Tipo**: EmailField(blank=True, null=True)
- **Função**: Contato corporativo
- **Uso**: Notificações, comunicação interna
- **Validação**: Formato de email automático
- **Obrigatório**: ❌

#### `usuario_sistema` (STRING)
- **Tipo**: CharField(max_length=50, blank=True, null=True)
- **Função**: Login do sistema (se diferente do telefone)
- **Uso**: Integração com sistemas de autenticação
- **Obrigatório**: ❌

#### `ativo` (BOOLEAN)
- **Tipo**: BooleanField(default=True)
- **Função**: Status de atividade no sistema
- **Estados**: `True` = Ativo, `False` = Inativo
- **Impacto**: Atendentes inativos não recebem novos atendimentos
- **Uso**: Gestão de recursos humanos

#### `disponivel` (BOOLEAN)
- **Tipo**: BooleanField(default=True)
- **Função**: Disponibilidade imediata para novos atendimentos
- **Estados**: `True` = Disponível, `False` = Ocupado/Pausa
- **Dinâmico**: Pode ser alterado em tempo real
- **Uso**: Distribuição de carga em tempo real

#### `max_atendimentos_simultaneos` (INTEGER)
- **Tipo**: PositiveIntegerField(default=5)
- **Função**: Limite de atendimentos paralelos
- **Validação**: Apenas números positivos
- **Uso**: Controle de carga de trabalho
- **Configurável**: ✅ (por atendente)

#### `especialidades` (JSON)
- **Tipo**: JSONField(default=list)
- **Função**: Lista de áreas de conhecimento
- **Estrutura**: 
  ```json
  ["vendas", "produto_x", "suporte_tecnico_avancado", "ingles"]
  ```
- **Uso**: Roteamento inteligente de atendimentos
- **Métodos**: `adicionar_especialidade()`, `remover_especialidade()`

#### `horario_trabalho` (JSON)
- **Tipo**: JSONField(default=dict)
- **Função**: Horários de trabalho por dia da semana
- **Estrutura**:
  ```json
  {
    "segunda": "08:00-18:00",
    "terca": "08:00-18:00",
    "quarta": "08:00-18:00",
    "quinta": "08:00-18:00",
    "sexta": "08:00-18:00",
    "sabado": "08:00-12:00",
    "domingo": "off"
  }
  ```
- **Uso**: Distribuição de atendimentos respeitando horários

#### `data_cadastro` (DATETIME)
- **Tipo**: DateTimeField(auto_now_add=True)
- **Função**: Data de cadastro no sistema
- **Imutável**: ✅
- **Uso**: Análise de rotatividade, relatórios RH

#### `ultima_atividade` (DATETIME)
- **Tipo**: DateTimeField(auto_now=True)
- **Função**: Última ação no sistema
- **Comportamento**: Atualizado automaticamente
- **Uso**: Monitoramento de atividade, timeouts

#### `metadados` (JSON)
- **Tipo**: JSONField(default=dict)
- **Função**: Configurações e preferências pessoais
- **Exemplos**:
  ```json
  {
    "tema_interface": "dark",
    "notificacoes_email": true,
    "historico_performance": [],
    "configuracoes_dashboard": {}
  }
  ```

### 🔗 **Relacionamentos**
- **1:N com ATENDIMENTO**: Um atendente pode ter múltiplos atendimentos
- **Opcional**: Atendimentos podem não ter atendente (apenas bot)

### 🔧 **Métodos Importantes**
- `get_atendimentos_ativos()`: Retorna atendimentos atuais
- `pode_receber_atendimento()`: Verifica disponibilidade

#### `__str__(self)`
**Retorna representação string do atendente.**

Returns:
- str: Nome e cargo do atendente

#### `adicionar_especialidade(self, especialidade)`
**Adiciona uma nova especialidade à lista de especialidades do atendente.**

Args:
- especialidade (str): Especialidade a ser adicionada

#### `remover_especialidade(self, especialidade)`
**Remove uma especialidade da lista de especialidades do atendente.**

Args:
- especialidade (str): Especialidade a ser removida

---

## 🎫 4. ENTIDADE: ATENDIMENTO

### 📝 **Descrição**
**Modelo para controlar o fluxo de atendimento.**

Representa um atendimento completo com controle de status, histórico, contexto da conversa e metadados associados.

### 🔧 **Campos Detalhados**

#### `id` (INTEGER, PK)
- **Tipo**: AutoField
- **Função**: Identificador único do atendimento
- **Geração**: Sequencial automática
- **Uso**: Referência em relatórios, logs

#### `cliente` (FK)
- **Tipo**: ForeignKey(Cliente, on_delete=CASCADE)
- **Função**: Vinculação ao cliente
- **Comportamento**: Deleta atendimento se cliente for removido
- **Related Name**: `'atendimentos'` (cliente.atendimentos.all())
- **Obrigatório**: ✅

#### `status` (STRING)
- **Tipo**: CharField(max_length=20, choices=StatusAtendimento.choices)
- **Função**: Estado atual do atendimento
- **Default**: `AGUARDANDO_INICIAL`
- **Valores Possíveis**:
  - `aguardando_inicial`: Criado, aguardando primeira interação
  - `em_andamento`: Conversa ativa (bot ou humano)
  - `aguardando_cliente`: Esperando resposta do cliente
  - `aguardando_atendente`: Esperando ação do atendente
  - `resolvido`: Finalizado com sucesso
  - `cancelado`: Cancelado pelo cliente ou sistema
  - `transferido`: Transferido para atendente humano
- **Transições**: Controladas por métodos específicos

#### `data_inicio` (DATETIME)
- **Tipo**: DateTimeField(auto_now_add=True)
- **Função**: Início oficial do atendimento
- **Comportamento**: Preenchido na criação
- **Uso**: SLA, métricas de tempo, relatórios

#### `data_fim` (DATETIME)
- **Tipo**: DateTimeField(blank=True, null=True)
- **Função**: Finalização do atendimento
- **Comportamento**: Preenchido pelo método `finalizar_atendimento()`
- **Uso**: Cálculo de duração, métricas de eficiência

#### `assunto` (STRING)
- **Tipo**: CharField(max_length=200, blank=True, null=True)
- **Função**: Resumo/tema principal do atendimento
- **Origem**: Gerado automaticamente pela IA ou inserido manualmente
- **Uso**: Categorização, busca, relatórios

#### `prioridade` (STRING)
- **Tipo**: CharField com choices
- **Valores**: `baixa`, `normal`, `alta`, `urgente`
- **Default**: `normal`
- **Função**: Controle de fila e SLA
- **Automático**: Pode ser definido pela IA baseado no conteúdo

#### `atendente_humano` (FK)
- **Tipo**: ForeignKey(AtendenteHumano, on_delete=SET_NULL, null=True)
- **Função**: Atendente responsável (quando transferido)
- **Comportamento**: Mantém NULL se apenas bot, preserva ID se atendente deletado
- **Related Name**: `'atendimentos'`
- **Obrigatório**: ❌

#### `contexto_conversa` (JSON)
- **Tipo**: JSONField(default=dict)
- **Função**: Estado atual da conversa e variáveis
- **Estrutura**:
  ```json
  {
    "etapa_atual": "coleta_dados",
    "dados_coletados": {
      "nome": "João",
      "problema": "erro_login"
    },
    "tentativas_resolucao": 2,
    "ultima_intent": "solicitar_suporte"
  }
  ```
- **Uso**: Continuidade da conversa, IA contextual
- **Métodos**: `atualizar_contexto()`, `get_contexto()`

#### `historico_status` (JSON)
- **Tipo**: JSONField(default=list)
- **Função**: Log de todas as mudanças de status
- **Estrutura**:
  ```json
  [
    {
      "timestamp": "2025-07-14T10:00:00Z",
      "status_anterior": "aguardando_inicial",
      "status_novo": "em_andamento",
      "observacao": "Bot iniciou atendimento",
      "usuario": "sistema"
    }
  ]
  ```
- **Auditoria**: ✅ Completa
- **Método**: `adicionar_historico_status()`

#### `tags` (JSON)
- **Tipo**: JSONField(default=list)
- **Função**: Categorização flexível do atendimento
- **Estrutura**: `["urgente", "produto_x", "desconto", "cliente_vip"]`
- **Origem**: IA, atendente ou regras automáticas
- **Uso**: Filtros, relatórios, analytics

#### `avaliacao` (INTEGER)
- **Tipo**: IntegerField com choices (1-5)
- **Função**: Avaliação final do cliente
- **Valores**: 1=Péssimo, 2=Ruim, 3=Regular, 4=Bom, 5=Excelente
- **Coleta**: Automática no encerramento
- **Métricas**: NPS, satisfação

#### `feedback` (TEXT)
- **Tipo**: TextField(blank=True, null=True)
- **Função**: Comentário livre do cliente
- **Coleta**: Opcional no encerramento
- **Uso**: Melhoria contínua, análise qualitativa

### 🔗 **Relacionamentos**
- **N:1 com CLIENTE**: Múltiplos atendimentos por cliente
- **N:1 com ATENDENTE_HUMANO**: Múltiplos atendimentos por atendente
- **1:N com MENSAGEM**: Um atendimento contém múltiplas mensagens

### 🔧 **Métodos Importantes**
- `finalizar_atendimento()`: Fecha o atendimento
- `adicionar_historico_status()`: Log de mudanças
- `atualizar_contexto()`: Atualiza variáveis da conversa
- `transferir_para_humano()`: Transfere para atendente
- `liberar_atendente_humano()`: Remove atendente

#### `finalizar_atendimento(self, novo_status=StatusAtendimento.RESOLVIDO)`
**Finaliza o atendimento definindo data_fim e novo status.**

Args:
- novo_status: Status final do atendimento (padrão: RESOLVIDO)

#### `adicionar_historico_status(self, novo_status, observacao="")`
**Adiciona uma entrada no histórico de mudanças de status.**

Args:
- novo_status: Novo status do atendimento
- observacao: Observação sobre a mudança (opcional)

#### `atualizar_contexto(self, chave, valor)`
**Atualiza uma chave específica no contexto da conversa.**

Args:
- chave: Chave do contexto a ser atualizada
- valor: Novo valor para a chave

#### `get_contexto(self, chave, padrao=None)`
**Recupera um valor do contexto da conversa.**

Args:
- chave: Chave do contexto a ser recuperada
- padrao: Valor padrão se a chave não existir

Returns:
- Valor da chave ou valor padrão

#### `transferir_para_humano(self, atendente_humano, observacao="")`
**Transfere o atendimento para um atendente humano específico.**

Args:
- atendente_humano: Instância do AtendenteHumano que receberá o atendimento
- observacao: Observação sobre a transferência (opcional)

#### `liberar_atendente_humano(self, observacao="")`
**Remove a atribuição do atendente humano do atendimento.**

Args:
- observacao: Observação sobre a liberação (opcional)

---

## 💬 5. ENTIDADE: MENSAGEM

### 📝 **Descrição**
**Modelo para armazenar todas as mensagens da conversa.**

Representa uma mensagem individual dentro de um atendimento, incluindo metadados, tipo de conteúdo e informações de processamento.

### 🔧 **Campos Detalhados**

#### `id` (INTEGER, PK)
- **Tipo**: AutoField
- **Função**: Identificador único da mensagem
- **Sequencial**: ✅ Mantém ordem cronológica

#### `atendimento` (FK)
- **Tipo**: ForeignKey(Atendimento, on_delete=CASCADE)
- **Função**: Vinculação ao atendimento
- **Comportamento**: Deleta mensagem se atendimento for removido
- **Related Name**: `'mensagens'`
- **Obrigatório**: ✅

#### `tipo` (STRING)
- **Tipo**: CharField(max_length=15, choices=TipoMensagem.choices)
- **Default**: `TEXTO`
- **Valores Possíveis**:
  - `texto`: Mensagem de texto simples
  - `imagem`: Arquivo de imagem (JPG, PNG, GIF)
  - `audio`: Arquivo de áudio/voz (MP3, OGG)
  - `video`: Arquivo de vídeo (MP4, AVI)
  - `documento`: Documento/arquivo (PDF, DOC, XLS)
  - `localizacao`: Coordenadas geográficas
  - `contato`: Informações de contato vCard
  - `sistema`: Mensagem automática do sistema

#### `conteudo` (TEXT)
- **Tipo**: TextField
- **Função**: Conteúdo principal da mensagem
- **Variações por Tipo**:
  - `texto`: Texto completo
  - `imagem/audio/video`: URL ou caminho do arquivo
  - `documento`: Nome e URL do arquivo
  - `localizacao`: Coordenadas + descrição
  - `contato`: Dados do contato
  - `sistema`: Mensagem automática
- **Obrigatório**: ✅

#### `remetente` (STRING)
- **Tipo**: CharField(max_length=20, choices=TipoRemetente.choices)
- **Default**: `CLIENTE`
- **Valores**:
  - `cliente`: Mensagem enviada pelo cliente
  - `bot`: Mensagem gerada pelo bot/IA
  - `atendente_humano`: Mensagem do atendente humano
- **Comportamento**: Define como o sistema processa a mensagem
- **Crítico**: ✅ Controla fluxo do bot

#### `timestamp` (DATETIME)
- **Tipo**: DateTimeField(auto_now_add=True)
- **Função**: Data/hora exata da mensagem
- **Ordenação**: Base para ordem cronológica
- **Precisão**: Microsegundos para ordenação exata

#### `message_id_whatsapp` (STRING)
- **Tipo**: CharField(max_length=100, blank=True, null=True)
- **Função**: ID único da mensagem no WhatsApp
- **Uso**: Evitar duplicatas, rastreamento de delivery
- **Opcional**: ✅ (apenas para mensagens WhatsApp)

#### `metadados` (JSON)
- **Tipo**: JSONField(default=dict)
- **Função**: Informações adicionais por tipo
- **Estruturas Exemplo**:
  ```json
  // Para imagem
  {
    "url_arquivo": "https://...",
    "tamanho": 1024000,
    "dimensoes": {"width": 1920, "height": 1080},
    "formato": "jpg"
  }
  
  // Para localização
  {
    "latitude": -23.5505,
    "longitude": -46.6333,
    "endereco": "São Paulo, SP"
  }
  
  // Para áudio
  {
    "duracao": 30,
    "formato": "ogg",
    "transcricao": "Olá, preciso de ajuda"
  }
  ```

#### `respondida` (BOOLEAN)
- **Tipo**: BooleanField(default=False)
- **Função**: Indica se a mensagem foi respondida
- **Uso**: Controle de fluxo, métricas de resposta
- **Método**: `marcar_como_respondida()`

#### `resposta_bot` (TEXT)
- **Tipo**: TextField(blank=True, null=True)
- **Função**: Resposta gerada pelo bot para esta mensagem
- **Preenchimento**: Mesmo se não enviada (baixa confiança)
- **Uso**: Análise de qualidade, treinamento

#### `intent_detectado` (STRING)
- **Tipo**: CharField(max_length=100, blank=True, null=True)
- **Função**: Intenção identificada pelo NLP
- **Exemplos**: "solicitar_suporte", "reclamar", "elogiar", "cancelar"
- **Origem**: Processamento de IA
- **Uso**: Analytics, melhoria da IA

#### `entidades_extraidas` (JSON)
- **Tipo**: JSONField(default=dict)
- **Função**: Entidades extraídas pelo NLP
- **Estrutura**:
  ```json
  {
    "pessoa": ["João Silva"],
    "produto": ["Produto X"],
    "data": ["amanhã", "15/07/2025"],
    "valor": ["R$ 100,00"],
    "email": ["joao@email.com"]
  }
  ```
- **Uso**: Automação, preenchimento de formulários

#### `confianca_resposta` (FLOAT)
- **Tipo**: FloatField(blank=True, null=True)
- **Função**: Nível de confiança da resposta do bot (0-1)
- **Thresholds**:
  - `< 0.5`: Baixa confiança - transferir para humano
  - `0.5-0.8`: Média confiança - pode precisar revisão
  - `> 0.8`: Alta confiança - enviar automaticamente
- **Crítico**: ✅ Controla automação

### 🔗 **Relacionamentos**
- **N:1 com ATENDIMENTO**: Múltiplas mensagens por atendimento
- **Ordem**: Ordenadas por timestamp dentro do atendimento

### 🔧 **Métodos e Properties**
- `marcar_como_respondida()`: Marca como respondida
- `pode_bot_responder()`: Verifica se bot pode responder
- `@property is_from_cliente`: Se é do cliente
- `@property is_from_bot`: Se é do bot
- `@property is_from_atendente`: Se é do atendente

#### `marcar_como_respondida(self, resposta, confianca=None)`
**Marca a mensagem como respondida e define a resposta.**

Args:
- resposta: Texto da resposta
- confianca: Nível de confiança da resposta (opcional)

#### `@property is_from_cliente`
**Verifica se a mensagem é do cliente.**

Returns:
- bool: True se a mensagem é do cliente

#### `@property is_from_bot`
**Verifica se a mensagem é do bot.**

Returns:
- bool: True se a mensagem é do bot

#### `@property is_from_atendente_humano`
**Verifica se a mensagem é de um atendente humano.**

Returns:
- bool: True se a mensagem é de um atendente humano

#### `pode_bot_responder(self)`
**Verifica se o bot pode responder considerando o histórico de mensagens.**

O bot não deve responder se há mensagens de atendente humano no atendimento.

Returns:
- bool: True se o bot pode responder

---

## 🔄 6. ENTIDADE: FLUXO_CONVERSA

### 📝 **Descrição**
**Modelo para definir fluxos de conversa e estados.**

Gerencia os fluxos de conversação automatizados do sistema, incluindo condições de entrada, estados e transições.

### 🔧 **Campos Básicos**
- `id`: Identificador único
- `nome`: Nome único do fluxo
- `descricao`: Descrição detalhada
- `condicoes_entrada`: Condições para ativação
- `estados`: Estados e transições do fluxo
- `ativo`: Status ativo/inativo
- `data_criacao`: Data de criação
- `data_modificacao`: Última modificação

### 🔧 **Métodos Importantes**

#### `__str__(self)`
**Retorna representação string do fluxo de conversa.**

Returns:
- str: Nome do fluxo de conversa

---

## 📊 7. ENUMS E TIPOS DE DADOS

### 🎯 **StatusAtendimento**
**Enum para definir os estados possíveis do atendimento.**

Define todos os status que um atendimento pode ter durante seu ciclo de vida, desde o início até a finalização.

```python
class StatusAtendimento(models.TextChoices):
    AGUARDANDO_INICIAL = "aguardando_inicial", "Aguardando Interação Inicial"
    EM_ANDAMENTO = "em_andamento", "Em Andamento"
    AGUARDANDO_CLIENTE = "aguardando_cliente", "Aguardando Cliente"
    AGUARDANDO_ATENDENTE = "aguardando_atendente", "Aguardando Atendente"
    RESOLVIDO = "resolvido", "Resolvido"
    CANCELADO = "cancelado", "Cancelado"
    TRANSFERIDO = "transferido", "Transferido para Humano"
```

### 📱 **TipoMensagem**
**Enum para definir os tipos de mensagem disponíveis no sistema.**

Define todos os tipos de conteúdo que podem ser enviados e recebidos através dos canais de comunicação.

```python
class TipoMensagem(models.TextChoices):
    TEXTO = "texto", "Texto"
    IMAGEM = "imagem", "Imagem"
    AUDIO = "audio", "Áudio"
    VIDEO = "video", "Vídeo"
    DOCUMENTO = "documento", "Documento"
    LOCALIZACAO = "localizacao", "Localização"
    CONTATO = "contato", "Contato"
    SISTEMA = "sistema", "Mensagem do Sistema"
```

### 👤 **TipoRemetente**
**Enum para definir os tipos de remetente das mensagens.**

Define quem enviou a mensagem para controle do fluxo de interação entre cliente, bot e atendente humano.

```python
class TipoRemetente(models.TextChoices):
    CLIENTE = "cliente", "Cliente"
    BOT = "bot", "Bot/Sistema"
    ATENDENTE_HUMANO = "atendente_humano", "Atendente Humano"
```

---

## 🔗 8. RELACIONAMENTOS DETALHADOS

### **Cliente → Atendimento (1:N)**
- **Tipo**: OneToMany
- **Comportamento**: Um cliente pode ter múltiplos atendimentos ao longo do tempo
- **Cascata**: DELETE CASCADE (remove atendimentos se cliente for deletado)
- **Acesso**: `cliente.atendimentos.all()`
- **Filtros Comuns**: `cliente.atendimentos.filter(status='em_andamento')`

### **AtendenteHumano → Atendimento (1:N)**
- **Tipo**: OneToMany Optional
- **Comportamento**: Um atendente pode ter múltiplos atendimentos simultâneos
- **Cascata**: SET_NULL (preserva atendimento se atendente for deletado)
- **Acesso**: `atendente.atendimentos.all()`
- **Limite**: Controlado por `max_atendimentos_simultaneos`

### **Atendimento → Mensagem (1:N)**
- **Tipo**: OneToMany
- **Comportamento**: Um atendimento contém múltiplas mensagens
- **Cascata**: DELETE CASCADE (remove mensagens se atendimento for deletado)
- **Ordenação**: Por `timestamp` (cronológica)
- **Acesso**: `atendimento.mensagens.order_by('timestamp')`

---

## 🚨 9. REGRAS DE NEGÓCIO CRÍTICAS

### 🤖 **Controle de Bot**
```python
def pode_bot_responder_atendimento(atendimento):
    """
    Bot NÃO responde se existir mensagem de ATENDENTE_HUMANO
    """
    return not atendimento.mensagens.filter(
        remetente=TipoRemetente.ATENDENTE_HUMANO
    ).exists()
```

### 📊 **Sistema de Confiança**
```python
if confianca_resposta < 0.5:
    # Transferir automaticamente para humano
    transferir_atendimento_automatico(atendimento)
elif confianca_resposta >= 0.8:
    # Enviar resposta automaticamente
    enviar_resposta_automatica(resposta)
else:
    # Confiança média - pode precisar revisão
    salvar_resposta_para_revisao(resposta)
```

### 🔄 **Transições de Status**
```python
# Fluxo normal
AGUARDANDO_INICIAL → EM_ANDAMENTO → RESOLVIDO

# Fluxo com transferência
AGUARDANDO_INICIAL → EM_ANDAMENTO → TRANSFERIDO → AGUARDANDO_ATENDENTE → RESOLVIDO

# Fluxo com pausas
EM_ANDAMENTO → AGUARDANDO_CLIENTE → EM_ANDAMENTO → RESOLVIDO
```

### 👥 **Gestão de Atendentes**
```python
def buscar_atendente_disponivel():
    return AtendenteHumano.objects.filter(
        ativo=True,
        disponivel=True,
        atendimentos__status__in=['em_andamento', 'aguardando_cliente']
    ).annotate(
        count_atendimentos=Count('atendimentos')
    ).filter(
        count_atendimentos__lt=F('max_atendimentos_simultaneos')
    ).first()
```

---

## 📊 10. ÍNDICES E PERFORMANCE

### 🚀 **Índices Recomendados**
```sql
-- Busca de cliente por telefone (muito frequente)
CREATE INDEX idx_cliente_telefone ON cliente(telefone);

-- Busca de atendimentos ativos (muito frequente)
CREATE INDEX idx_atendimento_status ON atendimento(status);
CREATE INDEX idx_atendimento_cliente_status ON atendimento(cliente_id, status);

-- Busca de mensagens por atendimento (frequente)
CREATE INDEX idx_mensagem_atendimento ON mensagem(atendimento_id);
CREATE INDEX idx_mensagem_timestamp ON mensagem(timestamp);

-- Busca de mensagens por remetente (para controle de bot)
CREATE INDEX idx_mensagem_remetente ON mensagem(atendimento_id, remetente);

-- WhatsApp message ID (evitar duplicatas)
CREATE UNIQUE INDEX idx_mensagem_whatsapp_id ON mensagem(message_id_whatsapp) WHERE message_id_whatsapp IS NOT NULL;
```

### 📈 **Queries Otimizadas**
```python
# Buscar atendimento ativo com mensagens
atendimento = Atendimento.objects.select_related('cliente', 'atendente_humano')\
    .prefetch_related('mensagens')\
    .filter(cliente__telefone=telefone, status__in=STATUS_ATIVOS)\
    .first()

# Verificar se bot pode responder (otimizado)
pode_responder = not Mensagem.objects.filter(
    atendimento=atendimento,
    remetente=TipoRemetente.ATENDENTE_HUMANO
).exists()
```

---

## �️ 12. FUNÇÕES UTILITÁRIAS DO SISTEMA

### 📞 **Validadores**

#### `validate_tag(value: str) -> None`
**Valida se a tag está em formato válido.**

A tag deve estar em minúsculo, sem espaços, com no máximo 40 caracteres e conter apenas letras minúsculas, números e underscore.

Args:
- value (str): Valor da tag a ser validada

Raises:
- ValidationError: Se a tag não atender aos critérios de validação

Examples:
```python
validate_tag("minha_tag_123")  # válida
validate_tag("MinhaTag")       # inválida - maiúsculas
validate_tag("minha tag")      # inválida - espaço
```

#### `validate_telefone(value: str) -> None`
**Valida se o número de telefone está no formato correto.**

Verifica se o número tem entre 10 e 15 dígitos (formato brasileiro) e contém apenas números após remover caracteres não numéricos.

Args:
- value (str): Número de telefone a ser validado

Raises:
- ValidationError: Se o número não atender aos critérios de validação

Examples:
```python
validate_telefone("11999999999")   # válido
validate_telefone("+5511999999999") # válido
validate_telefone("123")           # inválido - muito curto
```

### 🚀 **Funções de Inicialização e Gestão**

#### `inicializar_atendimento_whatsapp(numero_telefone, primeira_mensagem="", metadata_cliente=None, nome_cliente=None)`
**Inicializa ou recupera um cliente e cria um novo atendimento baseado no número do WhatsApp.**

Args:
- numero_telefone (str): Número de telefone do cliente
- primeira_mensagem (str, optional): Primeira mensagem recebida do cliente
- metadata_cliente (dict, optional): Metadados adicionais do cliente
- nome_cliente (str, optional): Nome do cliente (se conhecido)

Returns:
- tuple: Tupla com (cliente, atendimento) criados/recuperados

Raises:
- Exception: Se houver erro durante a inicialização

#### `buscar_atendimento_ativo(numero_telefone)`
**Busca um atendimento ativo para o número de telefone fornecido.**

Args:
- numero_telefone (str): Número de telefone do cliente

Returns:
- Atendimento: Atendimento ativo ou None se não encontrado

Raises:
- Exception: Se houver erro durante a busca

#### `processar_mensagem_whatsapp(numero_telefone, conteudo, tipo_mensagem=TipoMensagem.TEXTO, message_id=None, metadados=None, remetente=TipoRemetente.CLIENTE)`
**Processa uma mensagem recebida do WhatsApp.**

Args:
- numero_telefone (str): Número de telefone do cliente
- conteudo (str): Conteúdo da mensagem
- tipo_mensagem (TipoMensagem): Tipo da mensagem (texto, imagem, etc.)
- message_id (str, optional): ID da mensagem no WhatsApp
- metadados (dict, optional): Metadados adicionais da mensagem
- remetente (TipoRemetente): Tipo do remetente da mensagem

Returns:
- Mensagem: Objeto mensagem criado

Raises:
- Exception: Se houver erro durante o processamento

### 👥 **Funções de Gestão de Atendentes**

#### `buscar_atendente_disponivel(especialidades=None, departamento=None)`
**Busca um atendente humano disponível para receber um novo atendimento.**

Args:
- especialidades (list, optional): Lista de especialidades requeridas
- departamento (str, optional): Departamento específico

Returns:
- AtendenteHumano: Atendente disponível ou None se nenhum encontrado

#### `transferir_atendimento_automatico(atendimento, especialidades=None, departamento=None)`
**Transfere automaticamente um atendimento para um atendente humano disponível.**

Args:
- atendimento (Atendimento): Atendimento a ser transferido
- especialidades (list, optional): Lista de especialidades requeridas
- departamento (str, optional): Departamento específico

Returns:
- AtendenteHumano: Atendente que recebeu o atendimento ou None se nenhum disponível

Raises:
- Exception: Se houver erro durante a transferência

#### `listar_atendentes_por_disponibilidade()`
**Lista todos os atendentes agrupados por disponibilidade.**

Returns:
- dict: Dicionário com atendentes agrupados por status de disponibilidade

### 🤖 **Funções de Controle de Bot**

#### `pode_bot_responder_atendimento(atendimento)`
**Verifica se o bot pode responder em um atendimento específico.**

O bot não deve responder se há mensagens de atendente humano no atendimento.

Args:
- atendimento (Atendimento): Atendimento a ser verificado

Returns:
- bool: True se o bot pode responder

#### `enviar_mensagem_atendente(atendimento, atendente_humano, conteudo, tipo_mensagem=TipoMensagem.TEXTO, metadados=None)`
**Envia uma mensagem de um atendente humano para um atendimento.**

Args:
- atendimento (Atendimento): Atendimento onde a mensagem será enviada
- atendente_humano (AtendenteHumano): Atendente que está enviando a mensagem
- conteudo (str): Conteúdo da mensagem
- tipo_mensagem (TipoMensagem): Tipo da mensagem (padrão: TEXTO)
- metadados (dict, optional): Metadados adicionais da mensagem

Returns:
- Mensagem: Objeto mensagem criado

Raises:
- ValidationError: Se o atendente não estiver associado ao atendimento

---

## �🔒 11. SEGURANÇA E PRIVACIDADE

### 🛡️ **Dados Sensíveis**
- **Telefones**: Sempre normalizados e validados
- **Nomes**: Tratamento conforme LGPD
- **Mensagens**: Criptografia em trânsito e em repouso
- **Metadados**: Não incluir informações pessoais desnecessárias

### 🔐 **Validações de Segurança**
```python
def validate_telefone(value):
    # Remove caracteres não numéricos
    telefone_limpo = re.sub(r'\D', '', value)
    if len(telefone_limpo) < 10 or len(telefone_limpo) > 15:
        raise ValidationError("Telefone deve ter entre 10 e 15 dígitos")

def validate_tag(value):
    if len(value) > 40:
        raise ValidationError('Tag deve ter no máximo 40 caracteres.')
    if ' ' in value:
        raise ValidationError('Tag não deve conter espaços.')
    if not value.islower():
        raise ValidationError('Tag deve conter apenas letras minúsculas.')
    if not re.match(r'^[a-z0-9_]+$', value):
        raise ValidationError('Tag deve conter apenas letras minúsculas, números e underscore.')
```

---

**📋 Documento Versão**: 1.0  
**📅 Data**: 14 de julho de 2025  
**🎯 Status**: ✅ Documentação Completa com Docstrings  
**🔄 Próxima Revisão**: Conforme evolução do sistema  
**📚 Fonte**: Baseado nas docstrings do arquivo models.py
