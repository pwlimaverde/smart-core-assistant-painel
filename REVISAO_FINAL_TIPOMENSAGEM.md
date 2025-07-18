# Atualização Final da Classe TipoMensagem

## Revisão Completa Conforme Tabela da API

A classe `TipoMensagem` foi completamente revisada e atualizada para estar 100% conforme a tabela oficial da API. Todas as divergências foram corrigidas.

## ✅ Alterações Realizadas

### 1. **Novos Tipos Adicionados**
- **TEXTO_SIMPLES** (`conversation`) - Mensagens de texto sem formatação
- **STATUS** (`statusMessage`) - Envia conteúdo ao status (modo story)

### 2. **Tipos Renomeados para Maior Clareza**
- `TEXTO` → `TEXTO_ESTENDIDO` (`extendedTextMessage`)
- `ADESIVO` → `STICKER` (`stickerMessage`) 
- `INTERATIVA_BOTOES` → `BOTAO` (`buttonsMessage`)
- `INTERATIVA_LISTA` → `LISTA` (`listMessage`)

### 3. **Chaves API Corrigidas**
- `reactionMessage` → `reactMessage`
- `pollCreationMessage` → `pollMessage`

### 4. **Tipo Removido**
- `TEMPLATE` (`templateMessage`) - Não estava na tabela oficial

## 📋 Tabela Completa Implementada

| **Tipo de Mensagem** | **Enum** | **Chave API** | **Descrição** |
|----------------------|----------|---------------|---------------|
| Texto estendido | `TEXTO_ESTENDIDO` | `extendedTextMessage` | Mensagens de texto simples ou formatadas |
| Texto simples | `TEXTO_SIMPLES` | `conversation` | Mensagens de texto sem formatação |
| Imagem | `IMAGEM` | `imageMessage` | Envia imagem (PNG, JPG); aceita caption opcional |
| Vídeo | `VIDEO` | `videoMessage` | Envia vídeo; aceita legenda |
| Áudio | `AUDIO` | `audioMessage` | Envia arquivo de áudio (mp3, opus, etc.) |
| Documento | `DOCUMENTO` | `documentMessage` | Envia qualquer tipo de arquivo (PDF, DOCX etc.) |
| Sticker | `STICKER` | `stickerMessage` | Envia stickers (WebP) |
| Localização | `LOCALIZACAO` | `locationMessage` | Envia localização geográfica com lat/long |
| Contato | `CONTATO` | `contactMessage` | Envia cartão de contato vCard |
| Lista | `LISTA` | `listMessage` | Mensagem com seleção de opções em lista |
| Botão | `BOTAO` | `buttonsMessage` | Mensagem com botões clicáveis |
| Enquete | `ENQUETE` | `pollMessage` | Envia enquete com alternativa de escolha |
| Reação | `REACAO` | `reactMessage` | Envia reação (emoji) a uma mensagem existente |
| Status (Story) | `STATUS` | `statusMessage` | Envia conteúdo ao status (modo story) |
| Sistema | `SISTEMA` | `sistema` | Mensagem do Sistema |

## 🔄 Compatibilidade e Migração

### Código Atualizado Automaticamente
Os seguintes arquivos foram atualizados para usar `TEXTO_ESTENDIDO` ao invés de `TEXTO`:

- ✅ `models.py` - Todos os defaults e referências
- ✅ `tests_chatbot.py` - Testes atualizados
- ✅ `management/commands/chatbot.py` - Comando de chatbot
- ✅ `examples/chatbot_usage.py` - Exemplos de uso

### Migração Necessária para Código Externo

Se você tem código que usa os tipos antigos, precisará fazer as seguintes alterações:

```python
# ANTES (não funciona mais)
TipoMensagem.TEXTO
TipoMensagem.ADESIVO
TipoMensagem.INTERATIVA_BOTOES
TipoMensagem.INTERATIVA_LISTA

# DEPOIS (novo padrão)
TipoMensagem.TEXTO_ESTENDIDO    # Para texto formatado
TipoMensagem.TEXTO_SIMPLES      # Para texto simples
TipoMensagem.STICKER
TipoMensagem.BOTAO
TipoMensagem.LISTA
```

## 📝 Exemplos de Uso Atualizados

### 1. Processamento de Mensagens Recebidas

```python
def processar_webhook(dados):
    """Processa mensagem recebida via webhook."""
    chave_tipo = dados.get('message_type')
    
    # Converte chave da API para tipo interno
    tipo = TipoMensagem.obter_por_chave_json(chave_tipo)
    
    if tipo == TipoMensagem.TEXTO_ESTENDIDO:
        processar_texto_formatado(dados)
    elif tipo == TipoMensagem.TEXTO_SIMPLES:
        processar_texto_simples(dados)
    elif tipo == TipoMensagem.BOTAO:
        processar_botoes(dados)
    elif tipo == TipoMensagem.LISTA:
        processar_lista(dados)
    elif tipo == TipoMensagem.STATUS:
        processar_status(dados)
    # ... outros tipos
```

### 2. Envio de Diferentes Tipos de Mensagem

```python
# Texto simples
enviar_mensagem(TipoMensagem.TEXTO_SIMPLES, "Olá!")

# Texto formatado
enviar_mensagem(TipoMensagem.TEXTO_ESTENDIDO, "*Texto em negrito*")

# Botões interativos
enviar_mensagem(TipoMensagem.BOTAO, {
    "text": "Escolha uma opção:",
    "buttons": [{"id": "1", "text": "Opção 1"}]
})

# Status/Story
enviar_mensagem(TipoMensagem.STATUS, {
    "type": "image",
    "url": "https://exemplo.com/imagem.jpg"
})
```

### 3. Validação de Tipos

```python
def validar_tipo_suportado(chave_api):
    """Valida se o tipo de mensagem é suportado."""
    tipo = TipoMensagem.obter_por_chave_json(chave_api)
    
    if not tipo:
        return False, f"Tipo '{chave_api}' não suportado"
    
    # Tipos interativos requerem processamento especial
    tipos_interativos = [
        TipoMensagem.BOTAO,
        TipoMensagem.LISTA,
        TipoMensagem.ENQUETE
    ]
    
    if tipo in tipos_interativos:
        return True, f"Tipo interativo: {tipo.label}"
    
    return True, f"Tipo suportado: {tipo.label}"
```

## 🧪 Validação e Testes

### Teste de Conformidade
Execute o teste de conformidade para verificar se tudo está correto:

```bash
python teste_conformidade_tipomensagem.py
```

**Resultado esperado:** ✅ TODOS OS TESTES PASSARAM!

### Testes Unitários
Todos os testes existentes foram atualizados e passam:

```bash
python manage.py test oraculo.tests_chatbot
```

## 🔍 Verificação Final

A implementação atual está 100% conforme a tabela da API:

✅ **15 tipos implementados** (todos da tabela)  
✅ **Chaves API corretas** (sem divergências)  
✅ **Métodos de conversão funcionando** (bidirecional)  
✅ **Código atualizado** (sem referências antigas)  
✅ **Testes passando** (validação completa)  

## 📚 Documentação dos Métodos

### `obter_por_chave_json(chave_json: str)`
```python
# Exemplos de uso
TipoMensagem.obter_por_chave_json('conversation')        # TEXTO_SIMPLES
TipoMensagem.obter_por_chave_json('extendedTextMessage') # TEXTO_ESTENDIDO
TipoMensagem.obter_por_chave_json('buttonsMessage')     # BOTAO
TipoMensagem.obter_por_chave_json('statusMessage')      # STATUS
```

### `obter_chave_json(tipo_mensagem)`
```python
# Exemplos de uso
TipoMensagem.obter_chave_json(TipoMensagem.TEXTO_SIMPLES)   # 'conversation'
TipoMensagem.obter_chave_json(TipoMensagem.TEXTO_ESTENDIDO) # 'extendedTextMessage'
TipoMensagem.obter_chave_json(TipoMensagem.BOTAO)          # 'buttonsMessage'
TipoMensagem.obter_chave_json(TipoMensagem.STATUS)         # 'statusMessage'
```

---

**✅ A classe TipoMensagem está agora completamente alinhada com a tabela oficial da API, sem divergências ou tipos faltando.**
