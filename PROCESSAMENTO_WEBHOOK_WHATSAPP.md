# Processamento de Mensagens do WhatsApp via Webhook

## Visão Geral

Este documento explica como o sistema processa diferentes tipos de mensagens recebidas do WhatsApp através do webhook. A implementação suporta vários tipos de conteúdo, incluindo texto, imagem, vídeo, áudio e documentos.

## Fluxo de Processamento

### 1. Recebimento da Mensagem

O webhook recebe uma requisição POST contendo dados JSON da mensagem do WhatsApp. A estrutura básica é:

```json
{
  "data": {
    "key": {
      "remoteJid": "5511999999999@s.whatsapp.net",
      "id": "message-id-123"
    },
    "message": {
      "tipoMensagem": {
        // Conteúdo específico do tipo
      }
    }
  }
}
```

### 2. Extração de Dados Básicos

- **Número de Telefone**: Extraído de `data.key.remoteJid` (removendo o sufixo `@s.whatsapp.net`)
- **ID da Mensagem**: Extraído de `data.key.id`
- **Tipo de Mensagem**: Identificado pela primeira chave dentro do objeto `message`

### 3. Conversão do Tipo de Mensagem

A chave JSON do tipo de mensagem é convertida para o enum `TipoMensagem` interno usando o método `TipoMensagem.obter_por_chave_json()`.

### 4. Extração de Conteúdo por Tipo

Dependendo do tipo de mensagem, o conteúdo e metadados são extraídos de forma específica:

#### Texto (`extendedTextMessage`)

```python
conteudo = message_data.get('text', '')
```

#### Imagem (`imageMessage`)

```python
conteudo = message_data.get('caption', 'Imagem recebida')
metadados['mimetype'] = message_data.get('mimetype')
metadados['url'] = message_data.get('url')
metadados['fileLength'] = message_data.get('fileLength')
```

#### Vídeo (`videoMessage`)

```python
conteudo = message_data.get('caption', 'Vídeo recebido')
metadados['mimetype'] = message_data.get('mimetype')
metadados['url'] = message_data.get('url')
metadados['seconds'] = message_data.get('seconds')
metadados['fileLength'] = message_data.get('fileLength')
```

#### Áudio (`audioMessage`)

```python
conteudo = "Áudio recebido"
metadados['mimetype'] = message_data.get('mimetype')
metadados['url'] = message_data.get('url')
metadados['seconds'] = message_data.get('seconds')
metadados['ptt'] = message_data.get('ptt', False)  # Se é mensagem de voz
```

#### Documento (`documentMessage`)

```python
conteudo = message_data.get('fileName', 'Documento recebido')
metadados['mimetype'] = message_data.get('mimetype')
metadados['url'] = message_data.get('url')
metadados['fileLength'] = message_data.get('fileLength')
```

### 5. Processamento da Mensagem

Após a extração dos dados, a mensagem é processada usando a função `processar_mensagem_whatsapp()` com os seguintes parâmetros:

```python
mensagem = processar_mensagem_whatsapp(
    numero_telefone=phone,
    conteudo=conteudo,
    tipo_mensagem=tipo_mensagem,
    message_id=message_id,
    metadados=metadados,
    remetente=TipoRemetente.CLIENTE
)
```

Esta função:
1. Busca um atendimento ativo para o número de telefone
2. Se não existir, inicializa um novo atendimento
3. Cria um objeto `Mensagem` com os dados fornecidos
4. Atualiza o timestamp da última interação do cliente

## Processamento de Mídia

Para mensagens de mídia (imagem, vídeo, áudio, documento), o sistema:

1. Armazena os metadados da mídia (URL, tipo MIME, tamanho, etc.)
2. Usa o caption como conteúdo para imagens e vídeos, quando disponível
3. Usa o nome do arquivo como conteúdo para documentos

## Conversão para Texto via IA

O sistema prevê a conversão de conteúdo multimídia para texto usando IA:

- **Áudio**: Transcrição via Speech-to-Text
- **Imagem**: Análise e descrição via Computer Vision
- **Vídeo**: Extração da trilha de áudio e transcrição
- **Documento**: Extração de texto via OCR/parsing

## Testes

Para testar o processamento de diferentes tipos de mensagens, execute:

```bash
python teste_webhook_tipos_mensagem.py
```

Este script simula requisições webhook para diferentes tipos de mensagens e verifica se o processamento está correto.

## Próximos Passos

1. **Implementar Geração de Resposta Automática**: Integrar com IA para gerar respostas automáticas
2. **Download de Mídia**: Implementar download e armazenamento local de arquivos de mídia
3. **Conversão de Mídia para Texto**: Integrar com serviços de IA para converter mídia em texto
4. **Notificações para Atendentes**: Alertar atendentes sobre novas mensagens

## Referências

- [Documentação da API do WhatsApp](https://developers.facebook.com/docs/whatsapp/)
- [Documentação da Evolution API](https://docs.evolution-api.com/)