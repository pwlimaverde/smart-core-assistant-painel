# Fluxograma do Webhook WhatsApp - Notas Técnicas

## Visão Geral

Este documento complementa o diagrama `fluxograma_webhook_whatsapp.mmd` com explicações detalhadas sobre cada etapa do processamento de mensagens recebidas pelo webhook do WhatsApp.

## Arquitetura em Camadas

### 1. Camada de Entrada (1.x)
**Responsabilidade**: Validação inicial e parsing de dados

- **1.1 Validar API Key**: Função `_validar_api_key()` verifica autenticidade da requisição
- **1.2 API Key Válida?**: Decisão baseada na validação da chave de API
- **1.3 Parse JSON Request**: Conversão dos dados da requisição para formato JSON
- **1.4 JSON Válido?**: Verificação da integridade dos dados recebidos

### 2. Camada de Orquestração (2.x)
**Responsabilidade**: Coordenação do fluxo e roteamento inicial

- **2.1 Chamar nova_mensagem**: Invocação da função principal de processamento
- **2.2 Extrair Dados da Mensagem**: Extração de metadados (ID, remetente, timestamp)
- **2.3 Tipo de Mensagem?**: Classificação baseada no tipo de conteúdo recebido
- **2.4 Inicializar Atendimento WhatsApp**: Preparação do contexto de atendimento
- **2.5 Normalizar Telefone**: Formatação do número de telefone
- **2.6 Buscar/Criar Contato**: Gestão de dados do contato
- **2.7 Atendimento Ativo?**: Verificação de atendimento existente
- **2.8 Usar Atendimento Existente**: Reutilização de contexto
- **2.9 Criar Novo Atendimento**: Criação de novo atendimento

### 3. Camada de Processamento (3.x)
**Responsabilidade**: Processamento específico por tipo e persistência

#### Subprocessos por Tipo de Mensagem:
- **3.1 Processar Texto**: Extração de conteúdo textual
- **3.2 Processar Mídia**: Tratamento de imagens, vídeos, áudios, documentos
- **3.3 Processar Localização**: Extração de coordenadas geográficas
- **3.4 Processar Contato**: Processamento de informações de contato compartilhado
- **3.5 Processar Interativo**: Tratamento de listas, botões, polls
- **3.6 Processar Reação**: Processamento de emojis de reação

#### Persistência e Relacionamentos:
- **3.7 Chamar processar_mensagem_whatsapp**: Função de persistência principal
- **3.8 Tipo de Remetente?**: Classificação (contato, bot, agente humano)
- **3.9 Criar Mensagem**: Persistência da mensagem no banco
- **3.10 Mensagem Duplicada?**: Verificação de duplicação
- **3.11 Atualizar Última Interação**: Timestamp da última atividade
- **3.12 Primeira Mensagem?**: Verificação para inicialização de atendimento
- **3.13 Atualizar Status Atendimento**: Mudança de status quando necessário

### 4. Camada de Análise IA (4.x)
**Responsabilidade**: Processamento inteligente e extração de insights

#### Preparação e Contexto:
- **4.1 Chamar _analisar_conteudo_mensagem**: Função principal de análise
- **4.2 Carregar Histórico**: Recuperação do contexto conversacional
- **4.3 Conteúdo Não-Textual?**: Verificação de necessidade de conversão
- **4.4 Converter Contexto**: Função `_converter_contexto()` para mídia
- **4.5 Primeira Interação?**: Verificação se é o primeiro contato
- **4.6 Mensagem Apresentação**: Envio de mensagem de boas-vindas

#### Processamento IA:
- **4.7 Chamar FeaturesCompose**: Orquestrador de funcionalidades IA
- **4.8 Configurar LLM**: Configuração de parâmetros do modelo
- **4.9 Chamar AnalisePreviaMensagem**: Análise principal via LLM
- **4.10 Formatar Histórico para LLM**: Preparação do contexto
- **4.11 Processar Resposta LLM**: Interpretação da resposta do modelo
- **4.12 Extrair Intent e Entidades**: Parsing de intenções e entidades

#### Persistência de Análise:
- **4.13 Atualizar Mensagem com Análise**: Salvamento dos insights
- **4.14 Obter Entidades Válidas**: Função `_obter_entidades_metadados_validas()`
- **4.15 Processar Entidades do Contato**: Função `_processar_entidades_contato()`
- **4.16 Atualizar Metadados do Contato**: Enriquecimento do perfil
- **4.17 Nome Contato Vazio?**: Verificação da completude dos dados
- **4.18 Solicitar Informações**: Envio de solicitação de dados

---

## 🏗️ Detalhamento: inicializar_atendimento_whatsapp

### Função Principal
```python
inicializar_atendimento_whatsapp(
    numero_telefone: str,
    primeira_mensagem: str = "",
    metadata_contato: Optional[dict[str, Any]] = None,
    nome_contato: Optional[str] = None,
    nome_perfil_whatsapp: Optional[str] = None,
) -> tuple["Contato", "Atendimento"]
```

### Fluxo Detalhado

#### 1. Normalização do Telefone
- **Regex**: `re.sub(r"\D", "", numero_telefone)` - Remove caracteres não numéricos
- **Validação**: Adiciona prefixo "55" se não presente
- **Formatação**: Adiciona "+" no início
- **Resultado**: `+55XXXXXXXXXXX`

#### 2. Gestão do Contato
- **Busca**: `Contato.objects.get_or_create(telefone=telefone_formatado)`
- **Defaults**: 
  - `nome_contato`: Nome fornecido ou None
  - `nome_perfil_whatsapp`: pushName do WhatsApp
  - `metadata_contato`: Dados adicionais
- **Atualização**: Se contato existe, atualiza campos se necessário

#### 3. Verificação de Atendimento Ativo
- **Query**: Busca atendimentos com status válidos:
  - `AGUARDANDO_INICIAL`
  - `EM_ANDAMENTO`
  - `AGUARDANDO_CLIENTE`
  - `AGUARDANDO_ATENDENTE`
- **Filtro**: `contato=contato, status__in=status_validos`

#### 4. Criação de Novo Atendimento (se necessário)
- **Status Inicial**: `StatusAtendimento.AGUARDANDO_INICIAL`
- **Contexto**: Metadados específicos do WhatsApp
- **Histórico**: Entrada automática "Atendimento iniciado via WhatsApp"
- **Timestamp**: `data_inicio` automático

#### 5. Tratamento de Erros
- **Exception Handling**: Try/catch para toda a operação
- **Logging**: Registro de erros com contexto
- **Rollback**: Transações seguras para consistência

### Integrações

#### Com nova_mensagem
- **Chamada**: Após extração dos dados do webhook
- **Parâmetros**: Telefone, pushName, primeira mensagem
- **Retorno**: Tupla (contato, atendimento) para uso posterior

#### Com processar_mensagem_whatsapp
- **Dependência**: Requer contato e atendimento inicializados
- **Contexto**: Usa objetos retornados para criar mensagem
- **Status**: Pode alterar status do atendimento se primeira mensagem

### 5. Camada de Decisão (5.x)
**Responsabilidade**: Determinação do fluxo de resposta

- **5.1 Bot Pode Responder?**: Função `_pode_bot_responder_atendimento()`
- **5.2 Direcionar para Bot**: Fluxo automatizado de resposta
- **5.3 Direcionar para Humano**: Transferência para atendimento manual

### 6. Camada de Saída (6.x)
**Responsabilidade**: Direcionamento final e resposta

- **6.1 Retornar Sucesso**: Resposta HTTP 200 com confirmação

## Tratamento de Erros

### Tipos de Erro:
- **E1 Erro API Key Inválida**: Falha na autenticação
- **E2 Erro Parse JSON**: Dados malformados na requisição
- **E3 Erro Processamento**: Falhas durante o processamento
- **E4 Erro Banco de Dados**: Problemas de persistência
- **E5 Erro Análise IA**: Falhas no processamento inteligente
- **E6 Log do Erro**: Registro detalhado para debugging
- **E7 Retornar Erro**: Resposta HTTP com código de erro apropriado

### Estratégia de Recuperação:
- Todos os erros são logados para análise posterior
- Falhas não críticas permitem continuidade do fluxo
- Erros críticos resultam em resposta de erro controlada
- Conectores pontilhados indicam fluxos de exceção

## Pontos de Decisão Críticos

### Validação de Entrada:
1. **API Key**: Primeira barreira de segurança
2. **JSON Válido**: Integridade dos dados

### Classificação de Conteúdo:
1. **Tipo de Mensagem**: Determina processamento específico
2. **Tipo de Remetente**: Influencia fluxo de resposta
3. **Primeira Mensagem**: Inicialização de atendimento

### Análise Inteligente:
1. **Conteúdo Não-Textual**: Necessidade de conversão
2. **Bot Pode Responder**: Decisão final de roteamento

## Integrações Externas

### Banco de Dados:
- **Contato**: Gestão de perfis de usuários
- **Mensagem**: Histórico conversacional
- **Atendimento**: Estados de atendimento
- **Metadados**: Informações enriquecidas
- **Índices**: Otimizações para telefone, message_id_whatsapp, status

### Serviços IA:
- **LLM (Large Language Model)**: Análise de conteúdo
- **Extração de Entidades**: Identificação de dados estruturados
- **Detecção de Intenção**: Classificação de propósito
- **Entidades**: Extração automática de dados do cliente
- **Intents**: Detecção de intenções da conversa

### APIs WhatsApp:
- **Webhook**: Recebimento de mensagens
- **Metadados de Mídia**: Informações de arquivos
- **Send API**: Envio de respostas (futuro)
- **Media API**: Download de arquivos (futuro)
- **Tipos Suportados**: Texto, imagem, áudio, vídeo, documento, localização, contato, interativos

## Performance e Escalabilidade

### Otimizações:
- Validação rápida na entrada para rejeitar requisições inválidas
- Processamento assíncrono de análise IA quando possível
- Cache de entidades de metadados válidas
- Reutilização de conexões de banco de dados

### Monitoramento:
- Logs estruturados em cada etapa crítica
- Métricas de tempo de processamento
- Contadores de erro por tipo
- Alertas para falhas em cascata

## Segurança

### Validações:
- Autenticação via API Key
- Sanitização de dados de entrada
- Validação de tipos de dados
- Prevenção de injection attacks

### Auditoria:
- Log de todas as requisições
- Rastreamento de alterações em contatos
- Histórico de decisões de roteamento

## Manutenibilidade

### Modularidade:
- Funções específicas para cada tipo de processamento
- Separação clara entre camadas
- Interfaces bem definidas entre componentes

### Testabilidade:
- Pontos de injeção para mocks em testes
- Validações independentes testáveis
- Fluxos de erro reproduzíveis

### Documentação:
- Mapeamento direto entre código e diagrama
- Comentários inline nas funções críticas
- Exemplos de uso para cada tipo de mensagem

---

**Nota**: Este documento deve ser atualizado sempre que houver mudanças significativas no fluxo de processamento do webhook WhatsApp.