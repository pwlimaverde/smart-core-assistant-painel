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
3.  **Limpa o Ambiente Docker**: Remove containers, volumes e redes de execuções anteriores para garantir um ambiente limpo.
4.  **Remove Migrações Antigas**: Apaga todos os arquivos de migração dos aplicativos Django.
5.  **Constrói e Inicia os Containers**: Constrói as imagens Docker e inicia os serviços definidos no `docker-compose.yml`.
6.  **Aplica Migrações**: Cria e aplica as novas migrações no banco de dados.
7.  **Cria Superusuário**: Cria um superusuário com as credenciais `admin` e senha `123456`.