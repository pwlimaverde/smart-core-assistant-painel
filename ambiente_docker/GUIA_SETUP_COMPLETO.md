# Guia Completo de Setup - Smart Core Assistant Painel

## 🎯 Objetivo

Este guia garante que você possa configurar o ambiente de desenvolvimento **do zero** após clonar o repositório, seguindo um processo **100% automatizado** e **livre de erros**.

## 📋 Pré-requisitos

### Obrigatórios
- **Docker Desktop** instalado e funcionando
- **Git** para clonar o repositório
- **Credenciais do Firebase** (arquivo JSON)

### Verificação Rápida
```bash
# Verificar se o Docker está funcionando
docker --version
docker compose --version

# Verificar se o Docker está rodando
docker ps
```

## 🚀 Setup em 5 Passos

### Passo 1: Clonar o Repositório
```bash
git clone <URL_DO_REPOSITORIO>
cd smart-core-assistant-painel
```

### Passo 2: Configurar o Arquivo .env

1. **Copie o arquivo de exemplo:**
   ```bash
   cp .env.example .env
   ```

2. **Configure as variáveis obrigatórias no .env:**
   ```env
   # === CONFIGURAÇÕES OBRIGATÓRIAS ===
   
   # Django
   SECRET_KEY=sua_secret_key_aqui_muito_segura_e_longa
   DEBUG=True
   
   # PostgreSQL para Django
   POSTGRES_DB=smart_core_db
   POSTGRES_USER=smart_core_user
   POSTGRES_PASSWORD=sua_senha_postgres_segura
   
   # Firebase (CRÍTICO - deve ser JSON válido em uma linha)
   FIREBASE_KEY_JSON_CONTENT={"type":"service_account","project_id":"seu-projeto","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}
   
   # Evolution API
   EVOLUTION_API_BASE_URL=http://evolution-api:8080
   EVOLUTION_API_GLOBAL_API_KEY=sua_api_key_evolution
   
   # Ollama
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   
   # Webhook
   WEBHOOK_URL=http://localhost:8000/webhook/whatsapp/
   ```

### Passo 3: Preparar Credenciais do Firebase

**Opção A - Usando arquivo firebase_key.json (Recomendado):**
1. Coloque seu arquivo `firebase_key.json` na raiz do projeto
2. O script criará automaticamente a variável `FIREBASE_KEY_JSON_CONTENT`

**Opção B - Configuração manual:**
1. Abra seu arquivo `firebase_key.json`
2. Copie todo o conteúdo JSON
3. Remova quebras de linha e espaços extras
4. Cole na variável `FIREBASE_KEY_JSON_CONTENT` no .env

### Passo 4: Executar o Setup

**Windows:**
```cmd
.\ambiente_docker\setup.bat
```

**Linux/macOS:**
```bash
chmod +x ./ambiente_docker/setup.sh
./ambiente_docker/setup.sh
```

### Passo 5: Validar a Instalação

**Windows:**
```cmd
.\ambiente_docker\validate_setup.bat
```

**Linux/macOS:**
```bash
chmod +x ./ambiente_docker/validate_setup.sh
./ambiente_docker/validate_setup.sh
```

## ✅ Verificação de Sucesso

Após o setup, você deve ter:

- ✅ **Django App** rodando em http://localhost:8000/
- ✅ **Admin Panel** acessível em http://localhost:8000/admin/ (admin/123456)
- ✅ **Django Q Cluster** processando tarefas
- ✅ **PostgreSQL** conectado e com migrações aplicadas
- ✅ **Redis** funcionando para cache e filas
- ✅ **Evolution API** rodando em http://localhost:8080/
- ✅ **Firebase** configurado automaticamente

## 🔧 O Que o Setup Faz Automaticamente

### Validações Iniciais
- ✅ Verifica existência do arquivo .env
- ✅ Valida formato JSON do Firebase
- ✅ Cria variáveis ausentes automaticamente

### Limpeza do Ambiente
- ✅ Remove containers, volumes e redes antigas
- ✅ Apaga migrações antigas do Django
- ✅ Remove arquivos .pyc e cache Python

### Configuração do Ambiente
- ✅ Constrói imagens Docker otimizadas
- ✅ Cria arquivo firebase_key.json automaticamente
- ✅ Configura variáveis Redis para Django Q
- ✅ Aguarda banco de dados ficar disponível

### Inicialização do Django
- ✅ Aplica migrações do Django
- ✅ Aplica migrações específicas do Django Q
- ✅ Cria superusuário admin (senha: 123456)
- ✅ Inicia Django Q Cluster

## 🚨 Solução de Problemas

### Problema: "FIREBASE_KEY_JSON_CONTENT inválido"
**Solução:**
1. Verifique se o JSON está em uma única linha
2. Escape aspas duplas se necessário
3. Use um validador JSON online

### Problema: "Erro de conexão com PostgreSQL"
**Solução:**
1. Verifique se o Docker Desktop está rodando
2. Execute: `docker compose down -v`
3. Execute o setup novamente

### Problema: "Django Q Cluster não funciona"
**Solução:**
1. Verifique logs: `docker compose logs django-qcluster`
2. Verifique se Redis está rodando: `docker compose logs redis`
3. Execute o script de validação

### Problema: "Porta 8000 já está em uso"
**Solução:**
1. Pare outros serviços na porta 8000
2. Ou altere a porta no docker-compose.yml

## 📊 Comandos Úteis

### Monitoramento
```bash
# Ver logs de todos os serviços
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs -f django-app
docker compose logs -f django-qcluster

# Ver status dos containers
docker compose ps
```

### Manutenção
```bash
# Parar o ambiente
docker compose down

# Parar e remover volumes (CUIDADO: apaga dados)
docker compose down -v

# Reconstruir imagens
docker compose build --no-cache

# Reiniciar um serviço específico
docker compose restart django-app
```

### Acesso aos Containers
```bash
# Acessar shell do Django
docker compose exec django-app bash

# Executar comandos Django
docker compose exec django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py shell

# Ver migrações
docker compose exec django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py showmigrations
```

## 🔄 Processo de Reset Completo

Se precisar começar do zero:

```bash
# 1. Parar e remover tudo
docker compose down -v --remove-orphans

# 2. Remover imagens (opcional)
docker rmi $(docker images -q smart-core-assistant-painel*)

# 3. Limpar sistema Docker (opcional)
docker system prune -f

# 4. Executar setup novamente
./ambiente_docker/setup.bat  # Windows
./ambiente_docker/setup.sh   # Linux/macOS
```

## 📝 Checklist de Configuração

- [ ] Docker Desktop instalado e rodando
- [ ] Repositório clonado
- [ ] Arquivo .env criado e configurado
- [ ] Credenciais Firebase configuradas
- [ ] Script de setup executado sem erros
- [ ] Script de validação passou em todos os testes
- [ ] Django acessível em http://localhost:8000/
- [ ] Admin panel acessível com admin/123456
- [ ] Logs sem erros críticos

## 🎉 Pronto!

Seu ambiente de desenvolvimento está configurado e pronto para uso!

**Próximos passos:**
1. Acesse http://localhost:8000/ para ver a aplicação
2. Acesse http://localhost:8000/admin/ para o painel administrativo
3. Consulte a documentação do projeto para desenvolvimento

**Suporte:**
- Consulte os logs: `docker compose logs -f`
- Execute a validação: `./ambiente_docker/validate_setup.bat`
- Verifique a documentação técnica em `ANALISE_SETUP_PROBLEMAS_SOLUCOES.md`

---

**Versão do Guia:** 1.0.0  
**Última Atualização:** Janeiro 2025  
**Compatibilidade:** Windows, Linux, macOS