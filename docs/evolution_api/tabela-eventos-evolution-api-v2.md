# Tabela de Eventos da Evolution API v2 - Ordem Crescente

Esta documentação lista todos os eventos disponíveis na Evolution API v2, organizados em ordem alfabética crescente para facilitar a consulta e configuração de webhooks.

## 📋 Visão Geral

Os webhooks permitem integração em tempo real entre a Evolution API e WhatsApp™, possibilitando sincronização automatizada de dados e criação de bots de autoatendimento e sistemas multi-serviços.

## 🎯 Eventos Por Categoria

### Eventos de Conexão
| Evento | Descrição | Webhook URL |
|--------|-----------|-------------|
| `APPLICATION_STARTUP` | Notifica quando a inicialização da aplicação ocorre | `/application-startup` |
| `CONNECTION_UPDATE` | Informa o status da conexão WhatsApp (conectando, reconectando, desconectando) | `/connection-update` |
| `LOGOUT_INSTANCE` | Acionado quando a instância faz logout | `/logout-instance` |
| `QRCODE_UPDATED` | Envia o código QR em formato base64 para escaneamento | `/qrcode-updated` |
| `REMOVE_INSTANCE` | Acionado quando uma instância é removida do sistema | `/remove-instance` |

### Eventos de Mensagens
| Evento | Descrição | Webhook URL |
|--------|-----------|-------------|
| `MESSAGES_DELETE` | Informa quando uma mensagem é deletada | `/messages-delete` |
| `MESSAGES_SET` | Envia uma lista de todas as mensagens carregadas no WhatsApp (ocorre apenas uma vez) | `/messages-set` |
| `MESSAGES_UPDATE` | Informa quando uma mensagem é atualizada | `/messages-update` |
| `MESSAGES_UPSERT` | Notifica quando uma mensagem é recebida | `/messages-upsert` |
| `SEND_MESSAGE` | Notifica quando uma mensagem é enviada | `/send-message` |

### Eventos de Contatos
| Evento | Descrição | Webhook URL |
|--------|-----------|-------------|
| `CONTACTS_SET` | Realiza o carregamento inicial de todos os contatos (ocorre apenas uma vez) | `/contacts-set` |
| `CONTACTS_UPDATE` | Informa quando um contato é atualizado | `/contacts-update` |
| `CONTACTS_UPSERT` | Recarrega todos os contatos com informações adicionais (ocorre apenas uma vez) | `/contacts-upsert` |

### Eventos de Chats
| Evento | Descrição | Webhook URL |
|--------|-----------|-------------|
| `CHATS_DELETE` | Notifica quando um chat é deletado | `/chats-delete` |
| `CHATS_SET` | Envia uma lista de todos os chats carregados | `/chats-set` |
| `CHATS_UPDATE` | Informa quando um chat é atualizado | `/chats-update` |
| `CHATS_UPSERT` | Envia qualquer informação de novo chat | `/chats-upsert` |

### Eventos de Grupos
| Evento | Descrição | Webhook URL |
|--------|-----------|-------------|
| `CALL` | Acionado para eventos relacionados a chamadas (recebendo, iniciando, terminando) | `/call` |
| `GROUP_PARTICIPANTS_UPDATE` | Notifica quando uma ação ocorre envolvendo um participante ('add', 'remove', 'promote', 'demote') | `/group-participants-update` |
| `GROUPS_UPDATE` | Notifica quando um grupo tem suas informações atualizadas | `/groups-update` |
| `GROUPS_UPSERT` | Notifica quando um grupo é criado | `/groups-upsert` |

### Eventos de Etiquetas
| Evento | Descrição | Webhook URL |
|--------|-----------|-------------|
| `LABELS_ASSOCIATION` | Acionado quando etiquetas são associadas ou removidas de itens | `/labels-association` |
| `LABELS_EDIT` | Acionado quando etiquetas são criadas, modificadas ou deletadas | `/labels-edit` |

### Eventos de Status
| Evento | Descrição | Webhook URL |
|--------|-----------|-------------|
| `PRESENCE_UPDATE` | Informa se o usuário está online, realizando uma ação como digitando ou gravando, e seu último status visto: 'unavailable', 'available', 'typing', 'recording', 'paused' | `/presence-update` |

### Eventos de Bot
| Evento | Descrição | Webhook URL |
|--------|-----------|-------------|
| `TYPEBOT_CHANGE_STATUS` | Acionado quando o status do Typebot muda | `/typebot-change-status` |
| `TYPEBOT_START` | Acionado quando uma sessão Typebot começa | `/typebot-start` |

### Eventos de Token
| Evento | Descrição | Webhook URL |
|--------|-----------|-------------|
| `NEW_JWT` | Notifica quando o token (jwt) é atualizado | `/new-jwt` |

## 🔧 Configuração dos Eventos

### Configuração Global
Adicione as seguintes variáveis ao arquivo `.env` para habilitar webhooks globais:

```bash
WEBHOOK_GLOBAL_URL='https://sua-url.com/webhook'
WEBHOOK_GLOBAL_ENABLED=true
WEBHOOK_GLOBAL_WEBHOOK_BY_EVENTS=false

# Ativar eventos específicos
WEBHOOK_EVENTS_APPLICATION_STARTUP=false
WEBHOOK_EVENTS_QRCODE_UPDATED=true
WEBHOOK_EVENTS_CONNECTION_UPDATE=true
WEBHOOK_EVENTS_MESSAGES_UPSERT=true
# ... adicionar outros eventos conforme necessário
```

### Configuração por Instância
Use o endpoint `/webhook/instance` para configurar webhooks por instância:

```json
{
  "url": "https://sua-url.com/webhook",
  "webhook_by_events": false,
  "webhook_base64": false,
  "events": [
    "QRCODE_UPDATED",
    "MESSAGES_UPSERT",
    "MESSAGES_UPDATE",
    "CONNECTION_UPDATE",
    "SEND_MESSAGE"
  ]
}
```

## 📊 Formato de URLs por Evento

Quando `WEBHOOK_BY_EVENTS` ou `webhook_by_events` está habilitado, as URLs específicas serão geradas automaticamente, respeitando o formato:

```
{URL_BASE}/{nome-do-evento-em-kebab-case}
```

**Exemplo:**
- URL Base: `https://api.exemplo.com/webhook/`
- Evento: `MESSAGES_UPSERT`
- URL Final: `https://api.exemplo.com/webhook/messages-upsert`

## 📝 Notas Importantes

1. **Eventos Únicos**: Eventos como `MESSAGES_SET`, `CONTACTS_SET`, `CHATS_SET` e `CONTACTS_UPSERT` ocorrem apenas uma vez durante a sincronização inicial.
2. **Base64**: Use `webhook_base64: true` para receber arquivos em formato base64.
3. **Filtros**: Sempre filtre os eventos relevantes para seu uso específico.
4. **Retentativa**: A API tentará enviar o webhook até 3 vezes com intervalos de 15 minutos em caso de falha.

## 🔍 Referências

- [Documentação Oficial Webhooks Evolution API](https://doc.evolution-api.com/v2/en/configuration/webhooks)
- [Configuração de Eventos Evolution API](https://docs.evoapicloud.com/instances/events/events-system)