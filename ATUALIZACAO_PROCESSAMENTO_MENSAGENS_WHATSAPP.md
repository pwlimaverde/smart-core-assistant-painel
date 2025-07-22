# Atualização: Processamento de Mensagens WhatsApp com Nome do Perfil

As funções de processamento de mensagens do WhatsApp foram atualizadas para suportar o formato JSON correto do webhook e incluir o nome do perfil do usuário (`pushName`).

## Estrutura do JSON Webhook

O JSON recebido no webhook agora tem a seguinte estrutura:

```json
{
  "event": "messages.upsert",
  "instance": "suaInstancia",
  "data": {
    "key": {
      "remoteJid": "5516992805443@s.whatsapp.net",
      "fromMe": false,
      "id": "5F2AAA4BD98BB388BBCD6FCB9B4ED675"
    },
    "pushName": "Nome do Remetente",
    "message": {
      "extendedTextMessage": {
        "text": "Conteúdo da mensagem extendida"
      }
    },
    "messageType": "extendedTextMessage",
    "messageTimestamp": 1748739583
  },
  "owner": "nomeDaInstancia",
  "source": "android",
  "destination": "localhost",
  "date_time": "2025-07-22T13:30:00.000Z"
}
```

## Principais Mudanças

### 1. Função `nova_mensagem()` Atualizada

**Principais melhorias:**
- ✅ Extração correta do `pushName` do campo `data.pushName`
- ✅ Suporte ao campo `messageType` além da detecção automática
- ✅ Inclusão do `messageTimestamp` nos metadados
- ✅ Processamento de diferentes tipos de mensagem

**Exemplo de uso:**
```python
# JSON do webhook é processado automaticamente
webhook_data = {
    "event": "messages.upsert",
    "data": {
        "key": {
            "remoteJid": "5516992805443@s.whatsapp.net",
            "id": "MSG123"
        },
        "pushName": "João Silva",
        "message": {
            "extendedTextMessage": {
                "text": "Olá, preciso de ajuda!"
            }
        },
        "messageType": "extendedTextMessage",
        "messageTimestamp": 1748739583
    }
}

# Processa a mensagem
mensagem_id = nova_mensagem(webhook_data)
```

### 2. Função `processar_mensagem_whatsapp()` Aprimorada

**Nova assinatura:**
```python
def processar_mensagem_whatsapp(
    numero_telefone: str,
    conteudo: str,
    tipo_mensagem: TipoMensagem = TipoMensagem.TEXTO_FORMATADO,
    message_id: Optional[str] = None,
    metadados: Optional[dict[str, Any]] = None,
    nome_perfil_whatsapp: Optional[str] = None,  # NOVO PARÂMETRO
    remetente: Optional[TipoRemetente] = None
) -> int:
```

**O que mudou:**
- ✅ Novo parâmetro `nome_perfil_whatsapp` para o pushName
- ✅ Passa o nome do perfil para `inicializar_atendimento_whatsapp()`
- ✅ Melhor organização dos metadados

### 3. Função `inicializar_atendimento_whatsapp()` Expandida

**Nova assinatura:**
```python
def inicializar_atendimento_whatsapp(
    numero_telefone: str,
    primeira_mensagem: str = "",
    metadata_cliente: Optional[dict[str, Any]] = None,
    nome_cliente: Optional[str] = None,
    nome_perfil_whatsapp: Optional[str] = None  # NOVO PARÂMETRO
) -> tuple[Contato, Atendimento]:
```

**Comportamento atualizado:**
- ✅ Cria contato com `nome_perfil` preenchido
- ✅ Atualiza `nome_perfil` em contatos existentes quando necessário
- ✅ Evita salvamentos desnecessários com flag `atualizado`

### 4. Modelo `Contato` - Campo `nome_perfil`

O campo `nome_perfil` já existe no modelo e agora é utilizado para armazenar o `pushName` do WhatsApp:

```python
nome_perfil: models.CharField = models.CharField(
    max_length=100,
    blank=True,
    null=True,
    help_text="Nome do perfil cadastrado no WhatsApp do contato"
)
```

## Fluxo Completo de Processamento

### 1. Recebimento do Webhook
```python
# Webhook recebido do WhatsApp
webhook_json = {
    "event": "messages.upsert", 
    "data": {
        "key": {"remoteJid": "5516992805443@s.whatsapp.net", "id": "MSG123"},
        "pushName": "João Silva",
        "message": {"extendedTextMessage": {"text": "Olá!"}},
        "messageType": "extendedTextMessage"
    }
}
```

### 2. Processamento da Mensagem
```python
# nova_mensagem() extrai os dados
telefone = "5516992805443"  # de remoteJid
push_name = "João Silva"    # de pushName  
conteudo = "Olá!"          # de message.extendedTextMessage.text
message_id = "MSG123"      # de key.id
```

### 3. Inicialização do Contato
```python
# inicializar_atendimento_whatsapp() cria/atualiza contato
contato = Contato.objects.create(
    telefone="+5516992805443",
    nome_perfil="João Silva",  # pushName armazenado aqui
    # outros campos...
)
```

### 4. Resultado Final
- ✅ Contato criado/atualizado com nome do perfil WhatsApp
- ✅ Atendimento iniciado ou reutilizado
- ✅ Mensagem processada e armazenada

## Exemplo Completo de Uso

```python
def processar_webhook_whatsapp(request):
    """
    View para processar webhook do WhatsApp
    """
    try:
        # Recebe dados do webhook
        webhook_data = request.json
        
        # Processa mensagem automaticamente
        mensagem_id = nova_mensagem(webhook_data)
        
        # Log do resultado
        mensagem = Mensagem.objects.get(id=mensagem_id)
        contato = mensagem.atendimento.cliente
        
        logger.info(f"""
        Mensagem processada:
        - Telefone: {contato.telefone}
        - Nome perfil: {contato.nome_perfil}
        - Conteúdo: {mensagem.conteudo}
        - Tipo: {mensagem.tipo}
        """)
        
        return {"status": "success", "mensagem_id": mensagem_id}
        
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}")
        return {"status": "error", "message": str(e)}
```

## Benefícios das Melhorias

### 1. **Dados Mais Ricos**
- Nome do perfil WhatsApp armazenado automaticamente
- Timestamps preservados nos metadados
- Melhor rastreabilidade das mensagens

### 2. **Processamento Robusto** 
- Suporte nativo ao formato JSON do webhook
- Detecção automática do tipo de mensagem
- Tratamento de diferentes tipos de conteúdo

### 3. **Performance Otimizada**
- Evita atualizações desnecessárias no banco
- Detecção de mensagens duplicadas
- Reutilização de atendimentos ativos

### 4. **Manutenibilidade**
- Código mais organizado e documentado
- Validações robustas de entrada
- Logs informativos para debugging

## Compatibilidade

✅ **Totalmente compatível** com o código existente  
✅ **Parâmetros opcionais** - não quebra integrações existentes  
✅ **Migração automática** - sem necessidade de mudanças no banco  
✅ **Logs detalhados** para monitoramento  

## Próximos Passos

Para usar as melhorias:

1. **Deploy das alterações** - As funções já estão atualizadas
2. **Testar webhook** - Enviar mensagens de teste
3. **Verificar logs** - Confirmar processamento correto
4. **Monitorar dados** - Validar preenchimento do `nome_perfil`
