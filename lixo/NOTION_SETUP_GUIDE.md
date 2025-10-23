# Guia Completo de Configuração da Integração Notion

Este guia explica como configurar a integração completa entre o Django e o Notion para sincronização automática de Clientes e Contatos.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Configuração Inicial](#configuração-inicial)
4. [Executando o Setup](#executando-o-setup)
5. [Validação](#validação)
6. [Como Funciona](#como-funciona)
7. [Troubleshooting](#troubleshooting)
8. [Próximos Passos](#próximos-passos)

---

## 🎯 Visão Geral

A integração Notion permite sincronização automática e bidirecional entre:

- **Django** (models `Cliente` e `Contato`)
- **Notion** (databases `Clientes - CRM` e `Contatos - CRM`)

### Principais Funcionalidades

- ✅ **Criação automática de databases** no Notion com todas as propriedades
- ✅ **Persistência de IDs** no banco de dados Django (`NotionDatabaseConfig`)
- ✅ **Sincronização via signals** (mudanças no Django refletem no Notion)
- ✅ **Rastreamento de sincronização** (logs e status de cada operação)
- ✅ **Validação completa** de configurações e conectividade

---

## 🔧 Pré-requisitos

### 1. Integração Notion

Você precisa criar uma integração no Notion:

1. Acesse https://www.notion.so/my-integrations
2. Clique em **"+ New integration"**
3. Preencha:
   - **Name**: Smart Core Assistant (ou nome de sua preferência)
   - **Associated workspace**: Selecione seu workspace
   - **Type**: Internal integration
4. Configure as **Capabilities** (capacidades):
   - ✅ Read content
   - ✅ Update content
   - ✅ Insert content
5. Clique em **"Submit"** e copie o **Integration Token**

### 2. Página Notion

Crie uma página no Notion onde os databases serão criados:

1. Abra o Notion e crie uma nova página
2. Dê um nome (ex: "CRM - Databases")
3. Clique nos 3 pontinhos (...) → **"Add connections"**
4. Selecione a integração criada acima
5. Copie o **Page ID** da URL:
   - URL: `https://notion.so/workspace/Nome-da-Pagina-abc123def456?v=...`
   - Page ID: `abc123def456` (parte após o último `-` e antes do `?`)

### 3. Variáveis de Ambiente

Adicione ao arquivo `.env` na raiz do projeto:

```env
# Configuração do Notion
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_PAGE_ID=abc123def456
```

### 4. Banco de Dados Django

Certifique-se de que as migrations foram aplicadas:

```bash
uv run task migrate
```

---

## 🚀 Configuração Inicial

### Passo 1: Executar o Setup

Execute o script de setup para criar os databases no Notion:

```bash
python setup_notion.py
```

### O que o script faz:

1. **Valida configurações**
   - Verifica se `NOTION_TOKEN` está configurado
   - Verifica se `NOTION_PAGE_ID` está configurado
   - Testa conexão com a API do Notion

2. **Cria database de Contatos**
   - Cria database com título "Contatos - CRM"
   - Adiciona todas as propriedades:
     - Nome (title)
     - Telefone (rich_text)
     - Email (email)
     - WhatsApp (rich_text)
     - Ativo (checkbox)
     - Data Cadastro (date)
     - Última Interação (date)
     - Django ID (number)
   - Valida que propriedades foram criadas

3. **Cria database de Clientes**
   - Cria database com título "Clientes - CRM"
   - Adiciona todas as propriedades:
     - Nome Fantasia (title)
     - Razão Social (rich_text)
     - Tipo (select: Pessoa Física/Jurídica)
     - CNPJ (rich_text)
     - CPF (rich_text)
     - Telefone (phone_number)
     - Site (url)
     - Ramo de Atividade (rich_text)
     - Endereço (rich_text)
     - CEP (rich_text)
     - Cidade (rich_text)
     - UF (rich_text)
     - País (rich_text)
     - Ativo (checkbox)
     - Data Cadastro (date)
     - Última Atualização (date)
     - Django ID (number)
   - Valida que propriedades foram criadas

4. **Salva configurações no Django**
   - Cria/atualiza registros em `NotionDatabaseConfig`
   - Salva IDs dos databases
   - Salva nomes dos databases
   - Salva schemas completos das propriedades
   - Marca como ativo

5. **Backup no .env**
   - Adiciona/atualiza `NOTION_DATABASE_CONTATO_ID`
   - Adiciona/atualiza `NOTION_DATABASE_CLIENTE_ID`

### Saída Esperada

```
╭─────────────────────────────────────────────╮
│ Configuração de Databases no Notion         │
│ Criando estrutura COMPLETA de Contatos e    │
│ Clientes com persistência no Django         │
╰─────────────────────────────────────────────╯

1. Configurando conexão
  ✓ Cliente configurado
  ✓ Página pai: abc123def456

2. Criando Database de Contatos (com propriedades)
→ Criando database: Contatos - CRM
  • Criando estrutura base...
  ✓ Database criado: 1a2b3c4d-5e6f-7890-abcd-ef1234567890
  • Adicionando propriedades via UPDATE...
  ✓ UPDATE executado com sucesso
  • Aguardando API processar...
  ✓ SUCESSO! 8 propriedades criadas!
    - Ativo
    - Data Cadastro
    - Django ID
    - Email
    - Nome
    - Telefone
    - WhatsApp
    - Última Interação

3. Criando Database de Clientes (com propriedades)
→ Criando database: Clientes - CRM
  • Criando estrutura base...
  ✓ Database criado: 9f8e7d6c-5b4a-3210-fedc-ba9876543210
  • Adicionando propriedades via UPDATE...
  ✓ UPDATE executado com sucesso
  • Aguardando API processar...
  ✓ SUCESSO! 17 propriedades criadas!
    [lista de todas as propriedades...]

4. Salvando Configurações no Django
  • Salvando Contato no banco de dados...
  ✓ Configuração salva: Contato → Contatos - CRM (1a2b3c4d...)
  • Salvando Cliente no banco de dados...
  ✓ Configuração salva: Cliente → Clientes - CRM (9f8e7d6c...)

→ Salvando IDs no .env (backup)...
  ✓ IDs salvos em: C:\PROJETOS\...\smart-core-assistant-painel\.env

5. Resumo Final
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Database ┃ ID                                ┃ Propriedades ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ Contatos │ 1a2b3c4d-5e6f-7890-abcd-ef1234567 │ 8            │
│ Clientes │ 9f8e7d6c-5b4a-3210-fedc-ba9876543 │ 17           │
└──────────┴───────────────────────────────────┴──────────────┘

╭─────────────────────────────────────────────╮
│ ✓ SETUP COMPLETO COM SUCESSO!               │
│                                             │
│ Os databases foram criados com TODAS as     │
│ propriedades!                               │
│ IDs e schemas salvos no banco Django        │
│ (NotionDatabaseConfig)                      │
│                                             │
│ Próximos passos:                            │
│ 1. Verifique os databases no Notion         │
│ 2. Execute: python validate_notion_setup.py │
│ 3. Crie contatos/clientes no Django!        │
│                                             │
│ A sincronização está PRONTA e PERSISTIDA!  │
╰─────────────────────────────────────────────╯
```

---

## ✅ Validação

Após executar o setup, valide que tudo está configurado corretamente:

```bash
python validate_notion_setup.py
```

### O que o script de validação verifica:

1. **Variáveis de Ambiente**
   - ✓ NOTION_TOKEN configurado
   - ✓ NOTION_PAGE_ID configurado
   - ✓ NOTION_DATABASE_CONTATO_ID (backup)
   - ✓ NOTION_DATABASE_CLIENTE_ID (backup)

2. **Banco de Dados Django**
   - ✓ NotionDatabaseConfig para Contato existe
   - ✓ NotionDatabaseConfig para Cliente existe
   - ✓ Database IDs salvos
   - ✓ Schemas de propriedades salvos

3. **Conexão com Notion**
   - ✓ Token válido
   - ✓ Autenticação bem-sucedida
   - ✓ Bot ID retornado

4. **Databases no Notion**
   - ✓ Database de Contatos existe
   - ✓ Todas as propriedades presentes (8)
   - ✓ Database de Clientes existe
   - ✓ Todas as propriedades presentes (17)

5. **NotionSyncService**
   - ✓ Serviço inicializado
   - ✓ Database IDs carregados do NotionDatabaseConfig
   - ✓ Health check passou

### Saída de Sucesso

```
╭─────────────────────────────────────────────╮
│ ✓ TUDO CONFIGURADO CORRETAMENTE!            │
│                                             │
│ A integração com Notion está pronta!        │
│                                             │
│ Próximos passos:                            │
│ 1. Crie um Contato ou Cliente no Django     │
│ 2. Verifique se aparece no Notion           │
│ 3. Os signals estão ativos e devem          │
│    sincronizar automaticamente              │
│                                             │
│ Você está pronto para começar!              │
╰─────────────────────────────────────────────╯
```

---

## 🔄 Como Funciona

### Arquitetura de Persistência

```
┌─────────────────────────────────────────────────────────────────┐
│                          DJANGO                                 │
│                                                                 │
│  ┌───────────────────┐         ┌──────────────────────┐        │
│  │ Cliente/Contato   │         │ NotionDatabaseConfig │        │
│  │ (Model)           │────────▶│ (Persistência)       │        │
│  │                   │         │                      │        │
│  │ - id              │         │ - model_name         │        │
│  │ - nome            │         │ - database_id        │        │
│  │ - ...             │         │ - database_name      │        │
│  └───────────────────┘         │ - properties_schema  │        │
│          │                     └──────────────────────┘        │
│          │ Signal                        │                     │
│          │                               │ Busca ID            │
│          ▼                               ▼                     │
│  ┌───────────────────┐         ┌──────────────────────┐        │
│  │ ClienteSync/      │         │ NotionSyncService    │        │
│  │ ContatoSync       │◀────────│                      │        │
│  │ (Shadow Model)    │         │ - Lê NotionDB Config │        │
│  │                   │         │ - Cria páginas       │        │
│  │ - notion_id       │         │ - Atualiza páginas   │        │
│  │ - sync_status     │         └──────────────────────┘        │
│  │ - last_sync       │                   │                     │
│  └───────────────────┘                   │ API Call            │
└──────────────────────────────────────────┼─────────────────────┘
                                           │
                                           ▼
                              ┌────────────────────────┐
                              │        NOTION          │
                              │                        │
                              │  Database: Contatos    │
                              │  Database: Clientes    │
                              │                        │
                              │  (Páginas = Registros) │
                              └────────────────────────┘
```

### Fluxo de Sincronização

1. **Criação de Registro no Django**
   ```python
   # Usuário cria um contato no Django Admin
   contato = Contato.objects.create(
       nome="João Silva",
       telefone="11999999999",
       email="joao@example.com"
   )
   ```

2. **Signal Dispara**
   - Signal `post_save` detecta a criação
   - Cria registro em `ContatoSync` (shadow model)
   - Status inicial: `pending`

3. **NotionSyncService Busca ID**
   - Busca `database_id` em `NotionDatabaseConfig`
   - Se não encontrar, fallback para `.env`
   - Cache local para performance

4. **Sincronização com Notion**
   - Mapper converte dados Django → Notion
   - Cria página no database Notion
   - Salva `notion_id` no `ContatoSync`
   - Atualiza status para `synced`

5. **Log de Auditoria**
   - Cria registro em `SyncLog`
   - Registra operação, status, timestamp
   - Armazena request/response para debug

### Vantagens da Persistência no Django

✅ **Sem dependência do .env**: IDs não ficam apenas em arquivo texto  
✅ **Histórico**: Mantém schema e configurações antigas  
✅ **Múltiplos ambientes**: Dev/Staging/Prod têm seus próprios IDs  
✅ **Auditoria**: Sabe quando e como foi configurado  
✅ **Facilita deploy**: Migrations carregam configurações automaticamente  
✅ **Reconfigurável**: Pode alterar databases sem editar código  

---

## 🔧 Troubleshooting

### Problema: "NOTION_TOKEN não encontrado"

**Causa**: Variável não configurada no `.env`

**Solução**:
```bash
# Adicione ao .env
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Problema: "Page ID incorreto ou sem permissão"

**Causa**: Integração não tem acesso à página

**Solução**:
1. Abra a página no Notion
2. Clique em "..." → "Add connections"
3. Selecione sua integração
4. Execute o setup novamente

### Problema: "Propriedades não foram criadas"

**Causa**: API do Notion pode ter delay ou limitações

**Solução**:
1. Aguarde alguns minutos
2. Execute o script `validate_notion_setup.py`
3. Verifique manualmente no Notion
4. Se necessário, adicione propriedades manualmente

### Problema: "NotionDatabaseConfig não encontrado"

**Causa**: Migrations não aplicadas ou banco não configurado

**Solução**:
```bash
# Aplique migrations
uv run task migrate

# Verifique se a tabela existe
python manage.py dbshell
.tables  # SQLite
\dt      # PostgreSQL
```

### Problema: "Sincronização não está funcionando"

**Causa**: Signals podem não estar registrados

**Solução**:
```python
# Verifique se o app está em INSTALLED_APPS
# settings.py
INSTALLED_APPS = [
    ...
    'smart_core_assistant_painel.app.notion_sync',
    ...
]

# Reinicie o servidor Django
uv run task dev
```

### Logs e Debug

Para ver logs detalhados:

```python
# No Django shell
from smart_core_assistant_painel.app.notion_sync.models import SyncLog

# Últimos logs
logs = SyncLog.objects.all().order_by('-timestamp')[:10]
for log in logs:
    print(f"{log.timestamp} - {log.operation} - {log.status}")
    print(f"  {log.error_message if log.error_message else 'OK'}")
```

---

## 🚀 Próximos Passos

### 1. Testar Sincronização Básica

```bash
# Django Shell
python manage.py shell

# Criar um contato de teste
from smart_core_assistant_painel.app.user_management.models import Contato
contato = Contato.objects.create(
    nome="Teste Notion",
    telefone="11999999999",
    email="teste@notion.com"
)

# Verificar sincronização
from smart_core_assistant_painel.app.notion_sync.models import ContatoSync
sync = ContatoSync.objects.get(django_object=contato)
print(f"Status: {sync.sync_status}")
print(f"Notion ID: {sync.notion_id}")
```

### 2. Implementar Sincronização Assíncrona (Opcional)

Para melhor performance, considere usar Celery:

```python
# tasks.py
from celery import shared_task

@shared_task
def sync_to_notion_async(model_name, django_id):
    # Lógica de sincronização
    pass
```

### 3. Configurar Webhooks do Notion (Bidirecional)

Para sincronização Notion → Django:

1. Configure webhook URL no Notion
2. Implemente endpoint no Django
3. Processe mudanças vindas do Notion

### 4. Monitoramento e Alertas

Configure alertas para falhas de sincronização:

```python
# Criar comando Django para verificar falhas
python manage.py check_sync_failures

# Enviar alertas via email/Slack
```

---

## 📚 Referências

- [Documentação da API Notion](https://developers.notion.com/reference/database)
- [Notion Python SDK](https://github.com/ramnes/notion-sdk-py)
- [Django Signals](https://docs.djangoproject.com/en/stable/topics/signals/)

---

## 📝 Notas Finais

- **Ambientes**: Cada ambiente (dev/staging/prod) deve ter seu próprio `NOTION_PAGE_ID` e databases
- **Performance**: Para volumes altos, considere processamento assíncrono (Celery)
- **Rate Limits**: A API do Notion tem limites de requisições (respeite os delays)
- **Dados Sensíveis**: Nunca exponha tokens em logs ou repositório

---

**Dúvidas?** Consulte o código em:
- `src/smart_core_assistant_painel/app/notion_sync/`
- Ou entre em contato com a equipe de desenvolvimento

**Última atualização**: 2024