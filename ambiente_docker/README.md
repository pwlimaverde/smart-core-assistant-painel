# Ambiente de Desenvolvimento Docker

Este diretório contém os scripts para configurar e gerenciar o ambiente de desenvolvimento local usando Docker.

## Pré-requisitos

- Docker e Docker Compose instalados.
- Um arquivo `.env` na raiz do projeto. Um exemplo (`.env.example`) é fornecido no projeto.

## Como usar

Execute o script apropriado para o seu sistema operacional a partir da raiz do projeto:

### Windows

```bash
.\ambiente_docker\setup.bat
```

### Linux / macOS

```bash
chmod +x ./ambiente_docker/setup.sh
./ambiente_docker/setup.sh
```

## O que o script faz

1.  **Verifica o `.env`**: Garante que o arquivo de configuração `.env` existe na raiz do projeto.
2.  **Cria `firebase_key.json`**: Se a variável `FIREBASE_KEY_JSON_CONTENT` estiver no `.env`, o script cria o arquivo de credenciais do Firebase.
3.  **Verifica Configurações do Redis**: Garante que as variáveis `REDIS_HOST` e `REDIS_PORT` estão configuradas no `.env` para o Django Q Cluster.
4.  **Limpa o Ambiente Docker**: Remove containers, volumes e redes de execuções anteriores para garantir um ambiente limpo.
5.  **Remove Migrações Antigas**: Apaga todos os arquivos de migração dos aplicativos Django.
6.  **Constrói e Inicia os Containers**: Constrói as imagens Docker e inicia os serviços definidos no `docker-compose.yml`.
7.  **Aplica Migrações**: Cria e aplica as novas migrações no banco de dados, incluindo as específicas do Django Q.
8.  **Cria Superusuário**: Cria um superusuário com as credenciais `admin` e senha `123456`.
9.  **Inicia o Django Q Cluster**: Inicia o serviço de processamento assíncrono após as migrações.

## Configurações Importantes

### Redis para Django Q Cluster

O projeto utiliza Redis para o Django Q Cluster (processamento assíncrono). As seguintes variáveis devem estar configuradas no `.env`:

```env
REDIS_HOST=redis
REDIS_PORT=6379
```

**Nota**: Se essas variáveis não estiverem presentes no `.env`, o script as adicionará automaticamente com os valores padrão.

### Firebase Configuration

O arquivo `firebase_key.json` é criado automaticamente a partir da variável `FIREBASE_KEY_JSON_CONTENT` no `.env`. Certifique-se de que:

1. A variável `GOOGLE_APPLICATION_CREDENTIALS` aponta para o caminho correto
2. A variável `FIREBASE_KEY_JSON_CONTENT` contém o JSON válido das credenciais do Firebase

### Serviços Disponíveis

Após a execução do script, os seguintes serviços estarão disponíveis:

- **Aplicação Django**: http://localhost:8000
- **Painel Administrativo**: http://localhost:8000/admin/ (admin/123456)
- **Evolution API**: http://localhost:8080
- **PostgreSQL Django**: localhost:5432
- **PostgreSQL Evolution**: localhost:5433
- **Redis**: localhost:6379

## Changelog - Correções Implementadas

### v1.1.0 - Melhorias no Ambiente Docker

#### Correções do Django Q Cluster
- **Problema**: O serviço `django-qcluster` estava falhando ao conectar com o Redis devido à ausência das variáveis de ambiente `REDIS_HOST` e `REDIS_PORT`
- **Solução**: Adicionadas as variáveis `REDIS_HOST=redis` e `REDIS_PORT=6379` no `docker-compose.yml` para o serviço `django-qcluster`
- **Resultado**: Django Q Cluster agora conecta corretamente ao Redis e processa tarefas assíncronas

#### Melhorias nos Scripts de Setup
- **Verificação Automática do Redis**: Os scripts `setup.bat` e `setup.sh` agora verificam automaticamente se as variáveis `REDIS_HOST` e `REDIS_PORT` estão configuradas no `.env` e as adicionam com valores padrão se necessário
- **Lógica Aprimorada do Firebase**: Melhorada a lógica de criação do `firebase_key.json` para ser mais robusta e informativa
- **Tratamento de Erros**: Adicionados avisos e validações mais claras para configurações ausentes

#### Atualizações na Documentação
- **Seção de Configurações Importantes**: Adicionada documentação detalhada sobre Redis, Firebase e serviços disponíveis
- **Instruções Claras**: Melhoradas as instruções de uso e configuração do ambiente
- **Lista de Serviços**: Documentados todos os serviços disponíveis após a execução do script

#### Melhorias no .env.example
- **Configurações do Redis**: Adicionadas as variáveis `REDIS_HOST` e `REDIS_PORT` com valores padrão
- **Organização**: Melhor organização das variáveis por categoria
- **Comentários**: Adicionados comentários explicativos sobre as correções implementadas