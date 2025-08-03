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
- **3.9 Criar/Atualizar Contato**: Gestão de dados do contato
- **3.10 Criar Mensagem**: Persistência da mensagem no banco
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

#### Processamento IA:
- **4.5 Chamar FeaturesCompose**: Orquestrador de funcionalidades IA
- **4.6 Configurar LLM**: Configuração de parâmetros do modelo
- **4.7 Chamar AnalisePreviaMensagem**: Análise principal via LLM
- **4.8 Formatar Histórico para LLM**: Preparação do contexto
- **4.9 Processar Resposta LLM**: Interpretação da resposta do modelo
- **4.10 Extrair Intent e Entidades**: Parsing de intenções e entidades

#### Persistência de Análise:
- **4.11 Atualizar Mensagem com Análise**: Salvamento dos insights
- **4.12 Obter Entidades Válidas**: Função `_obter_entidades_metadados_validas()`
- **4.13 Processar Entidades do Contato**: Função `_processar_entidades_contato()`
- **4.14 Atualizar Metadados do Contato**: Enriquecimento do perfil

### 5. Camada de Decisão (5.x)
**Responsabilidade**: Determinação do fluxo de resposta

- **5.1 Bot Pode Responder?**: Função `_pode_bot_responder_atendimento()`
- **5.2 Verificar Mensagens de Agente**: Busca por intervenções humanas
- **5.3 Verificar Agente Associado**: Verificação de atendimento humano ativo

### 6. Camada de Saída (6.x)
**Responsabilidade**: Direcionamento final e resposta

- **6.1 Direcionar para Bot**: Fluxo automatizado de resposta
- **6.2 Direcionar para Humano**: Transferência para atendimento manual
- **6.3 Retornar Sucesso**: Resposta HTTP 200 com confirmação

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

### Serviços IA:
- **LLM (Large Language Model)**: Análise de conteúdo
- **Extração de Entidades**: Identificação de dados estruturados
- **Detecção de Intenção**: Classificação de propósito

### APIs WhatsApp:
- **Webhook**: Recebimento de mensagens
- **Metadados de Mídia**: Informações de arquivos

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