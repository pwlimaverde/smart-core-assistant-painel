# Notas Explicativas - Diagrama Oráculo

## 🤖 CONTROLE DE BOT

- **Bot NÃO responde** se existir mensagem de `ATENDENTE_HUMANO` no atendimento
- Campo `confianca_resposta` determina se resposta é enviada automaticamente
- **Baixa confiança** (< 0.5) = transferir para humano
- **Alta confiança** (> 0.8) = resposta automática

## 🔄 FLUXO DE ATENDIMENTO

1. Cliente inicia → **AGUARDANDO_INICIAL**
2. Bot responde → **EM_ANDAMENTO**
3. Se transferido → **TRANSFERIDO** + `atendente_humano_id` preenchido
4. Finalização → **RESOLVIDO/CANCELADO** + `data_fim` preenchida

## 🆔 IDENTIFICAÇÃO ÚNICA

- **Cliente**: telefone (formato internacional +5511999999999)
- **Atendente**: telefone + id interno
- **Mensagem**: campo `remetente` define comportamento do sistema

## 📱 INTEGRAÇÃO WHATSAPP

- `message_id_whatsapp` para rastreamento de mensagens
- Campo `metadados` contém informações de mídia, localização, etc.
- Suporte a todos os tipos de mensagem WhatsApp (texto, imagem, áudio, vídeo, documento, localização, contato)

## 🎯 REGRAS DE NEGÓCIO IMPORTANTES

### Quando o Bot Para de Responder:
```
Se EXISTE mensagem com remetente = 'atendente_humano' no atendimento:
    Bot NÃO responde mais automaticamente
    Todas as próximas respostas devem vir do atendente humano
```

### Controle de Confiança:
```
Se confianca_resposta < 0.5:
    Transferir automaticamente para atendente humano
    
Se confianca_resposta >= 0.8:
    Enviar resposta automaticamente
    
Se 0.5 <= confianca_resposta < 0.8:
    Pode precisar de revisão (regra customizável)
```

### Gestão de Status:
- **AGUARDANDO_INICIAL**: Primeiro contato do cliente
- **EM_ANDAMENTO**: Conversa ativa com bot ou atendente
- **AGUARDANDO_CLIENTE**: Esperando resposta do cliente
- **TRANSFERIDO**: Passou para atendimento humano
- **AGUARDANDO_ATENDENTE**: Esperando ação do atendente humano
- **RESOLVIDO**: Atendimento finalizado com sucesso
- **CANCELADO**: Atendimento cancelado pelo cliente ou sistema
