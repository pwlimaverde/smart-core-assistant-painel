# Correções no Processamento de Mensagens WhatsApp

## Problema Identificado

A IA não estava extraindo mais os dados das mensagens devido a inconsistências no processamento da estrutura JSON do webhook do WhatsApp.

### Estrutura JSON Correta

```json
{
  "event": "messages.upsert",
  "instance": "arcane",
  "data": {
    "key": {
      "remoteJid": "5516992805443@s.whatsapp.net",
      "fromMe": false,
      "id": "5F2AAA4BD98BB388BBCD6FCB9B4ED676"
    },
    "pushName": "xpto",
    "message": {
      "extendedTextMessage": {
        "text": "Meu nome é Paulo Weslley"
      }
    },
    "messageType": "conversation",
    "messageTimestamp": 1748739583
  }
}
```

### Problema Principal

- O campo `messageType` indicava "conversation"
- Mas a estrutura real da mensagem era `extendedTextMessage`
- O sistema estava priorizando o `messageType` em vez da estrutura real
- Isso causava extração incorreta do conteúdo da mensagem

## Correções Implementadas

### 1. Priorização da Estrutura Real da Mensagem

**Antes:**
```python
# Priorizava messageType sobre a estrutura real
tipo_chave = data_section.get('messageType')
if not tipo_chave:
    message_keys = message_section.keys()
    tipo_chave = list(message_keys)[0] if message_keys else None
```

**Depois:**
```python
# Prioriza a estrutura real da mensagem
message_keys = message_section.keys()
tipo_chave = list(message_keys)[0] if message_keys else None

# Se não conseguiu detectar da estrutura, usar messageType como fallback
if not tipo_chave:
    tipo_chave = data_section.get('messageType')
```

### 2. Melhoria na Extração de Conteúdo

**Antes:**
```python
if tipo_mensagem == TipoMensagem.TEXTO_FORMATADO:
    if tipo_chave == 'conversation':
        conteudo = message_data if isinstance(message_data, str) else str(message_data)
    else:
        conteudo = message_data.get('text', '')
```

**Depois:**
```python
if tipo_mensagem == TipoMensagem.TEXTO_FORMATADO:
    if tipo_chave == 'conversation':
        conteudo = message_data if isinstance(message_data, str) else str(message_data)
    elif tipo_chave == 'extendedTextMessage':
        conteudo = message_data.get('text', '')
    else:
        conteudo = message_data.get('text', str(message_data) if message_data else '')
```

### 3. Logs Aprimorados

Adicionados logs mais detalhados para debugging:

```python
logger.info(
    f"Processamento de mensagem - Telefone: {phone}, Tipo detectado: {tipo_chave}, "
    f"Tipo mapeado: {tipo_mensagem}, PushName: '{push_name}', "
    f"Conteúdo: {conteudo[:50]}...")
```

## Resultado Esperado

Com essas correções:

1. ✅ O sistema detecta corretamente `extendedTextMessage` como o tipo real da mensagem
2. ✅ Extrai corretamente o conteúdo de `data.message.extendedTextMessage.text`
3. ✅ Armazena o `pushName` como `nome_perfil_whatsapp` no contato
4. ✅ O texto "Meu nome é Paulo Weslley" é processado para extração de entidades
5. ✅ A IA pode extrair a entidade "cliente": "Paulo Weslley"

## Teste

Para testar, envie uma mensagem via webhook com a estrutura JSON fornecida. O sistema deve:

- Detectar `extendedTextMessage` (não `conversation`)
- Extrair corretamente o texto "Meu nome é Paulo Weslley"
- Processar o nome "Paulo Weslley" como entidade cliente
- Armazenar "xpto" como nome_perfil_whatsapp
- Atualizar o campo nome do contato com "Paulo Weslley"

## Verificação

Nos logs, você deve ver:

```
Processamento de mensagem - Telefone: 5516992805443, Tipo detectado: extendedTextMessage, 
Tipo mapeado: TipoMensagem.TEXTO_FORMATADO, PushName: 'xpto', 
Conteúdo: Meu nome é Paulo Weslley...
```

Em vez do anterior que mostrava `Tipo: conversation` incorretamente.
