# Análise do JSON de Webhook WhatsApp

## JSON Recebido

```json
{
   "event":"messages.upsert",
   "instance":"5588921729550",
   "data":{
     "key":{
       "remoteJid":"558897141275@s.whatsapp.net",
       "fromMe":false,
       "id":"55F3FB668576571711D16311A726B61d"
     },
     "pushName":"Paulo Weslley Limaverde",
     "message":{
       "conversation":"Qual o horário de funcionamento?",
       "messageContextInfo":{
         "deviceListMetadata":{
           "senderKeyHash":"3kLrJd5ais+GVw==",
           "senderTimestamp":"1753814692",
           "recipientKeyHash":"R63nxd0XafOzSg==",
           "recipientTimestamp":"1754438427"
         },
         "deviceListMetadataVersion":2,
         "messageSecret":"PLN05Qym4RjgniY5a+x5TudfziFRZ1CFollAQdm7/2E="
       }
     },
     "messageType":"conversation",
     "messageTimestamp":1754518764,
     "instanceId":"33ba19f5-8c6f-4b9f-a895-be46e0324607",
     "source":"android"
   },
   "destination":" `http://django-app:8000/oraculo/webhook_whatsapp/` ",
   "date_time":"2025-08-06T19:19:25.397Z",
   "sender":"5588921729550@s.whatsapp.net",
   "server_url":"http://localhost:8080",
   "apikey":"C4AFECA8B7FD-4644-AA6C-6DF92A4AC90F"
}
```

## Análise da Compatibilidade

### ✅ Campos Obrigatórios Presentes

O JSON está **compatível** com a função `nova_mensagem`. Todos os campos obrigatórios estão presentes:

1. **`data`** - ✅ Presente
2. **`data.key`** - ✅ Presente
3. **`data.key.remoteJid`** - ✅ Presente (`"558897141275@s.whatsapp.net"`)
4. **`data.key.id`** - ✅ Presente (`"55F3FB668576571711D16311A726B61d"`)
5. **`data.pushName`** - ✅ Presente (`"Paulo Weslley Limaverde"`)
6. **`data.message`** - ✅ Presente
7. **`data.messageTimestamp`** - ✅ Presente (`1754518764`)

### ✅ Processamento do Tipo de Mensagem

A função `nova_mensagem` processará corretamente este JSON:

1. **Detecção do tipo**: A primeira chave em `data.message` é `"conversation"`, que será detectada como `tipo_chave`
2. **Mapeamento**: `"conversation"` está mapeada para `TipoMensagem.TEXTO_FORMATADO` no método `obter_por_chave_json`
3. **Extração do conteúdo**: O texto `"Qual o horário de funcionamento?"` será extraído corretamente
4. **Extração do telefone**: `"558897141275"` será extraído do `remoteJid`

### ✅ Metadados Adicionais

Os seguintes metadados serão capturados:
- `messageTimestamp`: `1754518764`
- Outros campos como `messageContextInfo` não são processados pela função atual, mas não causam erro

## Sugestões de Melhorias (Opcionais)

### 1. Validação de Timestamp

**Problema**: O timestamp `1754518764` parece estar no futuro (ano 2025), o que pode indicar um problema de sincronização.

**Sugestão**: Adicionar validação de timestamp razoável:

```python
import time

# Adicionar na função nova_mensagem
message_timestamp = data_section.get("messageTimestamp")
if message_timestamp:
    current_timestamp = int(time.time())
    # Verificar se o timestamp não está muito no futuro (mais de 1 dia)
    if message_timestamp > current_timestamp + 86400:
        logger.warning(f"Timestamp da mensagem parece estar no futuro: {message_timestamp}")
```

### 2. Captura de Metadados Adicionais

**Sugestão**: Capturar metadados adicionais que podem ser úteis:

```python
# Adicionar aos metadados
metadados["instanceId"] = data_section.get("instanceId")
metadados["source"] = data_section.get("source")
metadados["fromMe"] = key_section.get("fromMe", False)

# Capturar informações de contexto se disponíveis
if "messageContextInfo" in message_section.get(tipo_chave, {}):
    metadados["messageContextInfo"] = message_section[tipo_chave]["messageContextInfo"]
```

### 3. Validação do Campo `destination`

**Problema**: O campo `destination` contém espaços e backticks desnecessários:
```
"destination":" `http://django-app:8000/oraculo/webhook_whatsapp/` "
```

**Sugestão**: Limpar o campo se for usado:
```python
destination = data.get("destination", "").strip().strip("`")
```

### 4. Logging Melhorado

**Sugestão**: Adicionar logs mais detalhados para debug:

```python
logger.info(f"Processando mensagem de {phone} - Tipo: {tipo_chave} - ID: {message_id}")
logger.debug(f"Conteúdo extraído: {conteudo[:50]}...")
```

## Conclusão

**✅ O JSON está TOTALMENTE COMPATÍVEL** com a função `nova_mensagem` e será processado corretamente sem necessidade de ajustes.

### Processamento Esperado:

1. **Telefone extraído**: `558897141275`
2. **Tipo de mensagem**: `TipoMensagem.TEXTO_FORMATADO`
3. **Conteúdo**: `"Qual o horário de funcionamento?"`
4. **Nome do perfil**: `"Paulo Weslley Limaverde"`
5. **Message ID**: `"55F3FB668576571711D16311A726B61d"`
6. **Metadados**: `{"messageTimestamp": 1754518764}`

A função criará um novo atendimento (se não existir) e uma nova mensagem no sistema, permitindo que o bot ou atendente humano responda adequadamente à pergunta sobre horário de funcionamento.

## Campos Não Utilizados (Mas Não Problemáticos)

Os seguintes campos estão presentes no JSON mas não são processados pela função atual:
- `event`
- `instance`
- `data.key.fromMe`
- `data.message.messageContextInfo`
- `data.instanceId`
- `data.source`
- `destination`
- `date_time`
- `sender`
- `server_url`
- `apikey`

Estes campos podem ser úteis para validações adicionais ou logging, mas não afetam o processamento principal da mensagem.