# 📋 Notas Explicativas - Fluxo de Recebimento de Mensagem WhatsApp

## 🎯 Visão Geral do Sistema
**Versão**: 4.3 - Otimização da Verificação Bot Response
**Data**: 18 de julho de 2025

Este fluxo representa o processo completo de **recebimento, processamento e resposta** de mensagens WhatsApp no sistema de atendimento inteligente. O sistema combina **automação via IA** com **atendimento humano** para oferecer suporte eficiente.

### ✨ **Principais Características**:
1. **Tratamento Completo de Mídia**: IA converte áudio, imagem e documentos para texto
2. **Direcionamento Inteligente**: Sistema detecta atendente responsável e direciona automaticamente
3. **Classificação Inteligente de Intent**: Distingue perguntas, satisfação e transferências
4. **Transferência Avançada**: Suporte a transferência por setor e entre atendentes específicos
5. **Loop Otimizado**: Bot retorna para início do fluxo, passando por classificação intent
6. **Busca Especializada**: Sistema busca atendentes por setor quando necessário
7. **Controle Hierárquico**: Estrutura numerada facilita navegação e manutenção

### 🔄 **Estrutura Hierárquica de Loops**
1. **6.9.1**: Loop nova mensagem bot - retorna para início (1.1) via intent (6.1)
2. **7.4.1**: Loop de busca por atendente (sub-nível de 7.4)
3. **8.1.3**: Loop notificação atendente (sub-nível de 8.1)
4. **8.1.4**: Loop nova mensagem durante espera atendente (sub-nível de 8.1)
5. **8.10.1**: Loop nova mensagem cliente para humano (sub-nível de 8.10)

**Vantagem**: A numeração hierárquica torna claro que os loops são **extensões** dos processos principais, com **classificação de intent** determinando fluxos específicos (pergunta vs satisfação).

### 🔄 **Atualizações na Versão 4.3**
1. **Otimização da Verificação Bot**: A função `_pode_bot_responder_atendimento` agora é chamada apenas uma vez no ponto 5.1
2. **Eliminação de Redundâncias**: Removida verificação duplicada no início do fluxo (antiga seção 1.5)
3. **Reorganização Estrutural**: Verificação de atendente responsável (5.2) agora ocorre após verificação bot (5.1)
4. **Fluxo Mais Limpo**: Centralizada a decisão de direcionamento bot vs humano em um único ponto
5. **Melhor Performance**: Evita múltiplas consultas desnecessárias ao banco de dados
6. **Clareza no Código**: Um único ponto de controle facilita manutenção e entendimento
7. **Lógica Otimizada**: Verifica primeiro se bot pode responder, depois contexto de responsabilidade

---

## 🚀 1. INÍCIO DO FLUXO - Nova Mensagem Recebida

### 📱 1.1 **Função: webhook_whatsapp (View Django)**
**Processo**: Ponto de entrada para o webhook do WhatsApp
- **Responsabilidades**:
  - Receber payload JSON do webhook
  - Validar API KEY e evento
  - Chamar `nova_mensagem()` para processamento
  - Obter o objeto Mensagem completo usando o ID retornado
  - Registrar logs de processamento
  - Retornar resposta HTTP adequada
- **Tratamento de Erros**:
  - Captura exceções durante todo o processamento
  - Registra erros detalhados via logger
  - Retorna resposta HTTP 500 em caso de falha
- **Estrutura**:
  ```python
  @csrf_exempt
  def webhook_whatsapp(request):
      from .models import nova_mensagem, Mensagem

      try:
          # Processar dados
          data = json.loads(request.body)
          mensagem_id = nova_mensagem(data)
          mensagem = Mensagem.objects.get(id=mensagem_id)
          
          # Log de sucesso
          logger.info(f"Mensagem processada com sucesso. ID: {mensagem_id}")
          
          # Responder ao webhook
          return JsonResponse({"status": "success", "mensagem_id": mensagem_id}, status=200)
      except Exception as e:
          logger.error(f"Erro no webhook WhatsApp: {e}")
          return JsonResponse({"error": str(e)}, status=500)
  ```

**Nota**: A verificação `_pode_bot_responder_atendimento` foi movida para o ponto 5.1 para otimizar o fluxo.

### 🔍 1.2 **Função: nova_mensagem**
**Processo**: Extração e processamento dos dados do webhook
- **Extrações**:
  - `phone`: Número do telefone do cliente (extraído de `data.key.remoteJid`)
  - `message_id`: ID único da mensagem no WhatsApp (extraído de `data.key.id`)
  - `tipo_chave`: Tipo da mensagem (textMessage, imageMessage, etc.)
  - `conteudo`: Conteúdo específico com base no tipo
  - `metadados`: Dados adicionais por tipo de mensagem (URL, mimetype, etc.)
- **Tipos Suportados**:
  - TEXTO_FORMATADO: Mensagens de texto simples
  - IMAGEM: Fotos com ou sem legenda
  - VIDEO: Vídeos com ou sem legenda
  - AUDIO: Mensagens de voz ou áudio
  - DOCUMENTO: Arquivos PDF, DOC, etc.
  - STICKER, LOCALIZACAO, CONTATO, LISTA, BOTOES, ENQUETE, REACAO
- **Retorno**: ID da mensagem criada (valor inteiro)

### ⚙️ 1.3 **Função: processar_mensagem_whatsapp**
**Processo**: Processamento completo da mensagem
- **Determinação do Remetente**:
  - Verifica se o número pertence a um atendente humano
  - Define como CLIENTE ou ATENDENTE_HUMANO
- **Fluxo Principal**:
  - Busca atendimento ativo com `buscar_atendimento_ativo()`
  - Se não existir, inicializa novo com `inicializar_atendimento_whatsapp()`
  - Cria objeto `Mensagem` no banco de dados com os dados do webhook
  - Atualiza timestamp da última interação do cliente
- **Retorno**: ID da mensagem criada

### 💾 1.4 **Recuperar Objeto Mensagem**
**Processo**: Recupera o objeto Mensagem completo a partir do ID
- **Função**: `Mensagem.objects.get(id=mensagem_id)`
- **Objetivo**: Obter todos os atributos da mensagem, incluindo o relacionamento com o atendimento
- **Importância**: Permite acessar `mensagem.atendimento` para verificações subsequentes

### ❓ 1.5 **Função: _pode_bot_responder_atendimento**
**Processo**: Verifica se o bot pode responder ao atendimento
- **Implementação**: 
  ```python
  def _pode_bot_responder_atendimento(atendimento):
      mensagens_atendente = atendimento.mensagens.filter(
          remetente=TipoRemetente.ATENDENTE_HUMANO
      ).exists()
      
      return not mensagens_atendente
  ```
- **Lógica**: O bot não deve responder se houver mensagens de atendente humano no atendimento
- **Resultado**: 
  - `True`: Bot pode responder (fluxo automatizado)
  - `False`: Bot não pode responder (fluxo humano)

**Técnica**: Utiliza Django ORM com `get_or_create()` para evitar duplicatas.

### 🔍 1.4 **Recuperar Objeto Mensagem**
**Processo**: Recupera o objeto Mensagem completo a partir do ID
- **Função**: `Mensagem.objects.get(id=mensagem_id)`
- **Objetivo**: Obter todos os atributos da mensagem, incluindo o relacionamento com o atendimento
- **Importância**: Permite acessar `mensagem.atendimento` para verificações subsequentes no fluxo

---

## 🔍 2. VERIFICAÇÃO DE ATENDIMENTO ATIVO - buscar_atendimento_ativo
**Processo**: Verificação do tipo de conteúdo recebido
- **TEXTO**: Prossegue diretamente para verificação de atendimento ativo
- **NÃO-TEXTO**: Direciona para processamento de conversão via IA
- **Tipos Suportados**: AUDIO, IMAGEM, VIDEO, DOCUMENTO, STICKER

### 🤖 1.6 **Processar Conteúdo Não-Texto**
**Processo**: Identificação e preparação para conversão
- **AUDIO**: Preparar para transcrição de voz para texto
- **IMAGEM**: Preparar para análise de conteúdo visual
- **DOCUMENTO**: Preparar para extração de texto (PDF, DOC, etc.)
- **VIDEO**: Preparar para transcrição de áudio do vídeo
- **Validação**: Verificar formato e tamanho do arquivo

### 📝 1.7 **Converter para Texto via IA Agent**
**Processo**: Conversão inteligente de conteúdo multimídia
- **Transcrição de Áudio**: 
  - Utiliza modelos de Speech-to-Text
  - Identifica idioma automaticamente
  - Filtra ruídos e melhora qualidade
- **Análise de Imagem**:
  - OCR para texto em imagens
  - Descrição de conteúdo visual
  - Identificação de elementos relevantes
- **Extração de Documento**:
  - Parse de PDFs e documentos
  - Preserva formatação importante
  - Extrai texto estruturado
- **Processamento de Vídeo**:
  - Extrai trilha de áudio
  - Transcreve conteúdo falado
  - Identifica cenas relevantes

**Resultado**: Conteúdo convertido em formato texto mantendo referência ao arquivo original.

---

## 🔍 2. VERIFICAÇÃO DE ATENDIMENTO ATIVO - buscar_atendimento_ativo

### 🔍 2.1 **Função: buscar_atendimento_ativo**
**Processo**: Localiza conversas em andamento
- **Implementação**:
  ```python
  def buscar_atendimento_ativo(numero_telefone):
      # Normaliza o número de telefone
      telefone_limpo = re.sub(r'\D', '', numero_telefone)
      if not telefone_limpo.startswith('55'):
          telefone_limpo = '55' + telefone_limpo
      telefone_formatado = '+' + telefone_limpo

      cliente = Cliente.objects.filter(telefone=telefone_formatado).first()
      if not cliente:
          return None

      atendimento = Atendimento.objects.filter(
          cliente=cliente,
          status__in=[
              StatusAtendimento.AGUARDANDO_INICIAL,
              StatusAtendimento.EM_ANDAMENTO,
              StatusAtendimento.AGUARDANDO_CLIENTE,
              StatusAtendimento.AGUARDANDO_ATENDENTE
          ]
      ).first()

      return atendimento
  ```
- **Status Verificados**:
  - `AGUARDANDO_INICIAL`: Novo atendimento criado
  - `EM_ANDAMENTO`: Conversa ativa com bot ou humano
  - `AGUARDANDO_CLIENTE`: Aguardando resposta do cliente
  - `AGUARDANDO_ATENDENTE`: Aguardando ação do atendente humano

**Lógica de Negócio**: Um cliente só pode ter **um atendimento ativo** por vez. Isso evita fragmentação de conversas e mantém contexto.

### 📋 2.2 **Decisão: Existe atendimento ativo?**
**Critério**: Busca por atendimento com status não finalizado
- **SIM**: Verifica se tem atendente responsável (2.3)
- **NÃO**: Inicia novo atendimento (3.1)

### 👤 2.3 **Decisão: Atendimento tem atendente responsável?**
**Processo**: Verificação de responsabilidade definida
- **Verificação**: `atendimento.atendente_humano is not None`
- **SIM**: Direciona para atendente responsável (2.4)
- **NÃO**: Continua fluxo normal sem responsável (4.1)

### 🎯 2.4 **Direcionar para Atendente Responsável**
**Processo**: Bypass do controle do bot
- **Prioridade**: Mensagem vai diretamente para atendente definido
- **Contexto**: Ignora triagem geral do sistema
- **Eficiência**: Conexão direta com responsável
- **Importância**: Mantém continuidade do atendimento humano

### 💾 2.5 **CREATE Mensagem Direta**
**Processo**: Salvamento para atendente responsável
- **Conteúdo**: Mensagem completa do cliente
- **Remetente**: `CLIENTE`
- **Vinculação**: Relaciona ao atendimento com responsável
- **Timestamp**: Automático

### 💾 2.6 **UPDATE Cliente - Interação Direta**
**Processo**: Atualização para fluxo direto
- **Campo**: `ultima_interacao = now`
- **Contexto**: Rastreamento de atividade com responsável
- **Analytics**: Dados para métricas de atendimento e direcionamento direto

---

## 🆕 3. CRIAR NOVO ATENDIMENTO - inicializar_atendimento_whatsapp

### 🆕 3.1 **Função: inicializar_atendimento_whatsapp**
**Processo**: Criação de novo atendimento
- **Implementação**:
  ```python
  def inicializar_atendimento_whatsapp(numero_telefone, mensagem_texto=None, tipo_mensagem=None):
      # Normaliza o número de telefone
      telefone_limpo = re.sub(r'\D', '', numero_telefone)
      if not telefone_limpo.startswith('55'):
          telefone_limpo = '55' + telefone_limpo
      telefone_formatado = '+' + telefone_limpo

      # Busca ou cria cliente
      cliente, cliente_criado = Cliente.objects.get_or_create(
          telefone=telefone_formatado,
          defaults={
              'nome': f'Cliente {telefone_formatado[-4:]}',
              'ultima_interacao': timezone.now()
          }
      )

      # Verifica se já existe atendimento ativo
      atendimento_ativo = buscar_atendimento_ativo(numero_telefone)
      if atendimento_ativo:
          return atendimento_ativo

      # Cria novo atendimento
      atendimento = Atendimento.objects.create(
          cliente=cliente,
          status=StatusAtendimento.AGUARDANDO_INICIAL,
          canal=CanalAtendimento.WHATSAPP,
          origem=OrigemAtendimento.CLIENTE
      )

      # Registra primeira mensagem se fornecida
      if mensagem_texto:
          Mensagem.objects.create(
              atendimento=atendimento,
              remetente=RemetenteMensagem.CLIENTE,
              tipo=tipo_mensagem or TipoMensagem.TEXTO,
              conteudo=mensagem_texto
          )

          # Atualiza status para EM_ANDAMENTO após primeira mensagem
          atendimento.status = StatusAtendimento.EM_ANDAMENTO
          atendimento.save(update_fields=['status'])

          # Registra mudança de status no histórico
          HistoricoStatusAtendimento.objects.create(
              atendimento=atendimento,
              status_anterior=StatusAtendimento.AGUARDANDO_INICIAL,
              status_novo=StatusAtendimento.EM_ANDAMENTO,
              motivo="Primeira mensagem do cliente"
          )

      return atendimento
  ```
- **Verificação**: Confirma ausência de atendimento ativo
- **Criação**: Novo registro de atendimento
- **Status Inicial**: `AGUARDANDO_INICIAL`
- **Vinculação**: Associa ao cliente (existente ou novo)

### 💾 3.2 **CREATE Mensagem (Primeira)**
- **Conteúdo**: Texto completo da mensagem original
- **Remetente**: `CLIENTE` (enum)
- **Tipo**: Detectado automaticamente (TEXTO/IMAGEM/etc)
- **Rastreamento**: `message_id_whatsapp` para evitar duplicatas
- **Timestamp**: Automático via `auto_now_add=True`
- **Condição**: Executado apenas se `mensagem_texto` for fornecido

### 💾 3.3 **UPDATE Atendimento - Status: EM_ANDAMENTO**
- **Transição**: `AGUARDANDO_INICIAL` → `EM_ANDAMENTO`
- **Histórico**: "Primeira mensagem recebida e processada"
- **Trigger**: Ativa o controle central do bot
- **Condição**: Executado apenas se `mensagem_texto` for fornecido

### 📝 3.4 **CREATE Histórico Status**
**Processo**: Registro de mudança de estado
- **Campos**:
  - `atendimento`: Referência ao atendimento
  - `status_anterior`: `AGUARDANDO_INICIAL`
  - `status_novo`: `EM_ANDAMENTO`
  - `data_hora`: Automático
  - `motivo`: "Primeira mensagem do cliente"
- **Condição**: Executado apenas se `mensagem_texto` for fornecido

---

## 🔄 4. CONTINUAR ATENDIMENTO EXISTENTE - Continuar Conversa

### 💾 4.1 **CREATE Mensagem (Continuação)**
- **Vinculação**: Relaciona à conversa existente via FK
- **Sequência**: Mantém ordem cronológica
- **Contexto**: Preserva histórico completo da conversa

### 💾 4.2 **UPDATE Cliente - Última Interação**
- **Campo**: `ultima_interacao = now`
- **Objetivo**: Rastreamento de atividade do cliente
- **Uso**: Analytics e métricas de engajamento

---

## 🔧 5. CONTROLE CENTRAL DO BOT - Bot assume controle do atendimento

### ❓ 5.1 **_pode_bot_responder_atendimento - ÚNICA VERIFICAÇÃO**
**Processo**: Verificação centralizada se o bot deve responder ao atendimento
- **Localização**: Única verificação realizada antes do fluxo de resposta
- **Condição Principal**: Não há mensagens de atendente humano no atendimento
- **Implementação**: 
  ```python
  def _pode_bot_responder_atendimento(atendimento):
      from .models import TipoRemetente
      
      mensagens_atendente = atendimento.mensagens.filter(
          remetente=TipoRemetente.ATENDENTE_HUMANO
      ).exists()
      
      return not mensagens_atendente
  ```
- **Resultado**: 
  - `True`: Bot pode responder - fluxo continua para 5.2
  - `False`: Bot não pode responder - direciona para 8.0 (Atendimento Humano)

### 👤 5.2 **Atendimento tem atendente responsável?**
**Processo**: Verificação de responsabilidade definida para contexto
- **Verificação**: `atendimento.atendente_humano is not None`
- **SIM**: Continua para verificação de tipo de mensagem (5.3)
- **NÃO**: Continua para verificação de tipo de mensagem (5.3)
- **Nota importante**: Esta verificação não bloqueia o fluxo, apenas registra o contexto para decisões futuras

### ❓ 5.3 **Mensagem precisa processamento especial?**
**Processo**: Verificação do tipo de conteúdo para processamento especial
- **Condição**: Tipo de mensagem não é TEXTO
- **SIM**: Direcionar para processamento especial (5.4)
- **NÃO**: Seguir para análise direta da mensagem (6.0)

### 🤖 5.4 **Processar Conteúdo Especial**
**Processo**: Tratamento específico para conteúdo não textual
- **Extração**: Informações contextuais do conteúdo
- **Metadados**: Específicos por tipo (imagem, áudio, documento, etc.)
- **Preparação**: Formatação para análise de intent
- **Resultado**: Conteúdo enriquecido para processamento pelo bot

## 🤖 6. FLUXO DE RESPOSTA DO BOT - Analisar e Classificar Intent

### 🧠 6. **Análise de Mensagem**
**Processo**: Análise inicial e preparação para classificação
- **IA Analítica**: Processa mensagem com modelos de linguagem
- **Extração**: Intent, entidades e contexto da conversa
- **Base de Conhecimento**: Consulta informações relevantes
- **Preparação**: Dados estruturados para classificação

### ❓ 6.1 **Classificar Intent**
**Processo**: Decisão crítica sobre o tipo de mensagem do cliente
- **PERGUNTA**: Cliente faz questionamento ou solicita informação
  - Exemplos: "Como faço para...", "Qual é o valor de...", "Preciso de ajuda com..."
  - Ação: Direciona para geração de resposta (6.2)
- **AGRADECIMENTO/SATISFAÇÃO**: Cliente demonstra resolução ou gratidão
  - Exemplos: "Obrigado", "Resolvido", "Já consegui", "Perfeito", "Muito obrigado"
  - Ação: Direciona para detecção de satisfação (6.3)
- **TRANSFERÊNCIA**: Cliente solicita mudança de setor ou atendente
  - Exemplos: "Quero falar com o financeiro", "Preciso falar com um supervisor"
  - Ação: Direciona para intent de transferência (6.1.1)

### 🔄 6.1.1 **Detectar Intent Transferência**
**Processo**: Identificação de solicitação de mudança de setor
- **Análise**: Cliente solicita mudança de setor ou especialista
- **Extração**: Identifica setor destino da mensagem
- **Exemplos**: "quero falar financeiro", "preciso suporte técnico"
- **Ação**: Direciona para busca de atendente (7. TRANSFERÊNCIA)

### 💭 6.2 **Gerar Resposta**
**Processo**: Criação de resposta para perguntas
- **IA Generativa**: Processa pergunta com modelo de linguagem
- **Cálculo de Confiança**: Score de 0.0 a 1.0
- **Personalização**: Adapta tom e conteúdo ao contexto
- **Preparação**: Resposta estruturada para avaliação

### ✅ 6.3 **Detectar Satisfação**
**Processo**: Processamento de sinais de resolução
- **Análise Semântica**: Identifica expressões de satisfação
- **Contexto**: Avalia se problema foi realmente resolvido
- **Agradecimento**: Processa diferentes formas de gratidão
- **Encerramento**: Prepara finalização automática do atendimento

### ❓ 6.4 **Verificação: Confiança >= 0.5?**
**Primeiro Filtro**: Avaliação inicial de confiança para perguntas
- **< 0.5**: Direcionamento para **6.5 transferir_atendimento_automatico**
- **≥ 0.5**: Prossegue para segundo filtro (6.6)

### 👤 6.5 **transferir_atendimento_automatico**
**Processo**: Transferência por baixa confiança
- **Motivo**: Baixa confiança na resposta gerada
- **Ação**: Transferir para atendente humano
- **Status**: Escalação automática

### ❓ 6.6 **Verificação: Confiança >= 0.8?**
**Segundo Filtro**: Avaliação de alta confiança
- **≥ 0.8**: **6.7 Resposta Automática** (alta confiança)
- **0.5-0.8**: **6.8 Resposta Requer Revisão** (confiança média)

### 📤 6.7 **Resposta Automática**
**Processo**: Envio direto ao cliente
- **Remetente**: `BOT` (identificação clara)
- **Ação**: Salvar mensagem BOT e enviar para cliente
- **Confiança**: Alta confiança (≥ 0.8)

### ⚠️ 6.8 **Resposta Requer Revisão**
**Processo**: Resposta com supervisão
- **Salvamento**: Resposta preparada com baixa confiança
- **Lógica**: Customizável conforme regras de negócio
- **Confiança**: Média (0.5-0.8)

### ⏳ 6.9 **Bot Aguarda Resposta Cliente**
**Processo**: Monitoramento automatizado com loop inteligente
- **Status**: `AGUARDANDO_CLIENTE`
- **Timeout**: Configurável (ex: 30 minutos sem resposta)
- **Loop**: Sistema mantém conversa até satisfação ou timeout
- **Inteligência**: Retorna para classificação de intent (6.1) automaticamente

#### 🔄 6.9.1 **Nova Mensagem Cliente Loop**
**Processo**: Retorno inteligente para início do fluxo
- **Ação**: Quando cliente responde, retorna para item **1.1** (Receber Mensagem)
- **Classificação**: Nova mensagem passa novamente por **6.1** (Classificar Intent)
- **Eficiência**: Satisfação é detectada automaticamente no intent
- **Loop**: Processo continua até cliente demonstrar satisfação ou timeout

---

## 👥 7. TRANSFERÊNCIA PARA ATENDENTE - buscar_atendente_disponivel

### 🔍 7.1 **Função: buscar_atendente_disponivel**
**Processo**: Localização de atendente apropriado
- **Filtros**:
  - `ativo=True`: Atendente logado no sistema
  - `disponivel=True`: Não está em pausa/ausente
  - `max_atendimentos_simultaneos`: Respeita limite de carga
- **Balanceamento**: Distribui carga entre atendentes

### 🏢 7.1.1 **Decisão: Transfer solicitada para setor específico?**
**Processo**: Verificação de especialização requerida
- **SIM**: Busca atendente por setor específico (7.1.2)
- **NÃO**: Busca atendente geral disponível (7.2)

### 🏢 7.1.2 **buscar_atendente_por_setor**
**Processo**: Busca especializada por setor
- **Filtros**: Atendentes do setor específico
- **Priorização**: Especialistas do setor em questão
- **Verificação**: Disponibilidade dentro do setor
- **Balanceamento**: Distribui carga dentro do setor

### ❓ 7.2 **Decisão: Atendente Disponível?**

#### ❌ **NÃO - 7.3 Nenhum Atendente Disponível**
**Processo**: Gerenciamento de fila com loop contínuo
- **Notificação**: Administradores alertados em tempo real
- **Estratégia**: Sistema inicia loop de busca contínua
- **Escalação**: Processo automático de chamada repetitiva
- **Monitoramento**: Log de tentativas e intervalos

### ⏳ 7.4 **Aguardar e Tentar Novamente**
**Processo**: Loop inteligente de busca por atendente
- **Intervalo**: Aguarda tempo configurável entre tentativas
- **Contador**: Incrementa número de tentativas
- **Log**: Registra cada ciclo de busca
- **Persistência**: Mantém tentativas até encontrar atendente disponível

### 🔄 7.4.1 **Nova Busca (Loop)**
**Processo**: Retorno automático para busca de atendente
- **Automático**: Sistema retorna automaticamente para item 7.1
- **Contínuo**: Loop persiste até encontrar atendente disponível
- **Inteligente**: Cada ciclo inclui notificação administrativa
- **Configurável**: Intervalo de tentativas pode ser ajustado

#### ✅ **SIM - 7.5 transferir_para_humano**
**Processo**: Atribuição de atendente
- **Atualização**: `atendimento.atendente_humano = atendente`
- **Status**: `TRANSFERIDO`
- **Histórico**: Log da transferência automática
- **Notificação**: Alerta em tempo real para atendente

### 📬 7.6 **Notificar Atendente**
**Processo**: Preparação para atendimento humano
- **Interface**: Prepara dashboard do atendente
- **Contexto**: Histórico completo da conversa
- **Ferramentas**: Acesso a informações do cliente

### 👤 7.7 **Atendente Assume Controle**
**Processo**: Transferência de responsabilidade
- **Bot**: Para de responder automaticamente
- **Controle**: Passa totalmente para o atendente humano
- **Estado**: Atendimento sob supervisão humana


---

## 👤 8. ATENDIMENTO HUMANO ATIVO - Aguardar Ação do Atendente

### ❓ 8.1 **Decisão: Atendente Enviou Resposta?**
**Processo**: Verificação de ação do atendente com timeout inteligente
- **SIM**: Processa mensagem do atendente (8.2)
- **NÃO**: Inicia monitoramento de timeout (8.1.1)

#### ⏰ 8.1.1 **Aguardar Timeout Atendente**
**Processo**: Monitoramento de tempo limite com notificação proativa
- **Período**: Configurável (ex: 5-10 minutos)
- **Monitoramento**: Sistema rastreia tempo de inatividade
- **Trigger**: Acionado quando atendente não responde no prazo

#### 📢 8.1.2 **Notificar Atendente Novamente**
**Processo**: Sistema de lembrete proativo
- **Alerta**: Notificação de timeout no dashboard
- **Conteúdo**: "Lembrete: Resposta pendente para cliente [nome/telefone]"
- **Escalação**: Incrementa contador de notificações
- **Persistência**: Mantém alertas até resposta ou finalização

#### 🔄 8.1.3 **Loop Notificação Atendente**
**Processo**: Ciclo contínuo de notificação até resposta ou fechamento
- **Hierarquia**: Sub-nível do item 8.1 (Aguardar Ação do Atendente)
- **Retorno**: Volta para decisão 8.1 (Atendente enviou resposta?)
- **Persistência**: Continua até atendente responder

#### 🔄 8.1.4 **Nova Mensagem Cliente Loop**
**Processo**: Reativação por nova mensagem do cliente
- **Hierarquia**: Sub-nível do item 8.1 (Aguardar Ação do Atendente)
- **Prioridade**: Nova mensagem interrompe ciclo de notificação
- **Continuidade**: Fluxo retorna ao início (item 1.1) mantendo contexto humano
- **Notificação**: Atendente é imediatamente alertado sobre nova mensagem

### 💾 8.2 **enviar_mensagem_atendente**
**Processo**: Processamento de mensagem do atendente
- **Remetente**: `ATENDENTE_HUMANO`
- **Rastreamento**: `ultima_atividade` atualizada
- **Metadados**: ID do atendente, timestamp
- **Controle**: Bot permanece inativo

### 🔄 8.3 **Decisão: Atendente solicitou transferência?**
**Processo**: Verificação de comando de transferência
- **Comando**: Detecta `/transfer` ou equivalente
- **SIM**: Processa comando de transferência (8.4)
- **NÃO**: Continua fluxo normal (8.9)

### 🔄 8.4 **processar_comando_transferencia**
**Processo**: Análise do comando de transferência
- **Extração**: Setor ou atendente destino
- **Validação**: Verifica permissões do atendente
- **Preparação**: Organiza histórico para transferência
- **Log**: Registra motivo da transferência

### 🎯 8.5 **Decisão: Tipo de Transferência?**
**Processo**: Classificação do destino da transferência
- **SETOR**: Transferência para setor específico (8.5.1)
- **ATENDENTE**: Transferência para atendente específico (8.5.2)

### 🏢 8.5.1 **transferir_para_setor**
**Processo**: Transferência por especialização
- **Busca**: Atendentes disponíveis do setor
- **Critérios**: Aplicar regras de disponibilidade
- **Balanceamento**: Distribuir carga dentro do setor
- **Especialização**: Priorizar expertise específica

### 👤 8.5.2 **transferir_para_atendente_especifico**
**Processo**: Transferência direcionada
- **Validação**: Verificar se atendente existe
- **Disponibilidade**: Checar status do atendente
- **Forçar**: Permite transferência mesmo se ocupado
- **Prioridade**: Atendimento específico solicitado

### 📝 8.6 **atualizar_historico_transferencia**
**Processo**: Registro completo da transferência
- **Origem**: Registrar atendente que transferiu
- **Destino**: Registrar novo responsável
- **Motivo**: Documentar razão da transferência
- **Timestamp**: Marcar momento da transferência

### 📬 8.7 **notificar_novo_atendente**
**Processo**: Comunicação ao novo responsável
- **Contexto**: Enviar histórico completo da conversa
- **Detalhes**: Informações sobre a transferência
- **Interface**: Preparar dashboard para novo atendente
- **Alerta**: Notificação em tempo real

### 📤 8.8 **notificar_atendente_origem**
**Processo**: Confirmação para quem transferiu
- **Confirmação**: Validar que transferência foi concluída
- **Liberação**: Remover conversa da lista do atendente
- **Contadores**: Atualizar métricas de atendimento
- **Status**: Liberar para novos atendimentos

### ❓ 8.9 **Decisão: Atendente Escolhe Próximo Passo?**
**Processo**: Controle total do atendente sobre o fluxo
- **Interface**: Dashboard com opções claras
- **Finalizar Agora**: Atendente avalia que problema foi resolvido
- **Aguardar Cliente**: Espera resposta do cliente para continuar
- **Autonomia**: Decisão exclusiva do atendente humano

### ⏳ 8.10 **Humano Aguarda Cliente**
**Processo**: Espera controlada por atendente
- **Status**: `AGUARDANDO_CLIENTE_HUMANO`
- **Timeout**: Sem timeout automático de encerramento
- **Controle**: Atendente mantém responsabilidade total
- **Flexibilidade**: Pode aguardar indefinidamente se necessário

#### 🔄 8.10.1 **Nova Mensagem Cliente Loop**
**Processo**: Recebimento de resposta durante espera
- **Reinício**: Fluxo retorna ao início (1.1)
- **Contexto**: Mantém atendente humano como responsável
- **Continuidade**: Preserva histórico completo da conversa
- **Prioridade**: Direcionamento direto para mesmo atendente

### 🏁 8.11 **Atendente Finaliza Agora**
**Processo**: Encerramento direto pelo atendente
- **Critério**: Atendente considera problema resolvido
- **Ação**: Direcionamento imediato para seção 9 (Encerramento)
- **Controle**: Bypassa verificações automáticas
- **Responsabilidade**: Atendente assume decisão de encerramento

---

## 🏁 9. ENCERRAR ATENDIMENTO - finalizar_atendimento

### 🏁 9.1 **Gerar Mensagem Final**
**Conteúdo Padrão**:
- Resumo da conversa e soluções fornecidas
- Solicitação de avaliação (NPS/satisfação)
- Mensagem de despedida personalizada
- Informações de contato para futuro suporte

### 💾 9.2 **UPDATE Atendimento - Status: RESOLVIDO**
- **Status Final**: `RESOLVIDO`
- **Timestamp**: `data_fim = now`
- **Histórico**: "Atendimento finalizado com sucesso"
- **Métricas**: Tempo total, número de mensagens

### 💾 9.3 **CREATE Mensagem (Encerramento)**
- **Conteúdo**: Mensagem final de encerramento
- **Remetente**: `BOT`
- **Timestamp**: Automático
- **Finalização**: Última mensagem do atendimento

### 📤 9.4 **Enviar Mensagem Final**
**Processo**: Comunicação de encerramento
- **Avaliação**: Link ou formulário de feedback
- **Follow-up**: Agendamento de contato futuro se necessário
- **Documentação**: Registro completo para análise

### 🏁 9.5 **Fim do Fluxo**
**Estado**: Atendimento Encerrado
- **Conclusão**: Processo totalmente finalizado
- **Arquivo**: Conversa arquivada para histórico
- **Disponibilidade**: Sistema pronto para nova interação

---

## 🔄 LOOPS HIERÁRQUICOS - Retornos Estruturados

### 🔄 6.9.1 **Nova Mensagem Bot Loop (Loop Hierárquico)**
**Processo**: Reativação durante espera do bot
- **Hierarquia**: Sub-nível do item 6.9 (Bot Aguarda Resposta Cliente)
- **Contexto**: Mantém controle automatizado
- **Prioridade**: Nova mensagem interrompe timeout do bot
- **Continuidade**: Fluxo retorna ao início (item 1.1) mantendo contexto bot

### 🔄 7.4.1 **Loop de Busca por Atendente (Referência Cruzada)**
**Processo**: Loop contínuo de busca por atendente disponível
- **Hierarquia**: Sub-nível do item 7.4 (Aguardar e Tentar Novamente)
- **Estratégia**: Busca persistente com notificações administrativas
- **Retorno**: Volta para item 7.1 (buscar_atendente_disponivel)
- **Eficiência**: Garante que nenhum cliente fique sem atendimento

### 🔄 8.1.3 **Loop de Notificação do Atendente (Referência Cruzada)**
**Processo**: Ciclo de lembrete para atendente inativo
- **Hierarquia**: Sub-nível do item 8.1 (Aguardar Ação do Atendente)
- **Timeout**: Sistema monitora inatividade do atendente
- **Opções de Saída**: Alertas periódicos até resposta OU fechamento do atendimento
- **Flexibilidade**: Atendente pode decidir encerrar sem responder
- **Retorno**: Volta para decisão 8.1 (Atendente enviou resposta?)

### 🔄 8.1.4 **Nova Mensagem Atendente Loop (Loop Hierárquico)**
**Processo**: Interrupção por nova mensagem durante espera do atendente
- **Hierarquia**: Sub-nível do item 8.1 (Aguardar Ação do Atendente)
- **Prioridade**: Nova mensagem tem precedência sobre timeout
- **Interrupção**: Para ciclo de notificação do atendente
- **Retorno**: Fluxo volta ao início (item 1.1) mantendo contexto humano

### 🔄 8.10.1 **Nova Mensagem Cliente Loop para Humano (Loop Hierárquico)**
**Processo**: Reativação durante espera controlada pelo atendente
- **Hierarquia**: Sub-nível do item 8.10 (Humano Aguarda Cliente)
- **Controle**: Mantém responsabilidade do atendente humano
- **Flexibilidade**: Sem timeout automático de encerramento
- **Continuidade**: Fluxo retorna ao início (item 1.1) preservando contexto humano

---

## 📊 MÉTRICAS E MONITORAMENTO

### 📈 **KPIs Principais**
- **Tempo de Primeira Resposta**: Bot vs Humano
- **Taxa de Resolução Automática**: % resolvido pelo bot
- **Satisfação do Cliente**: NPS e feedback
- **Eficiência do Atendente**: Tempo médio por atendimento

### 🔍 **Logs e Auditoria**
- **Rastreabilidade**: Cada ação é logada
- **Debugging**: Facilita identificação de problemas
- **Compliance**: Atende requisitos de auditoria
- **Analytics**: Base para melhorias contínuas

---

## 🎯 REGRAS DE NEGÓCIO CRÍTICAS

### 🚫 **Restrições**
1. **Um atendimento ativo por cliente**
2. **Bot respeita controle humano**
3. **Mensagens não podem ser perdidas**
4. **Histórico deve ser preservado**

### ✅ **Garantias**
1. **Todas as mensagens são processadas**
2. **Contexto é mantido entre sessões**
3. **Escalação automática funciona**
4. **Auditoria completa está disponível**
5. **Loops hierárquicos garantem continuidade**

---

## 🔧 CONSIDERAÇÕES TÉCNICAS

### 🏗️ **Arquitetura**
- **Django Models**: ORM para persistência
- **Celery**: Processamento assíncrono
- **Redis**: Cache e filas
- **mySQL**: Banco de dados principal

### 🔒 **Segurança**
- **Sanitização**: Todos os inputs são validados
- **Rate Limiting**: Proteção contra spam
- **Encryption**: Dados sensíveis criptografados
- **Access Control**: Permissões granulares

### 📱 **Integrações**
- **WhatsApp Business API**: Comunicação oficial
- **IA/LLM**: Processamento de linguagem natural
- **Agentes de IA para Mídia**:
  - **Speech-to-Text**: Transcrição de áudios e vídeos
  - **OCR/Vision**: Análise de imagens e documentos
  - **Document Parser**: Extração de texto de PDFs e documentos
  - **Content Analyzer**: Interpretação inteligente de conteúdo multimídia
- **CRM**: Sincronização de dados de clientes
- **Analytics**: Ferramentas de monitoramento

---

**Versão**: 4.0 - Documentação Totalmente Alinhada com Diagrama  
**Data**: 15 de julho de 2025  
**Status**: ✅ Documentação Sincronizada - Compatibilidade Total Verificada  
**Próxima Revisão**: Conforme evolução do sistema  
**🔗 Referência**: Totalmente alinhado com diagrama_fluxo_recebimento_mensagem.mmd  
**📋 Melhorias Principais**: 
- **Verificação de Atendente Responsável (2.3-2.6)**: Sistema direciona automaticamente para atendente definido
- **Classificação de Intent (6.1)**: Sistema inteligente distingue PERGUNTA vs AGRADECIMENTO/SATISFAÇÃO vs TRANSFERÊNCIA
- **Intent de Transferência (6.1.1)**: Detecta solicitações de mudança de setor automaticamente
- **Busca por Setor (7.1.1-7.1.2)**: Sistema pode filtrar atendentes por especialização
- **Transferência entre Atendentes (8.3-8.8)**: Atendentes podem transferir conversas entre si
- **Encerramento Direto**: Sinais de satisfação direcionam automaticamente para encerramento (6.3 → 9)
- **Fluxo Simplificado**: Bot retorna para início (6.9.1) passando por classificação intent
- **Loop Otimizado**: Elimina redundâncias com classificação centralizada
- **Controle Hierárquico**: Fluxos finais distintos - Bot (6.9 simplificado) vs Humano (8.x controle manual)
- **Loops hierárquicos**: 6.9.1, 7.4.1, 8.1.3-8.1.4, 8.10.1 para melhor organização
