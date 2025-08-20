# ✅ Checklist de Setup - Smart Core Assistant Painel

## 🎯 Validação Rápida do Setup

Use este checklist para verificar se o setup foi executado corretamente.

## 📋 Pré-Setup

- [ ] **Docker Desktop** instalado e rodando
- [ ] **Git** disponível no sistema
- [ ] **Repositório clonado** localmente
- [ ] **Arquivo .env** criado a partir do .env.example
- [ ] **Credenciais Firebase** configuradas no .env

## 🚀 Execução do Setup

- [ ] **Script de setup executado** sem erros
  - Windows: `./ambiente_docker/setup.bat`
  - Linux/macOS: `./ambiente_docker/setup.sh`
- [ ] **Todos os containers iniciados** sem falhas
- [ ] **Migrações aplicadas** com sucesso
- [ ] **Superusuário criado** (admin/123456)

## ✅ Validação dos Serviços

### Containers Docker
- [ ] **django-app** - Status: Up
- [ ] **django-qcluster** - Status: Up
- [ ] **postgres** - Status: Up
- [ ] **redis** - Status: Up
- [ ] **evolution-api** - Status: Up

### Conectividade
- [ ] **Django App** - http://localhost:8000/ (responde)
- [ ] **Admin Panel** - http://localhost:8000/admin/ (login funciona)
- [ ] **Evolution API** - http://localhost:8080/ (responde)
- [ ] **PostgreSQL** - Conexão estabelecida
- [ ] **Redis** - Conexão estabelecida

### Funcionalidades
- [ ] **Django Q Cluster** - Processando tarefas
- [ ] **Firebase** - Arquivo firebase_key.json criado
- [ ] **Migrações** - Todas aplicadas
- [ ] **Logs** - Sem erros críticos

## 🔍 Comandos de Verificação

### Status dos Containers
```bash
docker compose ps
```
**Esperado:** Todos os serviços com status "Up"

### Teste de Conectividade
```bash
# Teste Django
curl http://localhost:8000/

# Teste Evolution API
curl http://localhost:8080/
```

### Verificação de Logs
```bash
# Logs gerais (últimas 50 linhas)
docker compose logs --tail=50

# Logs específicos
docker compose logs django-app
docker compose logs django-qcluster
```

### Validação Automática
```bash
# Windows
.\ambiente_docker\validate_setup.bat

# Linux/macOS
./ambiente_docker/validate_setup.sh
```

## 🚨 Indicadores de Problema

### ❌ Sinais de Falha
- [ ] Container com status "Exited" ou "Restarting"
- [ ] Erro 500 ao acessar http://localhost:8000/
- [ ] Logs com "CRITICAL" ou "ERROR"
- [ ] Impossibilidade de login no admin
- [ ] Django Q Cluster não processando

### 🔧 Ações Corretivas
1. **Verificar logs:** `docker compose logs -f`
2. **Reiniciar serviços:** `docker compose restart`
3. **Reset completo:** `docker compose down -v && ./setup.bat`
4. **Validar .env:** Verificar formato do Firebase JSON

## 📊 Script de Validação Automática

O script `validate_setup.bat/.sh` verifica automaticamente:

- ✅ Status de todos os containers
- ✅ Resposta HTTP do Django (porta 8000)
- ✅ Funcionamento do Django Q Cluster
- ✅ Conexão com PostgreSQL
- ✅ Conexão com Redis
- ✅ Existência do firebase_key.json
- ✅ Criação do superusuário admin
- ✅ Ausência de erros críticos nos logs

## 🎯 Critérios de Sucesso

### ✅ Setup Bem-Sucedido
- Todos os containers rodando
- Django acessível e responsivo
- Admin panel funcionando
- Django Q Cluster ativo
- Logs limpos (sem erros críticos)
- Validação automática 100% aprovada

### 📈 Métricas de Performance
- **Tempo de setup:** < 10 minutos
- **Tempo de inicialização:** < 2 minutos
- **Resposta Django:** < 1 segundo
- **Conexão DB:** < 500ms

## 🔄 Processo de Reset

Se algum item falhar:

1. **Reset suave:**
   ```bash
   docker compose restart
   ```

2. **Reset completo:**
   ```bash
   docker compose down -v
   ./ambiente_docker/setup.bat  # Windows
   ./ambiente_docker/setup.sh   # Linux/macOS
   ```

3. **Reset total (último recurso):**
   ```bash
   docker compose down -v --remove-orphans
   docker system prune -f
   ./ambiente_docker/setup.bat  # Windows
   ./ambiente_docker/setup.sh   # Linux/macOS
   ```

## 📝 Registro de Validação

**Data:** ___________  
**Responsável:** ___________  
**Versão:** ___________  

**Resultado:**
- [ ] ✅ Setup aprovado - Todos os itens validados
- [ ] ⚠️ Setup com ressalvas - Alguns itens falharam
- [ ] ❌ Setup reprovado - Falhas críticas encontradas

**Observações:**
_________________________________
_________________________________
_________________________________

---

**Versão do Checklist:** 1.0.0  
**Compatibilidade:** Windows, Linux, macOS  
**Última Atualização:** Janeiro 2025