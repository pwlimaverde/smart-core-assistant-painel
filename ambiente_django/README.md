# Ambiente Django (Smart Core Assistant Painel)

Este diretório contém o script de setup para levantar apenas o ambiente Django e seu cluster (Django Q), além de suas dependências (PostgreSQL e Redis). Os serviços de chat (Evolution API e Ollama) foram movidos para um ambiente separado (ambiente_chat) e são consumidos via URLs expostas pelo host.

## Requisitos

- Windows 10/11
- Docker Desktop instalado e em execução
- PowerShell (executar como usuário com permissão para Docker)

## Variáveis e Portas

- Django: http://localhost:8000
- PostgreSQL: localhost:5436 (exposto)
- Redis: localhost:6382 (exposto)
- Evolution API (ambiente_chat): http://localhost:8080
- Ollama (ambiente_chat): http://localhost:11434

Certifique-se de que no arquivo `.env` da raiz estejam configurados:

```
EVOLUTION_API_URL=http://localhost:8080
OLLAMA_BASE_URL=http://localhost:11434
POSTGRES_HOST=localhost
POSTGRES_PORT=5436
REDIS_HOST=localhost
REDIS_PORT=6382
```

Dentro dos containers, o acesso a Evolution API e Ollama é feito via `host.docker.internal` (já definido no docker-compose.yml).

## Como subir o ambiente

1. Abra um PowerShell na raiz do projeto: `c:\PROJETOS\PYTHON\APPS\smart-core-assistant-painel`
2. Execute o setup:
   
   - Build incremental:
     
     ```powershell
     .\ambiente_django\setup.ps1
     ```
   
   - Build limpo (reconstruir imagens do zero):
     
     ```powershell
     .\ambiente_django\setup.ps1 -CleanBuild
     ```

O script executa, em ordem:
- docker compose down -v
- docker compose build (com `uv sync` dentro do Dockerfile)
- docker compose up -d
- Aguarda o PostgreSQL ficar pronto
- Sincroniza dependências no container (`uv sync --frozen`)
- Aplica migrações (`manage.py migrate`)
- Cria/atualiza superusuário `admin` com senha `123456`

## Comandos úteis

- Logs gerais:
  ```powershell
  docker compose logs -f
  ```

- Logs da app Django:
  ```powershell
  docker compose logs -f django-app
  ```

- Acessar shell do Django:
  ```powershell
  docker compose exec django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py shell
  ```

- Fazer migrações:
  ```powershell
  docker compose exec django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py makemigrations
  docker compose exec django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate
  ```

- Criar superusuário manualmente (se necessário):
  ```powershell
  docker compose exec django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py createsuperuser
  ```

## Notas

- Não altere o ambiente `ambiente_chat`. Este ambiente Django está isolado e apenas consome Evolution API e Ollama via HTTP.
- As variáveis `EVOLUTION_API_URL` e `OLLAMA_BASE_URL` também são disponibilizadas no container (via `host.docker.internal`) para integração entre ambientes.