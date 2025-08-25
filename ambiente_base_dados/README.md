# Ambiente Base de Dados - Smart Core Assistant

Este diretório contém a configuração completa do ambiente de base de dados para o projeto Smart Core Assistant.

## 🎯 Componentes

### Serviços Docker
- **PostgreSQL 16**: Banco de dados principal com extensões pgvector e outras
- **Redis 6.2**: Cache em memória para sessões e filas

### Extensões PostgreSQL Incluídas
- `vector`: Para busca semântica com embeddings
- `uuid-ossp`: Geração de UUIDs
- `pg_trgm`: Busca textual com trigramas
- `btree_gin`: Índices avançados

## 🚀 Instalação Rápida

### Automática (Recomendada)
```batch
# Execute o script de configuração automática
setup.bat
```

Este script irá:
1. ✅ Verificar se Docker está rodando
2. 🧹 Limpar ambiente anterior (containers e volumes)
3. 🏗️ Construir e iniciar containers
4. ⏳ Aguardar banco ficar pronto
5. 📦 Executar migrações Django
6. 👤 Criar superusuário (admin/123456)

### Manual
```batch
# 1. Construir e iniciar containers
docker-compose up --build -d

# 2. Verificar status
docker-compose ps

# 3. Aplicar migrações (do diretório raiz do projeto)
cd ..
python src/smart_core_assistant_painel/app/ui/manage.py migrate

# 4. Criar superusuário
python src/smart_core_assistant_painel/app/ui/manage.py createsuperuser
```

## 📊 Informações de Conexão

### PostgreSQL
- **Host**: localhost
- **Porta**: 5436
- **Banco**: smart_core_db
- **Usuário**: postgres
- **Senha**: postgres123

### Redis
- **Host**: localhost
- **Porta**: 6382

### Superusuário Django (após setup.bat)
- **Usuário**: admin
- **Senha**: 123456

## 🛠️ Comandos Úteis

```batch
# Ver logs em tempo real
docker-compose logs -f

# Parar serviços
docker-compose down

# Parar e remover volumes (CUIDADO: apaga dados)
docker-compose down -v

# Reconstruir apenas PostgreSQL
docker-compose up --build -d postgres-remote

# Acessar shell do PostgreSQL
docker-compose exec postgres-remote psql -U postgres -d smart_core_db

# Acessar shell do Redis
docker-compose exec redis-remote redis-cli
```

## 🗂️ Estrutura de Arquivos

```
ambiente_base_dados/
├── docker-compose.yml     # Configuração dos serviços
├── Dockerfile            # Imagem customizada do PostgreSQL
├── setup.bat             # Script de instalação automática
├── .dockerignore         # Arquivos ignorados no build
├── README.md             # Esta documentação
└── initdb/               # Scripts de inicialização do banco
    └── 00-extensions.sql # Instalação das extensões
```

## ⚠️ Observações Importantes

1. **Docker Desktop**: Deve estar rodando antes de executar os comandos
2. **Porta 5436**: PostgreSQL usa porta customizada para evitar conflitos
3. **Senha padrão**: Altere a senha em produção
4. **Volumes persistentes**: Os dados são mantidos entre reinicializações
5. **Limpeza completa**: Use `docker-compose down -v` apenas se quiser apagar todos os dados

## 🔧 Customização

### Variáveis de Ambiente
Crie um arquivo `.env` no diretório para personalizar:

```env
POSTGRES_DB=meu_banco
POSTGRES_USER=meu_usuario
POSTGRES_PASSWORD=minha_senha
POSTGRES_PORT=5432
REDIS_PORT=6379
```

### Adicionando Scripts SQL
Coloque arquivos `.sql` em `initdb/` para execução automática na criação do banco.

## 🆘 Solução de Problemas

### Erro: "Docker não está rodando"
- Inicie o Docker Desktop
- Aguarde ele ficar completamente ativo

### Erro: "Porto já em uso"
- Altere as portas no docker-compose.yml
- Ou pare outros serviços que usam as mesmas portas

### Erro: "Falha nas migrações"
- Verifique se o banco está realmente ativo
- Confira as credenciais no arquivo .env do projeto principal

### Banco não aceita conexões
```batch
# Verificar status dos containers
docker-compose ps

# Ver logs detalhados
docker-compose logs postgres-remote

# Testar conexão manual
docker-compose exec postgres-remote pg_isready -U postgres
```