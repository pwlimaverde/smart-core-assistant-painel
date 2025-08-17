# Smart Core Assistant Painel

Um painel inteligente para assistente virtual com integração WhatsApp.

## Características

- Interface Django moderna
- Integração com Evolution API com tratamento UTF-8 robusto
- Suporte a PostgreSQL e Redis
- Processamento de linguagem natural
- Ambiente Docker completo
- Webhook WhatsApp com fallback de encoding automático
- QR Code Evolution API otimizado
- Serviço de envio de mensagens WhatsApp com arquitetura modular

## Instalação

### Usando Docker (Recomendado)

```bash
# Windows
powershell -ExecutionPolicy Bypass -File scripts/start-docker.ps1

# Linux/Mac
./scripts/setup-docker.sh
```

### Desenvolvimento Local (Ambiente Misto)

Para desenvolvimento local com bancos de dados no Docker e aplicação local:

1. Crie o arquivo `.env` na raiz do projeto (veja [ambiente_misto/README.md](ambiente_misto/README.md) para instruções detalhadas)
2. Execute o script de setup unificado:

```bash
# Windows
ambiente_misto\setup.bat

# Linux/Mac
chmod +x ambiente_misto/setup.sh
./ambiente_misto/setup.sh
```

3. Em um novo terminal, inicie a aplicação Django:

```bash
python src/smart_core_assistant_painel/app/ui/manage.py runserver 0.0.0.0:8000
```

Veja [ambiente_misto/README.md](ambiente_misto/README.md) para detalhes completos.

### Configuração do Ambiente de Desenvolvimento Misto

O ambiente de desenvolvimento misto permite executar os bancos de dados (PostgreSQL e Redis) em containers Docker enquanto a aplicação Django roda localmente na sua máquina. Isso facilita o desenvolvimento e a depuração.

#### Estrutura

- `ambiente_misto/setup.sh`/`ambiente_misto/setup.bat`: Scripts unificados para configurar e iniciar todo o ambiente.
- `ambiente_misto/README.md`: Documentação detalhada do ambiente de desenvolvimento misto.

#### Funcionalidades do Script de Setup

O script realiza todas as seguintes ações em sequência:

1.  **Verifica o Arquivo de Configuração**: Garante que `.env` existe.
2.  **Configura o Git**: Configura o Git para ignorar alterações locais em arquivos de configuração específicos do ambiente.
3.  **Ajusta o `settings.py`**: O arquivo de configuração do Django é modificado para apontar para o PostgreSQL rodando no Docker e usar cache em memória.
4.  **Ajusta o `docker-compose.yml`**: O arquivo do Docker Compose é reescrito para conter apenas os serviços de banco de dados, usando PostgreSQL versão 14.
5.  **Limpa o `Dockerfile`**: O Dockerfile principal é esvaziado.
6.  **Inicia os Containers**: Os containers do `postgres` e `redis` são iniciados em background.
7.  **Instala as dependências Python necessárias**.
8.  **Apaga as migrações do Django**.
9.  **Aplica as migrações do Django**.
10. **Cria um superusuário com nome `admin` e senha `123456`**.

#### Acesso ao Painel de Administração

Após executar o script de setup e iniciar a aplicação Django, você pode acessar o painel de administração em:

- **URL**: [http://localhost:8000/admin/](http://localhost:8000/admin/)
- **Usuário**: `admin`
- **Senha**: `123456`

#### Parando o Ambiente

Para parar os containers do PostgreSQL e Redis, utilize docker-compose a partir da **raiz do projeto**:

```bash
docker-compose down -v
```

Isso irá parar e remover os containers, além de apagar os volumes de dados. Para manter os dados, use:

```bash
docker-compose down
```

### Desenvolvimento Local (Tradicional)

```bash
# Instalar dependências
uv sync --dev

# Executar migrações
uv run migrate

# Iniciar servidor
uv run dev
```

## Configuração

1. Copie `.env.example` para `.env` (se existir)
2. Configure suas variáveis de ambiente
3. Execute as migrações do Django
4. Inicie os serviços

## Documentação

Veja [ambiente_docker/README.md](ambiente_docker/README.md) para instruções detalhadas do Docker.

### Correções Recentes

- ✅ **Webhook WhatsApp**: Implementado tratamento robusto de encoding UTF-8 com fallback automático
- ✅ **Evolution API**: Configuração otimizada para geração de QR Code
- ✅ **Validação JSON**: Prevenção de erros de atributo em objetos string
- ✅ **Logging**: Sistema de logs detalhado para debugging

Para detalhes completos das correções, consulte a seção correspondente em [ambiente_docker/README.md](ambiente_docker/README.md).

## Serviços

O projeto utiliza uma arquitetura modular baseada no padrão `py-return-success-or-error` para implementar funcionalidades. Recursos recentes incluem:

### Serviço de Envio de Mensagens WhatsApp

Implementamos um serviço modular para envio de mensagens via WhatsApp utilizando a Evolution API:

- **DataSource**: `WhatsAppAPIDataSource` - Responsável por interagir diretamente com a API
- **UseCase**: `WhatsAppSendMessageUseCase` - Implementa a lógica de negócio para envio de mensagens
- **Interface**: `WhatsAppServiceInterface` - Define o contrato para o serviço
- **Serviço de Alto Nível**: `send_whatsapp_message` - Função simplificada para envio de mensagens

Exemplo de uso:
```python
from smart_core_assistant_painel.modules.services.features.whatsapp_services.send_message_service import send_whatsapp_message

result = send_whatsapp_message(
    instance="5588921729550",
    api_key="sua_chave_api",
    message_data={
        "number": "5511999999999",
        "textMessage": {
            "text": "Olá! Esta é uma mensagem de teste."
        }
    }
)
```

## Licença

MIT License