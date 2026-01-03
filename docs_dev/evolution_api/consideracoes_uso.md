Para esse cenário específico (Evolution como "Gateway" de entrada de mensagens e saída de respostas de texto), a configuração de **desativar o armazenamento de dados** é, sem dúvida, a **melhor decisão**.

Você transformará a Evolution API em um serviço **quase stateless** (sem estado), o que a torna extremamente leve e rápida. O Postgres da Evolution servirá praticamente apenas para guardar a chave de sessão do WhatsApp (o login).

Aqui está a configuração exata e otimizada para o seu caso de uso:

### Configuração Otimizada (`docker-compose.yml`)

No serviço `evolution`, use estas variáveis. Isso garante que o banco da Evolution fique minúsculo e não consuma IOPS do disco.

```yaml
    environment:
      # ... (URL, KEY, etc) ...

      # --- CONFIGURAÇÃO DE BANCO DE DADOS ---
      DATABASE_ENABLED: true
      DATABASE_PROVIDER: postgresql
      DATABASE_CONNECTION_URI: ... # Sua string de conexão
      
      # [CRÍTICO] Mantém a sessão do WhatsApp salva. 
      # Se colocar false, ao reiniciar o container, o cliente perde o QR Code.
      DATABASE_SAVE_DATA_INSTANCE: true
      
      # [OTIMIZAÇÃO] Desativa todo o resto. 
      # O Evolution não salvará logs de conversas, contatos ou status.
      DATABASE_SAVE_DATA_NEW_MESSAGE: false
      DATABASE_SAVE_MESSAGE_UPDATE: false
      DATABASE_SAVE_DATA_CONTACTS: false
      DATABASE_SAVE_DATA_CHATS: false
      DATABASE_SAVE_DATA_LABELS: false
      DATABASE_SAVE_DATA_HISTORIC: false

      # --- CONFIGURAÇÃO DE WEBHOOK ---
      WEBHOOK_GLOBAL_URL: ${WEBHOOK_CORE_URL}
      WEBHOOK_GLOBAL_ENABLED: true
      
      # Importante: Define quais eventos o Webhook vai disparar.
      # Como você só quer mensagens chegando, filtramos aqui para economizar rede.
      WEBHOOK_EVENTS_APPLICATION_STARTUP: false
      WEBHOOK_EVENTS_QRCODE_UPDATED: true       # Útil para seu frontend mostrar o QR Code
      WEBHOOK_EVENTS_MESSAGES_SET: false        # Histórico antigo (não precisa)
      WEBHOOK_EVENTS_MESSAGES_UPSERT: true      # A MENSAGEM CHEGANDO (O principal)
      WEBHOOK_EVENTS_MESSAGES_UPDATE: false     # Status de entrega/leitura (Ack)
      WEBHOOK_EVENTS_MESSAGES_DELETE: false
      WEBHOOK_EVENTS_SEND_MESSAGE: false
      WEBHOOK_EVENTS_CONTACTS_SET: false
      WEBHOOK_EVENTS_CONTACTS_UPSERT: false
      WEBHOOK_EVENTS_CONTACTS_UPDATE: false
      WEBHOOK_EVENTS_PRESENCE_UPDATE: false
      WEBHOOK_EVENTS_CHATS_SET: false
      WEBHOOK_EVENTS_CHATS_UPSERT: false
      WEBHOOK_EVENTS_CHATS_UPDATE: false
      WEBHOOK_EVENTS_CHATS_DELETE: false
      WEBHOOK_EVENTS_GROUPS_UPSERT: false
      WEBHOOK_EVENTS_GROUPS_UPDATE: false
      WEBHOOK_EVENTS_GROUP_PARTICIPANTS_UPDATE: false
      WEBHOOK_EVENTS_CONNECTION_UPDATE: true    # Útil para saber se caiu ou conectou
```

### Por que isso é ideal para sua infraestrutura?

1.  **Redução Drástica de CPU e Disco:**
    Ao receber uma mensagem (`MESSAGES_UPSERT`), a Evolution normalmente faria: *Receber -> Descriptografar -> Escrever no Banco (Insert Message) -> Atualizar Chat -> Atualizar Contato -> Disparar Webhook*.
    Com essa config, ela faz apenas: *Receber -> Descriptografar -> Disparar Webhook*.
    Isso libera muito recurso para o seu **Django** e o **Postgres do Cliente** (onde o `pgvector` roda).

2.  **Backup e Migração Simplificados:**
    O banco da Evolution terá apenas alguns KBs (tabela `instance`). Se precisar mover o cliente de servidor, é instantâneo.

3.  **Foco no Webhook:**
    Como você não salva localmente, a confiabilidade do Webhook é crucial. Certifique-se de que seu Redis (do Evolution) está configurado, pois a Evolution usa o Redis para gerenciar a fila de envio dos Webhooks. Se o seu Django cair por 1 minuto, a Evolution segura os eventos no Redis e tenta enviar de novo.

### Um ponto de atenção (Dica de Ouro)

Você mencionou que processa apenas `MESSAGES_UPSERT`.

Se o seu chatbot enviar uma mensagem e ela falhar (ex: número não existe ou erro no WhatsApp), você **não saberá** se não ouvir o evento `MESSAGES_UPDATE` (ou configurar o webhook de envio).

*   **Cenário:** O Django envia "Olá". O Evolution retorna "200 OK" (significa que recebeu o comando).
*   **Realidade:** O WhatsApp tenta entregar e falha.
*   **Problema:** Seu sistema acha que enviou, mas o usuário não recebeu.

Se isso não for crítico para o MVP (Mínimo Produto Viável), mantenha desligado (`WEBHOOK_EVENTS_MESSAGES_UPDATE: false`). Mas se precisar de confirmação de leitura ("check azul") ou confirmação de entrega ("check duplo"), você precisará ativar esse evento no webhook (mas continue **não salvando no banco** `DATABASE_SAVE_MESSAGE_UPDATE: false`).