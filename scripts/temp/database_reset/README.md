# 🔄 Reset Completo do Banco de Dados

Este script permite resetar completamente o banco de dados do projeto, removendo todas as migrações e recriando a estrutura do zero.

## 📋 O que o script faz:

1. **🛑 Para containers Docker** - Para todos os serviços do projeto
2. **🗑️ Remove volumes** - Remove volumes do PostgreSQL e Redis
3. **🧹 Limpa migrações** - Remove arquivos de migração antigas
4. **🚀 Inicia containers** - Inicia os serviços do zero
5. **🏗️ Recria banco** - Aplica migrações desde o início
6. **👤 Cria superusuário** - Configura usuário admin

## 📁 Estrutura Preservada:

### App `clientes`
- ✅ `__init__.py`
- ✅ `0001_initial.py`
- ✅ `0002_enable_pgvector_extension.py` (*Importante: mantém pgvector*)

### App `notion_sync`
- ✅ `__init__.py`
- ✅ `0001_initial.py` (recriado automaticamente)

### Demais apps
- ✅ Apenas `__init__.py` (limpo para recriação do zero)

## 🚀 Como usar:

```bash
# Navegar para o diretório do projeto
cd C:\PROJETOS\PYTHON\APPS\smart-core-assistant-painel

# Executar o script de reset
python scripts\database_reset\reset_database.py
```

## ⚠️ Antes de executar:

1. **Docker deve estar rodando**
   ```bash
   docker --version
   ```

2. **Salvar dados importantes** (se necessário)
   - Configurações do Notion
   - Dados críticos

3. **Backup do banco** (se necessário)
   ```bash
   docker compose exec postgres pg_dump -U postgres smart_core_db > backup.sql
   ```

## 📊 Após a execução:

### ✅ Serviços disponíveis:
- **Admin Django**: http://localhost:8000/admin/
- **API REST**: http://localhost:8000/api/
- **Documentação**: http://localhost:8000/docs/

### 🔐 Credenciais iniciais:
- **Usuário**: `admin`
- **Senha**: (definir no admin após primeiro acesso)

### 🗄️ Estrutura recriada:
- Todas as tabelas do zero
- Índices criados automaticamente
- Extensão pgvector habilitada
- Migrações aplicadas sequencialmente

## 🛠️ Configurações após reset:

### 1. Senha do Superusuário:
```bash
# Acessar o admin e definir senha
# Usuário: admin
# Email: admin@example.com
```

### 2. Verificar pgvector:
```bash
# Conectar ao banco e verificar
docker compose exec postgres psql -U postgres -d smart_core_db -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### 3. Configurar Notion (se necessário):
```bash
# Executar script de configuração
uv run task setup_notion_databases
```

## 🔧 Customização:

### Modificar apps a limpar:
No script `reset_database.py`, edite a variável `apps_clean`:

```python
apps_clean = [
    ("caminho/do/app/migrations", ["arquivo1.py", "arquivo2.py"]),  # Preservar
    ("outro/app/migrations", ["__init__.py"]),  # Limpar completamente
]
```

### Modificar volumes a remover:
```python
volumes_to_remove = [
    "postgres_django_data",
    "redis_data",
    # Adicionar outros volumes se necessário
]
```

## 🚨 Importante:

- **Perda de dados**: Este script APAGARÁ todos os dados
- **Ambiente de desenvolvimento**: Apenas para desenvolvimento/testes
- **Backups recomendados**: Sempre faça backup antes
- **Docker necessário**: Docker Desktop/Docker Engine deve estar rodando

## 🔄 Fluxo completo:

```bash
# 1. Reset completo (automático)
python scripts\database_reset\reset_database.py

# 2. Verificar status dos serviços
docker compose ps

# 3. Acessar o admin
# http://localhost:8000/admin/

# 4. Configurar integrações (se necessário)
# - Notion
# - Firebase
# - Outros serviços
```

## 📝 Logs e Troubleshooting:

### Logs de execução:
O script exibe logs detalhados de cada etapa:
- 🔄 Executando comandos
- ✅ Sucesso nas operações
- ❌ Erros (se ocorrerem)

### Problemas comuns:

1. **Docker não responde**:
   ```bash
   docker info
   docker compose ps
   ```

2. **Migrações falham**:
   ```bash
   uv run task migrate --fake
   uv run task migrate
   ```

3. **Containers não iniciam**:
   ```bash
   docker compose logs postgres
   docker compose logs redis
   ```

## 📞 Suporte:

Caso encontre problemas:
1. Verifique os logs do script
2. Verifique os logs do Docker
3. Verifique as configurações no `.env`
4. Consulte a documentação do projeto

---

**⚠️ AVISO**: Use este script com cuidado. Ele remove todos os dados permanentemente.