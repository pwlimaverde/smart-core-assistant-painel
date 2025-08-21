# Smart Core Assistant Painel - Ambiente Docker

Este diretório contém os scripts para configurar e gerenciar o ambiente de desenvolvimento local usando Docker.

## Pré-requisitos

- Docker e Docker Compose instalados
- Git instalado
- Um arquivo `.env` na raiz do projeto (use `.env.example` como base)

## Setup Rápido

Execute o script apropriado para o seu sistema operacional **a partir da raiz do projeto**:

### Windows
```cmd
.\ambiente_docker\setup.bat
```

### Linux / macOS
```bash
chmod +x ./ambiente_docker/setup.sh
./ambiente_docker/setup.sh
```

## Configuração do Arquivo .env

Antes de executar o setup, configure as seguintes variáveis obrigatórias no arquivo `.env`:

```env
# Firebase (obrigatório)
GOOGLE_APPLICATION_CREDENTIALS=./src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json
FIREBASE_KEY_JSON_CONTENT={"type":"service_account","project_id":"seu-projeto",...}

# Evolution API (obrigatório)
EVOLUTION_API_BASE_URL=http://evolution-api:8080
EVOLUTION_API_GLOBAL_API_KEY=sua_chave_evolution_api

# Redis (adicionado automaticamente se não existir)
REDIS_HOST=redis
REDIS_PORT=6379

# Outras configurações necessárias...
```

**Importante**: O script verificará automaticamente se as variáveis `REDIS_HOST` e `REDIS_PORT` estão configuradas e as adicionará com valores padrão se necessário.

## O que o Script de Setup Faz

1. **Validação de Ambiente**:
   - Verifica se está sendo executado na raiz do projeto
   - Valida a existência do arquivo `.env`
   - Verifica credenciais do Firebase
   - Valida formato JSON do Firebase

2. **Preparação do Ambiente**:
   - Configura variáveis Redis automaticamente se não existirem
   - Cria o arquivo `firebase_key.json` a partir da variável `FIREBASE_KEY_JSON_CONTENT`
   - Limpa containers, volumes e redes de execuções anteriores
   - Remove migrações antigas do Django

3. **Construção e Inicialização**:
   - Constrói as imagens Docker com todas as dependências
   - Inicia todos os serviços definidos no `docker-compose.yml`
   - Aplica migrações no banco de dados
   - Cria superusuário (admin/123456)
   - Inicia o Django Q Cluster para processamento assíncrono

## Serviços Disponíveis

Após a execução bem-sucedida do script:

- **Aplicação Django**: http://localhost:8000
- **Painel Administrativo**: http://localhost:8000/admin/ (admin/123456)
- **Evolution API**: http://localhost:8080
- **Ollama (LLM)**: http://localhost:11434
- **PostgreSQL Django**: localhost:5432
- **PostgreSQL Evolution**: localhost:5433
- **Redis**: localhost:6379

## Validação do Setup

Para verificar se tudo está funcionando:

1. **Acesse a aplicação**: http://localhost:8000
2. **Verifique o admin**: http://localhost:8000/admin/ (admin/123456)
3. **Confira os logs dos containers**:
   ```bash
   docker logs smart-core-assistant-dev
   docker logs smart-core-qcluster-dev
   docker logs evolution-api-dev
   docker logs ollama-dev
   ```
4. **Teste o Ollama**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

## Problemas Comuns e Soluções

### 1. Erro de Conexão com Redis
**Problema**: Django Q Cluster não consegue conectar ao Redis
**Solução**: Verifique se as variáveis `REDIS_HOST=redis` e `REDIS_PORT=6379` estão no `.env`

### 2. Arquivo firebase_key.json não encontrado
**Problema**: Erro ao carregar credenciais do Firebase
**Solução**: 
- Verifique se `FIREBASE_KEY_JSON_CONTENT` está configurado no `.env`
- Certifique-se de que o JSON está válido (use um validador JSON)
- Confirme que `GOOGLE_APPLICATION_CREDENTIALS` aponta para o caminho correto

### 3. Containers não iniciam
**Problema**: Falha na inicialização dos containers
**Solução**: 
- Execute `docker system prune -a --volumes` para limpar o ambiente
- Verifique se o Docker tem espaço suficiente em disco
- Execute o setup novamente

### 4. Migrações falham
**Problema**: Erro durante aplicação das migrações
**Solução**: O script remove automaticamente migrações antigas e recria todas

### 5. Logs repetitivos de HEALTHCHECK
**Problema**: Requisições `GET /health/` a cada 30 segundos nos logs
**Solução**: O HEALTHCHECK foi desativado no Dockerfile para ambiente de desenvolvimento. Se precisar reativar:
```dockerfile
# Descomente no Dockerfile:
# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#   CMD curl -f http://localhost:8000/health/ || exit 1
```

### 6. Problemas com Ollama
**Problema**: Erro de conexão com o Ollama ou modelos não encontrados
**Solução**: 
- Verifique se o container Ollama está rodando: `docker logs ollama-dev`
- Teste a conectividade: `curl http://localhost:11434/api/tags`
- Para baixar novos modelos: `docker compose exec ollama ollama pull <nome-do-modelo>`
- Modelos padrão instalados: `llama3.2` e `mxbai-embed-large`

## Limpeza do Ambiente

Para remover completamente o ambiente Docker:

```bash
# Parar e remover containers, volumes e redes
docker compose down --volumes --remove-orphans

# Limpeza completa do sistema Docker (opcional)
docker system prune -a --volumes
```

## Estrutura de Arquivos

```
ambiente_docker/
├── setup.bat          # Script de setup para Windows
├── setup.sh           # Script de setup para Linux/macOS
├── validate_setup.bat # Script de validação para Windows
├── validate_setup.sh  # Script de validação para Linux/macOS
└── README.md          # Este arquivo
```

## Histórico de Correções

### Principais Problemas Resolvidos:

1. **Loop Infinito no Docker Entrypoint**: Desabilitado entrypoint problemático no Dockerfile
2. **Django Q Cluster**: Configuradas variáveis de ambiente Redis necessárias
3. **Firebase Key**: Criação automática do arquivo `firebase_key.json` a partir da variável de ambiente
4. **Migrações**: Limpeza automática de migrações antigas antes da recriação
5. **Dependências**: Instalação otimizada com `uv sync` e dependências específicas do PostgreSQL
6. **Healthcheck**: Desativado para evitar logs desnecessários e requisições repetitivas em desenvolvimento
7. **Estrutura de Diretórios**: Criação automática de diretórios necessários

### Melhorias Implementadas:

- Validação automática de configurações
- Criação automática de variáveis Redis se ausentes
- Logs mais informativos durante o setup
- Tratamento robusto de erros
- Documentação completa e clara

## Suporte

Se encontrar problemas durante o setup:

1. Verifique se todos os pré-requisitos estão instalados
2. Confirme que o arquivo `.env` está configurado corretamente
3. Execute o script de validação correspondente ao seu sistema
4. Consulte os logs dos containers para diagnóstico detalhado

O ambiente foi testado e validado em múltiplas execuções, garantindo reprodutibilidade e confiabilidade.