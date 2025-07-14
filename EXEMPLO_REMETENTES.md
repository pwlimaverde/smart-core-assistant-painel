# Exemplo de Uso - Sistema de Remetentes em Mensagens

## Visão Geral

O sistema agora possui um controle claro de quem está enviando mensagens, com 3 tipos de remetente:
- **CLIENTE**: Mensagens enviadas pelo cliente
- **BOT**: Mensagens enviadas pelo bot/sistema automatizado
- **ATENDENTE_HUMANO**: Mensagens enviadas por atendentes humanos

## Funcionalidades Principais

### 1. Controle de Interação do Bot
Quando um atendente humano envia uma mensagem no atendimento, o bot automaticamente para de responder nesse atendimento.

### 2. Identificação Clara de Remetentes
Cada mensagem tem um campo `remetente` que identifica exatamente quem a enviou.

## Exemplos de Uso

### Processar Mensagem do Cliente
```python
from oraculo.models import processar_mensagem_whatsapp, TipoRemetente

# Mensagem do cliente (padrão)
mensagem = processar_mensagem_whatsapp(
    numero_telefone="+5511999999999",
    conteudo="Olá, preciso de ajuda",
    remetente=TipoRemetente.CLIENTE  # Opcional, é o padrão
)
```

### Enviar Mensagem do Bot
```python
from oraculo.models import Mensagem, TipoRemetente, TipoMensagem

# Criar mensagem do bot
mensagem_bot = Mensagem.objects.create(
    atendimento=atendimento,
    tipo=TipoMensagem.TEXTO,
    conteudo="Olá! Como posso ajudar você hoje?",
    remetente=TipoRemetente.BOT
)
```

### Enviar Mensagem de Atendente Humano
```python
from oraculo.models import enviar_mensagem_atendente

# Usar função especializada
mensagem_atendente = enviar_mensagem_atendente(
    atendimento=atendimento,
    atendente_humano=atendente,
    conteudo="Olá! Sou João, vou ajudar você agora."
)
```

### Verificar se Bot Pode Responder
```python
from oraculo.models import pode_bot_responder_atendimento

# Verificar se bot pode responder no atendimento
if pode_bot_responder_atendimento(atendimento):
    # Bot pode responder
    print("Bot pode responder")
else:
    # Atendente humano já interagiu, bot não deve responder
    print("Atendente humano assumiu o atendimento")
```

### Verificar Tipo de Remetente
```python
# Usando propriedades da mensagem
if mensagem.is_from_client:
    print("Mensagem do cliente")
elif mensagem.is_from_bot:
    print("Mensagem do bot")
elif mensagem.is_from_atendente_humano:
    print("Mensagem de atendente humano")

# Ou usando o campo diretamente
if mensagem.remetente == TipoRemetente.CLIENTE:
    print("Mensagem do cliente")
```

## Migração do Código Existente

### Campo is_from_client (Compatibilidade)
O campo `is_from_client` foi mantido como propriedade para compatibilidade:

```python
# Código antigo continua funcionando
if mensagem.is_from_client:
    print("Mensagem do cliente")

# Equivale ao novo código
if mensagem.remetente == TipoRemetente.CLIENTE:
    print("Mensagem do cliente")
```

## Fluxo de Trabalho Recomendado

1. **Mensagem do Cliente**: Usa `TipoRemetente.CLIENTE`
2. **Bot Responde**: Verifica `pode_bot_responder_atendimento()` antes de responder
3. **Transferência para Humano**: Atendente assume o atendimento
4. **Atendente Responde**: Usa `TipoRemetente.ATENDENTE_HUMANO`
5. **Bot Para de Responder**: Automaticamente detecta e para de interagir

## Benefícios

✅ **Clareza**: Identificação precisa de quem enviou cada mensagem
✅ **Controle**: Bot para automaticamente quando atendente assume
✅ **Compatibilidade**: Código existente continua funcionando
✅ **Flexibilidade**: Suporte a novos tipos de remetente no futuro
✅ **Auditoria**: Histórico completo de quem participou de cada conversa
