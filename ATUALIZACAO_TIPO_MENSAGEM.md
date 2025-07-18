# Atualização da Classe TipoMensagem

## Resumo das Alterações

A classe `TipoMensagem` foi atualizada para incluir todos os tipos de mensagem suportados pela API do WhatsApp/Evolution API, conforme a tabela de referência fornecida.

## Novos Tipos de Mensagem

A classe agora inclui os seguintes tipos:

| Tipo de Mensagem | Chave JSON | Descrição |
|------------------|------------|-----------|
| TEXTO | `extendedTextMessage` | Mensagens de texto simples ou formatado |
| AUDIO | `audioMessage` | Mensagens de voz ou áudio |
| VIDEO | `videoMessage` | Arquivos de vídeo |
| IMAGEM | `imageMessage` | Mensagens contendo imagens |
| DOCUMENTO | `documentMessage` | Arquivos como PDF, DOC etc. |
| LOCALIZACAO | `locationMessage` | Mensagens contendo localização geográfica |
| CONTATO | `contactMessage` | Compartilhamento de contato |
| ADESIVO | `stickerMessage` | Mensagens do tipo figurinha (imagem .webp) |
| TEMPLATE | `templateMessage` | Mensagens pré-formatadas para automação |
| INTERATIVA_BOTOES | `buttonsMessage` | Mensagens com botões |
| INTERATIVA_LISTA | `listMessage` | Mensagens com listas interativas |
| REACAO | `reactionMessage` | Reação emoji a mensagens |
| ENQUETE | `pollCreationMessage` | Mensagens de criação de enquete |
| SISTEMA | `sistema` | Mensagem do Sistema |

## Novos Métodos

### `obter_por_chave_json(chave_json: str)`

Retorna o tipo de mensagem baseado na chave JSON recebida.

**Parâmetros:**
- `chave_json` (str): Chave JSON do tipo de mensagem (ex: 'extendedTextMessage')

**Retorna:**
- `TipoMensagem`: Tipo de mensagem correspondente ou `None` se não encontrado

**Exemplos:**
```python
# Obtendo tipo por chave JSON
tipo = TipoMensagem.obter_por_chave_json('extendedTextMessage')
print(tipo)  # TipoMensagem.TEXTO

tipo = TipoMensagem.obter_por_chave_json('audioMessage')
print(tipo)  # TipoMensagem.AUDIO

# Chave inexistente
tipo = TipoMensagem.obter_por_chave_json('chave_inexistente')
print(tipo)  # None
```

### `obter_chave_json(tipo_mensagem)`

Retorna a chave JSON correspondente ao tipo de mensagem.

**Parâmetros:**
- `tipo_mensagem`: Tipo de mensagem do enum

**Retorna:**
- `str`: Chave JSON correspondente ou `None` se não encontrado

**Exemplos:**
```python
# Obtendo chave JSON por tipo
chave = TipoMensagem.obter_chave_json(TipoMensagem.TEXTO)
print(chave)  # 'extendedTextMessage'

chave = TipoMensagem.obter_chave_json(TipoMensagem.AUDIO)
print(chave)  # 'audioMessage'
```

## Casos de Uso

### 1. Processamento de Mensagens Recebidas

```python
def processar_mensagem_recebida(dados_webhook):
    """Processa mensagem recebida via webhook."""
    
    # Extrai a chave JSON da mensagem
    chave_tipo = None
    for key in dados_webhook.get('message', {}):
        if key.endswith('Message'):
            chave_tipo = key
            break
    
    if chave_tipo:
        # Converte para o tipo interno
        tipo_mensagem = TipoMensagem.obter_por_chave_json(chave_tipo)
        
        if tipo_mensagem:
            print(f"Mensagem do tipo: {tipo_mensagem.label}")
            
            # Processa de acordo com o tipo
            if tipo_mensagem == TipoMensagem.TEXTO:
                processar_texto(dados_webhook['message']['extendedTextMessage'])
            elif tipo_mensagem == TipoMensagem.AUDIO:
                processar_audio(dados_webhook['message']['audioMessage'])
            # ... outros tipos
```

### 2. Envio de Mensagens

```python
def enviar_mensagem(tipo_mensagem, conteudo):
    """Envia mensagem através da API."""
    
    # Obtém a chave JSON para a API
    chave_json = TipoMensagem.obter_chave_json(tipo_mensagem)
    
    if chave_json:
        payload = {
            'number': numero_destino,
            'message': {
                chave_json: conteudo
            }
        }
        
        # Envia via API
        response = requests.post(api_url, json=payload)
```

### 3. Validação e Logging

```python
def validar_tipo_mensagem(chave_json):
    """Valida se o tipo de mensagem é suportado."""
    
    tipo = TipoMensagem.obter_por_chave_json(chave_json)
    
    if tipo:
        logger.info(f"Tipo de mensagem válido: {tipo.label}")
        return True
    else:
        logger.warning(f"Tipo de mensagem não suportado: {chave_json}")
        return False
```

## Migração de Código Existente

Se você tinha código que usava os valores antigos, será necessário fazer as seguintes alterações:

**Antes:**
```python
if mensagem.tipo == TipoMensagem.TEXTO:  # valor era 'texto'
    processar_texto(mensagem)
```

**Depois:**
```python
if mensagem.tipo == TipoMensagem.TEXTO:  # valor agora é 'extendedTextMessage'
    processar_texto(mensagem)
```

**Ou se você quiser manter compatibilidade:**
```python
# Converte valor antigo para novo
if mensagem.tipo == 'texto':
    mensagem.tipo = TipoMensagem.TEXTO
```

## Observações Importantes

1. **Valores Alterados**: Os valores dos enum foram alterados para corresponder às chaves JSON da API
2. **Compatibilidade**: Código existente que dependia dos valores antigos precisará ser atualizado
3. **Performance**: Os métodos são otimizados para uso frequente
4. **Extensibilidade**: Novos tipos podem ser facilmente adicionados seguindo o padrão estabelecido

## Testing

Para testar a funcionalidade, você pode usar o arquivo `teste_tipo_mensagem.py` incluído no projeto:

```bash
cd /caminho/para/projeto
python teste_tipo_mensagem.py
```

Este teste verifica:
- Conversão de chave JSON para tipo
- Conversão de tipo para chave JSON  
- Correspondência bidirecional
- Tratamento de valores inválidos
