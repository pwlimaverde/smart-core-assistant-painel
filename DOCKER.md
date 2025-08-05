# Docker Setup - Smart Core Assistant Painel

Este documento explica como usar o Docker para executar o Smart Core Assistant Painel com a sequência de inicialização correta.

## 🏗️ Arquitetura de Inicialização

O sistema foi configurado para garantir que o Django só inicie após a conclusão das seguintes etapas:

1. **`start_initial_loading`**: Inicializa o Firebase Remote Config
2. **`start_services`**: Carrega dados do Remote Config e configura variáveis de ambiente dinamicamente
3. **Django**: Inicia apenas após as etapas anteriores

## 📁 Arquivos Docker

### Desenvolvimento
- `Dockerfile.dev`: Imagem otimizada para desenvolvimento
- `docker-compose.dev.yml`: Orquestração para ambiente de desenvolvimento
- `scripts/docker-entrypoint.sh`: Script de inicialização para Django
- `scripts/docker-entrypoint-qcluster.sh`: Script de inicialização para QCluster

### Produção
- `Dockerfile`: Imagem otimizada para produção
- `docker-compose.yml`: Orquestração para ambiente de produção

### Scripts de Conveniência
- `scripts/start-docker-dev.ps1`: Inicia ambiente de desenvolvimento (Windows)
- `scripts/start-docker-dev.sh`: Inicia ambiente de desenvolvimento (Linux/Mac)
- `scripts/start-docker-prod.ps1`: Inicia ambiente de produção (Windows)

## 🚀 Como Usar

### Desenvolvimento

#### Windows (PowerShell)
```powershell
# Navegar para o diretório do projeto
cd c:\PROJETOS\PYTHON\APPS\smart-core-assistant-painel

# Executar script de inicialização
.\scripts\start-docker-dev.ps1
```

#### Linux/Mac (Bash)
```bash
# Navegar para o diretório do projeto
cd /path/to/smart-core-assistant-painel

# Tornar script executável e executar
chmod +x scripts/start-docker-dev.sh
./scripts/start-docker-dev.sh
```

#### Manual
```bash
# Construir e iniciar
docker-compose -f docker-compose.dev.yml up --build -d

# Ver logs
docker-compose -f docker-compose.dev.yml logs -f

# Parar
docker-compose -f docker-compose.dev.yml down
```

### Produção

#### Windows (PowerShell)
```powershell
# Navegar para o diretório do projeto
cd c:\PROJETOS\PYTHON\APPS\smart-core-assistant-painel

# Executar script de inicialização
.\scripts\start-docker-prod.ps1
```

#### Manual
```bash
# Construir e iniciar
docker-compose up --build -d

# Ver logs
docker-compose logs -f

# Parar
docker-compose down
```

## 🔧 Serviços

### Django App
- **Porta**: 8000
- **URL**: http://localhost:8000
- **Healthcheck**: http://localhost:8000/admin/

### Django QCluster
- **Função**: Processamento de tarefas assíncronas
- **Dependência**: Aguarda Django App inicializar

### Evolution API
- **Porta**: 8080
- **URL**: http://localhost:8080
- **Função**: API para WhatsApp

### PostgreSQL
- **Django DB**: `smart_core_db`
- **Evolution DB**: `evolution`
- **Volumes persistentes**: Dados mantidos entre reinicializações

## 🔐 Configuração de Variáveis

### Variáveis Estáticas (docker-compose)
- `DJANGO_SETTINGS_MODULE`
- `DJANGO_DEBUG`
- `POSTGRES_*` (configurações de banco)

### Variáveis Dinâmicas (Firebase Remote Config)
Estas variáveis são carregadas automaticamente pelo `start_services`:
- `SECRET_KEY_DJANGO`
- `OPENAI_API_KEY`
- `GROQ_API_KEY`
- `EVOLUTION_API_URL`
- E outras configurações específicas do projeto

## 📋 Comandos Úteis

### Desenvolvimento
```bash
# Ver logs em tempo real
docker-compose -f docker-compose.dev.yml logs -f django-app

# Acessar shell do Django
docker-compose -f docker-compose.dev.yml exec django-app bash

# Executar comandos Django
docker-compose -f docker-compose.dev.yml exec django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py shell

# Reiniciar apenas o Django
docker-compose -f docker-compose.dev.yml restart django-app

# Ver status dos containers
docker-compose -f docker-compose.dev.yml ps
```

### Produção
```bash
# Ver logs em tempo real
docker-compose logs -f django-app

# Acessar shell do Django
docker-compose exec django-app bash

# Reiniciar apenas o Django
docker-compose restart django-app

# Ver status dos containers
docker-compose ps
```

## 🔍 Troubleshooting

### Problema: Django não inicia
1. Verificar logs: `docker-compose logs django-app`
2. Verificar se Firebase está configurado
3. Verificar se `start_initial_loading` executou com sucesso
4. Verificar se `start_services` carregou as variáveis

### Problema: QCluster não inicia
1. Verificar se Django App está rodando
2. Verificar logs: `docker-compose logs django-qcluster`
3. QCluster aguarda Django App estar pronto

### Problema: Banco de dados não conecta
1. Verificar se PostgreSQL está rodando: `docker-compose ps`
2. Verificar logs do PostgreSQL: `docker-compose logs postgres-django`
3. Aguardar mais tempo para inicialização

### Problema: Firebase não inicializa
1. Verificar se `firebase_key.json` existe
2. Verificar permissões do arquivo
3. Verificar logs de inicialização

## 📦 Volumes

### Desenvolvimento
- `./src:/app/src`: Código fonte (hot reload)
- `./src/smart_core_assistant_painel/app/ui/db`: Banco SQLite (se usado)
- `./src/smart_core_assistant_painel/app/ui/media`: Arquivos de mídia

### Produção
- Apenas volumes de dados persistentes
- Código fonte é copiado para a imagem

## 🔒 Segurança

### Desenvolvimento
- Debug habilitado
- Código fonte montado como volume
- Senhas simples para facilitar desenvolvimento

### Produção
- Debug desabilitado
- Usuário não-root no container
- Código fonte copiado (não montado)
- Healthchecks configurados
- Apenas dependências de produção

## 📝 Logs

Todos os containers geram logs estruturados que podem ser visualizados com:

```bash
# Todos os serviços
docker-compose logs -f

# Serviço específico
docker-compose logs -f django-app

# Últimas N linhas
docker-compose logs --tail=50 django-app
```

## 🔄 Atualizações

Para atualizar o ambiente após mudanças no código:

```bash
# Desenvolvimento (hot reload automático)
# Apenas salvar os arquivos

# Produção (rebuild necessário)
docker-compose down
docker-compose up --build -d
```