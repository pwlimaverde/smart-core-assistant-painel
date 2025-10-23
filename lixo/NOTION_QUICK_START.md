# 🚀 Quick Start - Configuração Notion (5 minutos)

Guia rápido para configurar a integração com Notion. Para detalhes completos, veja [NOTION_SETUP_GUIDE.md](NOTION_SETUP_GUIDE.md).

---

## ✅ Checklist de Setup

### 1️⃣ Criar Integração no Notion (2 min)

- [ ] Acesse: https://www.notion.so/my-integrations
- [ ] Clique em **"+ New integration"**
- [ ] Preencha:
  - Name: `Smart Core Assistant`
  - Type: `Internal integration`
- [ ] Marque as capabilities:
  - ✅ Read content
  - ✅ Update content
  - ✅ Insert content
- [ ] Copie o **Integration Token** (começa com `secret_`)

### 2️⃣ Criar Página no Notion (1 min)

- [ ] Crie uma nova página no Notion (ex: "CRM - Databases")
- [ ] Clique nos 3 pontinhos (...) → **"Add connections"**
- [ ] Selecione a integração criada no passo 1
- [ ] Copie o **Page ID** da URL:
  - URL: `https://notion.so/.../Nome-da-Pagina-ABC123DEF456?v=...`
  - Page ID: `ABC123DEF456` (parte após último `-` e antes do `?`)

### 3️⃣ Configurar Variáveis de Ambiente (1 min)

Adicione ao arquivo `.env` na raiz do projeto:

```env
# Integração Notion
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_PAGE_ID=ABC123DEF456
```

⚠️ **IMPORTANTE**: Substitua pelos valores reais copiados nos passos anteriores!

### 4️⃣ Aplicar Migrations do Django (30 seg)

```bash
uv run task migrate
```

### 5️⃣ Executar Setup Automático (1 min)

```bash
python setup_notion.py
```

**O que acontece:**
- ✅ Cria database "Contatos - CRM" no Notion (8 propriedades)
- ✅ Cria database "Clientes - CRM" no Notion (17 propriedades)
- ✅ Salva IDs no banco de dados Django (NotionDatabaseConfig)
- ✅ Salva IDs no .env como backup

### 6️⃣ Validar Configuração (30 seg)

```bash
python validate_notion_setup.py
```

**Resultado esperado:** Todas as verificações com ✓ verde

---

## 🎉 Pronto! Agora Teste

### Teste Manual no Django Admin

1. **Inicie o servidor:**
   ```bash
   uv run task dev
   ```

2. **Acesse o Django Admin:**
   ```
   http://localhost:8000/admin
   ```

3. **Crie um novo Contato:**
   - User Management → Contatos → Add Contato
   - Preencha: Nome, Telefone, Email
   - Clique em "Save"

4. **Verifique no Notion:**
   - Abra a página criada no passo 2
   - Deve aparecer o database "Contatos - CRM"
   - O contato deve estar lá! 🎊

### Teste via Django Shell

```bash
python manage.py shell
```

```python
# Criar contato de teste
from smart_core_assistant_painel.app.user_management.models import Contato

contato = Contato.objects.create(
    nome="João da Silva",
    telefone="11999999999",
    email="joao@example.com",
    ativo=True
)

# Verificar sincronização
from smart_core_assistant_painel.app.notion_sync.models import ContatoSync

sync = ContatoSync.objects.get(django_object=contato)
print(f"✓ Status: {sync.sync_status}")
print(f"✓ Notion ID: {sync.notion_id}")
print(f"✓ Última sync: {sync.last_sync}")
```

**Resultado esperado:**
```
✓ Status: synced
✓ Notion ID: 1a2b3c4d-5e6f-7890-abcd-ef1234567890
✓ Última sync: 2024-01-15 10:30:45
```

---

## 🔍 Verificar Status da Integração

### Ver Configurações Salvas

```bash
python manage.py shell
```

```python
from smart_core_assistant_painel.app.notion_sync.models import NotionDatabaseConfig

# Listar todas as configurações
for config in NotionDatabaseConfig.objects.all():
    print(f"{config.model_name}: {config.database_id}")
```

### Ver Logs de Sincronização

```python
from smart_core_assistant_painel.app.notion_sync.models import SyncLog

# Últimos 10 logs
logs = SyncLog.objects.all().order_by('-timestamp')[:10]
for log in logs:
    print(f"[{log.status}] {log.operation} - {log.model_name} #{log.django_id}")
```

---

## ❌ Problemas Comuns

### "NOTION_TOKEN não encontrado"

```bash
# Verifique se o .env está correto
cat .env | grep NOTION_TOKEN

# Deve mostrar:
# NOTION_TOKEN=secret_xxxxx...
```

### "Page ID incorreto ou sem permissão"

1. Abra a página no Notion
2. Clique em "..." → "Add connections"
3. Selecione sua integração
4. Execute novamente: `python setup_notion.py`

### "NotionDatabaseConfig não encontrado"

```bash
# Aplique as migrations
uv run task migrate

# Verifique se foi criado
python manage.py shell
>>> from smart_core_assistant_painel.app.notion_sync.models import NotionDatabaseConfig
>>> NotionDatabaseConfig.objects.count()
```

### "Propriedades não aparecem no Notion"

1. Aguarde 1-2 minutos (API pode ter delay)
2. Execute validação: `python validate_notion_setup.py`
3. Verifique manualmente no Notion
4. Se necessário, reexecute: `python setup_notion.py`

---

## 📋 Resumo dos Comandos

```bash
# 1. Aplicar migrations
uv run task migrate

# 2. Configurar Notion (cria databases)
python setup_notion.py

# 3. Validar configuração
python validate_notion_setup.py

# 4. Testar no shell
python manage.py shell

# 5. Iniciar servidor
uv run task dev
```

---

## 📚 Documentação Completa

- **Setup Detalhado**: [NOTION_SETUP_GUIDE.md](NOTION_SETUP_GUIDE.md)
- **API Notion**: https://developers.notion.com/reference/database
- **Código Fonte**: `src/smart_core_assistant_painel/app/notion_sync/`

---

## 🆘 Precisa de Ajuda?

1. **Execute o validador completo:**
   ```bash
   python validate_notion_setup.py
   ```

2. **Veja os logs detalhados:**
   ```bash
   tail -f logs/app.log  # Se tiver logging configurado
   ```

3. **Consulte a documentação completa:** [NOTION_SETUP_GUIDE.md](NOTION_SETUP_GUIDE.md)

---

## ✅ Checklist Final

Depois de tudo configurado:

- [ ] ✓ Variáveis de ambiente configuradas (`.env`)
- [ ] ✓ Migrations aplicadas
- [ ] ✓ Setup executado com sucesso (`setup_notion.py`)
- [ ] ✓ Validação passou (`validate_notion_setup.py`)
- [ ] ✓ Databases visíveis no Notion
- [ ] ✓ Teste manual funcionou (criar contato → aparece no Notion)
- [ ] ✓ NotionDatabaseConfig tem registros no banco
- [ ] ✓ Signals estão ativos (mudanças sincronizam automaticamente)

**Parabéns! 🎉 Sua integração Notion está PRONTA!**

---

**Tempo total**: ~5 minutos  
**Última atualização**: 2024