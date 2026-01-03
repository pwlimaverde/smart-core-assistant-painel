Essa é uma arquitetura clássica de SaaS Multi-tenant com "Database per Tenant" (Banco de dados por cliente), mas com o desafio adicional de coordenação centralizada de eventos externos (Webhooks da Evolution API).

O maior desafio aqui não é receber os dados, mas sim rotear a conexão do banco de dados dinamicamente no momento da escrita, sem travar sua aplicação principal.

Aqui está minha sugestão de arquitetura e implementação usando Django + Celery + Redis:

1. Visão Geral da Arquitetura

Imagine sua aplicação como um Hub Central de Processamento.

Entrada: A Evolution API (instância do cliente) envia o Webhook para o seu SaaS.

Ingestão: O Django recebe, valida a origem e coloca a mensagem em uma fila (Redis).

Processamento (Worker): Um worker do Celery pega a mensagem.

Roteamento: O worker consulta no seu "Banco Mestre" qual é a string de conexão do banco de dados daquele cliente específico.

Persistência: O worker abre uma conexão temporária com o Postgres do cliente e salva os dados.

2. Estratégia de Identificação (O Endpoint do Webhook)

Não use um único endpoint genérico. Use a URL para identificar o cliente logo de cara. Configure a Evolution API para enviar os webhooks para uma URL que contenha o ID do cliente ou um token único.

URL Sugerida:
https://api.seusaas.com/webhooks/v1/{client_unique_id}/{instance_name}/

client_unique_id: Um UUID que identifica o cliente no seu Banco Mestre.

instance_name: Nome da instância na Evolution (para logs).

3. Implementação no Django (Passo a Passo)
A. O "Banco Mestre" (SaaS Database)

Você precisa de um banco de dados central (do seu SaaS) que guarda as credenciais dos bancos dos clientes.

code
Python
download
content_copy
expand_less
# core/models.py
from django.db import models

class Client(models.Model):
    name = models.CharField(max_length=100)
    api_token = models.CharField(max_length=64) # Para validar que o webhook é dele
    uuid = models.UUIDField(unique=True)
    
    # Credenciais do Banco do Cliente (criptografadas preferencialmente)
    db_name = models.CharField(max_length=100)
    db_user = models.CharField(max_length=100)
    db_password = models.CharField(max_length=100)
    db_host = models.CharField(max_length=200)
    db_port = models.IntegerField(default=5432)

    is_active = models.BooleanField(default=True)
B. A View de Ingestão (Leve e Rápida)

A view não deve processar nada nem conectar no banco do cliente. Ela só recebe e joga na fila.

code
Python
download
content_copy
expand_less
# webhooks/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .tasks import process_webhook_event

class EvolutionWebhookView(APIView):
    def post(self, request, client_uuid, instance_name):
        # 1. Validação básica (opcionalmente checar se o cliente existe no cache)
        payload = request.data
        
        # 2. Despachar para o Celery imediatamente
        # Passamos o UUID e o payload. Não passamos objetos do banco.
        process_webhook_event.delay(str(client_uuid), payload)
        
        return Response({"status": "received"}, status=200)
C. O Worker e o Roteamento de Banco (Onde a mágica acontece)

Aqui você precisa resolver o problema de conectar em bancos desconhecidos em tempo de execução. O Django settings.DATABASES é estático, então você precisará configurar conexões manualmente ou usar um gerenciador de contexto.

Sugestão: Use uma abordagem de conexão manual segura ou injete a configuração no runtime.

code
Python
download
content_copy
expand_less
# webhooks/tasks.py
from celery import shared_task
from django.db import connections
from core.models import Client
import psycopg2 # Ou use a ORM do Django de forma dinâmica

@shared_task
def process_webhook_event(client_uuid, payload):
    try:
        # 1. Buscar credenciais no Banco Mestre
        client = Client.objects.get(uuid=client_uuid, is_active=True)
        
        # 2. Processar os dados (Lógica de negócio do seu SaaS)
        processed_data = transform_evolution_data(payload)
        
        # 3. Conectar ao Banco do Cliente e Salvar
        # Opção A: Usando SQL Raw (Mais rápido e menos propenso a erros de estado do Django)
        save_to_client_db_raw(client, processed_data)
        
        # Opção B: Se você precisa usar o Django ORM nos modelos do cliente,
        # você precisará de uma configuração de roteamento de DB dinâmica, 
        # o que é complexo para hosts externos variados.
        
    except Client.DoesNotExist:
        print(f"Cliente {client_uuid} não encontrado.")
    except Exception as e:
        print(f"Erro ao processar: {e}")
        # Retry logic here

def transform_evolution_data(payload):
    # Sua lógica para extrair mensagem, telefone, etc.
    return {
        'phone': payload.get('data', {}).get('remoteJid'),
        'message': payload.get('data', {}).get('message', {}).get('conversation'),
        # ...
    }

def save_to_client_db_raw(client, data):
    """
    Conecta diretamente ao banco do cliente usando psycopg2
    """
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=client.db_name,
            user=client.db_user,
            password=client.db_password,
            host=client.db_host,
            port=client.db_port
        )
        cur = conn.cursor()
        
        # Exemplo de Insert
        sql = "INSERT INTO chats_message (phone, content, created_at) VALUES (%s, %s, NOW())"
        cur.execute(sql, (data['phone'], data['message']))
        
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Erro de conexão com DB do cliente: {e}")
        if conn: conn.rollback()
        raise e # Para o Celery tentar novamente
    finally:
        if conn: conn.close()
4. Pontos Críticos e Soluções
Segurança (Conexão com Banco Externo)

Como seus clientes "montam o servidor", o banco deles estará na internet.

Requisito: O cliente deve liberar o IP do seu SaaS no firewall (pg_hba.conf ou Security Group da AWS/DigitalOcean) para permitir a conexão na porta 5432.

SSL: Force o uso de SSL (sslmode='require') na conexão psycopg2 para garantir que os dados não trafeguem em texto plano.

Performance e Concorrência

Pool de Conexões: Abrir e fechar conexão (psycopg2.connect) a cada mensagem é lento. Se o volume for alto, considere usar PgBouncer no lado do cliente ou implementar um padrão de Singleton/Pool persistente nos seus Celery Workers (cuidado com vazamento de memória).

Filas Separadas: Se você tiver um cliente "gigante" e 50 pequenos, o gigante pode entupir a fila. Use filas do Celery separadas ou prioridades (ex: queue='high_priority' para clientes premium).

Idempotência

A Evolution API (e webhooks em geral) pode enviar o mesmo evento duas vezes (retry).

Antes de inserir no banco do cliente, verifique se o ID da mensagem (key.id da Evolution) já existe na tabela de mensagens do cliente. Se existir, ignore.

5. Alternativa Híbrida (Recomendada)

Se lidar com múltiplas conexões de saída for muito instável (firewalls de clientes bloqueando, latência de rede, bancos caindo), considere inverter a responsabilidade final:

Seu SaaS recebe o webhook e processa.

Seu SaaS salva o dado processado em uma API do Cliente (que o cliente deve hospedar junto com o banco dele).

Ou seja: Evolution -> Seu SaaS -> Request HTTP (POST) -> Servidor do Cliente (Django/FastAPI) -> Banco Local.

Isso substitui uma conexão de banco de dados (stateful/complexa) por uma chamada HTTP simples (stateless/padronizada). Se o servidor do cliente estiver fora, você recebe um erro 500 e o Celery tenta de novo depois.

Resumo da Sugestão

Para começar rápido e manter o controle:

Use Celery para garantir que o webhook nunca dê timeout.

Use uma tabela Master para guardar as connection strings.

Use SQL Puro (Psycopg2) ou SQLAlchemy Core dentro da task do Celery para escrever no banco do cliente. Evite tentar configurar o Django ORM para conectar dinamicamente em 50 bancos externos diferentes em tempo de execução, isso costuma ser uma dor de cabeça em arquiteturas distribuídas.