# Sistema de Chatbot para Atendimento ao Cliente

Este sistema fornece uma estrutura completa para gerenciar conversas de chatbot com IA para atendimento ao cliente, com foco em integração com WhatsApp.

## 🚀 Funcionalidades

### Modelos Principais

1. **Cliente** - Gerencia informações dos clientes
2. **Atendimento** - Controla o fluxo de atendimento
3. **Mensagem** - Armazena todas as mensagens da conversa
4. **FluxoConversa** - Define fluxos e estados da conversa

### Funcionalidades Principais

- ✅ Cadastro automático de clientes pelo número do WhatsApp
- ✅ Controle de estados de atendimento (aguardando, em andamento, resolvido, etc.)
- ✅ Histórico completo de mensagens
- ✅ Transferência para atendente humano
- ✅ Sistema de avaliação do atendimento
- ✅ Contexto de conversa persistente
- ✅ Suporte a diferentes tipos de mensagem (texto, imagem, áudio, etc.)
- ✅ Interface administrativa completa
- ✅ Comandos de gerenciamento via Django

## 📋 Instalação

### 1. Aplicar Migrações

```bash
# Gerar migrações para os novos modelos
python manage.py makemigrations oraculo

# Aplicar migrações
python manage.py migrate
```

### 2. Criar Superusuário (se necessário)

```bash
python manage.py createsuperuser
```

## 🛠️ Uso Básico

### Primeira Interação via WhatsApp

```python
from smart_core_assistant_painel.app.ui.oraculo.models import inicializar_atendimento_whatsapp

# Quando receber a primeira mensagem do WhatsApp
telefone = "+5511999999999"
primeira_mensagem = "Olá! Preciso de ajuda com meu pedido."

cliente, atendimento = inicializar_atendimento_whatsapp(
    numero_telefone=telefone,
    primeira_mensagem=primeira_mensagem,
    nome_cliente="João Silva"  # Opcional
)

print(f"Cliente: {cliente.telefone}")
print(f"Atendimento: {atendimento.id}")
print(f"Status: {atendimento.get_status_display()}")
```

### Processar Mensagens Subsequentes

```python
from smart_core_assistant_painel.app.ui.oraculo.models import processar_mensagem_whatsapp

# Para mensagens subsequentes
mensagem = processar_mensagem_whatsapp(
    numero_telefone="+5511999999999",
    conteudo="Meu pedido é o número 12345",
    tipo_mensagem=TipoMensagem.TEXTO
)

print(f"Mensagem processada: {mensagem.conteudo}")
```

### Buscar Atendimento Ativo

```python
from smart_core_assistant_painel.app.ui.oraculo.models import buscar_atendimento_ativo

atendimento = buscar_atendimento_ativo("+5511999999999")
if atendimento:
    print(f"Atendimento ativo: {atendimento.id}")
    print(f"Status: {atendimento.get_status_display()}")
```

## 🎯 Gerenciamento via Comandos Django

### Comando Principal

```bash
# Inicializar novo cliente
python manage.py chatbot --acao inicializar --telefone "+5511999999999" --nome "João Silva" --mensagem "Olá!"

# Processar mensagem
python manage.py chatbot --acao processar --telefone "+5511999999999" --mensagem "Preciso de ajuda"

# Ver estatísticas
python manage.py chatbot --acao estatisticas

# Executar demonstração
python manage.py chatbot --acao demo

# Limpar dados (cuidado!)
python manage.py chatbot --acao limpar
```

## 🔧 Integração com WhatsApp

### Exemplo de Integração

```python
# webhook_whatsapp.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from .models import (
    processar_mensagem_whatsapp, 
    buscar_atendimento_ativo,
    StatusAtendimento, 
    TipoMensagem
)

@csrf_exempt
@require_http_methods(["POST"])
def webhook_whatsapp(request):
    try:
        data = json.loads(request.body)
        
        # Extrair dados da mensagem do WhatsApp
        numero_telefone = data.get('from')
        conteudo = data.get('text', {}).get('body', '')
        message_id = data.get('id')
        
        # Processar mensagem
        mensagem = processar_mensagem_whatsapp(
            numero_telefone=numero_telefone,
            conteudo=conteudo,
            message_id=message_id
        )
        
        # Gerar resposta do bot (aqui você integraria com sua IA)
        resposta = gerar_resposta_ia(mensagem)
        
        # Salvar resposta do bot
        mensagem.marcar_como_respondida(resposta)
        
        return JsonResponse({
            'status': 'success',
            'response': resposta
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def gerar_resposta_ia(mensagem):
    """
    Aqui você integraria com sua IA para gerar respostas
    """
    # Exemplo simples
    if "pedido" in mensagem.conteudo.lower():
        return "Vou verificar seu pedido. Qual é o número?"
    elif "obrigado" in mensagem.conteudo.lower():
        # Finalizar atendimento
        mensagem.atendimento.finalizar_atendimento()
        return "De nada! Seu atendimento foi finalizado. Avalie nosso atendimento de 1 a 5."
    else:
        return "Como posso ajudá-lo hoje?"
```

## 📊 Interface Administrativa

Acesse `/admin/` para gerenciar:

- **Clientes**: Visualizar e editar informações dos clientes
- **Atendimentos**: Monitorar status e histórico dos atendimentos
- **Mensagens**: Ver todas as mensagens das conversas
- **Fluxos de Conversa**: Configurar fluxos automatizados

### Funcionalidades do Admin

1. **Dashboard**: Overview geral do sistema
2. **Filtros**: Filtrar por status, data, avaliação, etc.
3. **Busca**: Buscar por telefone, nome, conteúdo de mensagem
4. **Inlines**: Ver mensagens diretamente no atendimento
5. **Readonly**: Campos calculados e timestamps

## 🔄 Estados de Atendimento

- **AGUARDANDO_INICIAL**: Aguardando primeira interação
- **EM_ANDAMENTO**: Conversa ativa
- **AGUARDANDO_CLIENTE**: Aguardando resposta do cliente
- **AGUARDANDO_ATENDENTE**: Aguardando atendente humano
- **RESOLVIDO**: Atendimento concluído com sucesso
- **CANCELADO**: Atendimento cancelado
- **TRANSFERIDO**: Transferido para atendente humano

## 📱 Tipos de Mensagem Suportados

- **TEXTO**: Mensagens de texto
- **IMAGEM**: Fotos e imagens
- **AUDIO**: Mensagens de voz
- **VIDEO**: Vídeos
- **DOCUMENTO**: Arquivos e documentos
- **LOCALIZACAO**: Localização geográfica
- **CONTATO**: Informações de contato
- **SISTEMA**: Mensagens automáticas do sistema

## 🎨 Exemplos de Uso Avançado

### Contexto de Conversa

```python
# Armazenar informações no contexto
atendimento.atualizar_contexto('numero_pedido', '12345')
atendimento.atualizar_contexto('produto', 'Smartphone')
atendimento.atualizar_contexto('etapa', 'verificacao_pedido')

# Recuperar informações do contexto
numero_pedido = atendimento.get_contexto('numero_pedido')
etapa_atual = atendimento.get_contexto('etapa')
```

### Transferência para Humano

```python
# Transferir para atendente humano
atendimento.status = StatusAtendimento.TRANSFERIDO
atendimento.atendente_humano = "Maria Santos"
atendimento.adicionar_historico_status(
    StatusAtendimento.TRANSFERIDO,
    "Transferido por solicitação do cliente"
)
atendimento.save()
```

### Finalizar Atendimento

```python
# Finalizar com avaliação
atendimento.avaliacao = 5
atendimento.feedback = "Atendimento excelente!"
atendimento.finalizar_atendimento(StatusAtendimento.RESOLVIDO)
```

## 📈 Estatísticas e Relatórios

```python
# Estatísticas básicas
from django.db.models import Count, Avg

# Atendimentos por status
stats = Atendimento.objects.values('status').annotate(count=Count('id'))

# Avaliação média
avg_rating = Atendimento.objects.aggregate(Avg('avaliacao'))['avaliacao__avg']

# Clientes mais ativos
top_clients = Cliente.objects.annotate(
    total_atendimentos=Count('atendimentos')
).order_by('-total_atendimentos')[:10]
```

## 🚀 Próximos Passos

1. **Integrar com IA**: Conectar com OpenAI, Anthropic, ou outra IA
2. **Webhooks**: Configurar webhooks do WhatsApp Business API
3. **Análise de Sentimento**: Analisar satisfação do cliente
4. **Chatbot Flows**: Criar fluxos mais complexos
5. **Métricas**: Dashboard com métricas em tempo real
6. **Notificações**: Alertas para atendentes humanos

## 🔒 Segurança

- Validação de números de telefone
- Sanitização de entrada
- Logs de auditoria
- Controle de acesso via Django Admin

## 📝 Notas Importantes

- Sempre usar números de telefone no formato internacional (+55...)
- O sistema automaticamente normaliza números de telefone
- Contexto da conversa é armazenado em JSON para flexibilidade
- Histórico de status mantém rastreabilidade completa
- Suporte a múltiplos canais (preparado para expansão)

---

**Desenvolvido para Smart Core Assistant**
Sistema completo para automação de atendimento ao cliente com IA.
