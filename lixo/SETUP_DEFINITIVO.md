# 🎯 SETUP DEFINITIVO - Integração Django com Notion

**Status:** Guia Completo e Testado  
**Última Atualização:** 23 de Outubro de 2025  
**Tempo Estimado:** 20 minutos

---

## ⚠️ IMPORTANTE: Como a API do Notion Funciona

A API do Notion tem uma **limitação conhecida**:
- Quando você cria um database via API, ele é criado **VAZIO** (sem colunas/propriedades)
- As colunas SÓ aparecem quando você as adiciona manualmente no Notion

**Por isso, este setup tem 2 etapas:**
1. **Automática**: Script cria os databases vazios e salva os IDs
2. **Manual** (5 minutos): Você adiciona as colunas no Notion
3. **Automática**: Sistema sincroniza automaticamente

---

## 📋 Pré-requisitos

- ✅ Python 3.13+
- ✅ Django instalado e rodando
- ✅ Conta no Notion
- ✅ Token de integração do Notion configurado em `.env`

---

## 🚀 ETAPA 1: Criar Databases Vazios (Automático)

### 1.1. Verificar Configurações

Certifique-se que seu `.env` tem:

```bash
NOTION_TOKEN=secret_seu_token_aqui
NOTION_PAGE_ID=id_da_pagina_pai
```

### 1.2. Executar Script de Setup

```bash
python setup_notion.py
```

**O que o script faz:**
- ✅ Cria database "Contatos - CRM" no Notion
- ✅ Cria database "Clientes - CRM" no Notion
- ✅ Salva os IDs no `.env`
- ✅ Salva no banco Django (model `NotionDatabaseConfig`)

**Resultado esperado:**
```
SUCESSO TOTAL!
Databases criados:
- Contatos: a9454f14-f271-4869-a331-4500e48e3f46
- Clientes: 24c326d1-b789-4e26-95cd-2b1dd352e0e6
```

---

## 🔧 ETAPA 2: Adicionar Colunas no Notion (Manual - 5 minutos)

### 2.1. Abrir Database de Contatos

1. Abra o Notion
2. Navegue até a página "Gestão de Atendimentos"
3. Clique no database **"Contatos - CRM"**

### 2.2. Adicionar Colunas no Database de Contatos

Clique no **"+"** ao lado de "Name" e adicione EXATAMENTE estas colunas:

| Nome da Coluna | Tipo | Como Adicionar |
|---|---|---|
| `Nome` | Title | Renomeie "Name" para "Nome" |
| `Telefone` | Text | + → Text → Digite "Telefone" |
| `Email` | Email | + → Email → Digite "Email" |
| `WhatsApp` | Text | + → Text → Digite "WhatsApp" |
| `Ativo` | Checkbox | + → Checkbox → Digite "Ativo" |
| `Data Cadastro` | Date | + → Date → Digite "Data Cadastro" |
| `Última Interação` | Date | + → Date → Digite "Última Interação" |
| `Django ID` | Number | + → Number → Digite "Django ID" |

**Configurar Django ID:**
- Clique no nome da coluna "Django ID"
- Em "Number format" escolha: **Number** (sem formatação)

### 2.3. Abrir Database de Clientes

1. Volte para "Gestão de Atendimentos"
2. Clique no database **"Clientes - CRM"**

### 2.4. Adicionar Colunas no Database de Clientes

Adicione EXATAMENTE estas colunas:

| Nome da Coluna | Tipo | Observações |
|---|---|---|
| `Nome Fantasia` | Title | Renomeie "Name" |
| `Razão Social` | Text | |
| `Tipo` | Select | Adicione opções: "Pessoa Física", "Pessoa Jurídica" |
| `CNPJ` | Text | |
| `CPF` | Text | |
| `Telefone` | Phone | Tipo específico "Phone" |
| `Site` | URL | Tipo específico "URL" |
| `Ramo de Atividade` | Text | |
| `Endereço` | Text | |
| `CEP` | Text | |
| `Cidade` | Text | |
| `UF` | Text | |
| `País` | Text | |
| `Ativo` | Checkbox | |
| `Data Cadastro` | Date | |
| `Última Atualização` | Date | |
| `Django ID` | Number | **IMPORTANTE** |

**Configurar campo Tipo (Select):**
1. Clique no nome da coluna "Tipo"
2. Adicione as opções:
   - `Pessoa Física` (cor azul)
   - `Pessoa Jurídica` (cor verde)

**Configurar Django ID:**
- Mesmo processo do database de Contatos

---

## ✅ ETAPA 3: Validar Setup (Automático)

### 3.1. Executar Teste de Integração

```bash
python test_notion_integration.py
```

**Resultado esperado:**
```
✅ TODOS OS TESTES PASSARAM!

A integração com o Notion está funcionando perfeitamente.
Verifique os dados no Notion!
```

### 3.2. Verificar no Notion

1. Abra os databases no Notion
2. Você deverá ver:
   - **Contatos**: Uma página de teste criada e depois removida
   - **Clientes**: Uma página de teste criada e depois removida
3. As colunas devem estar preenchidas com dados de teste

---

## 🎉 ETAPA 4: Usar o Sistema

### 4.1. Criar um Contato Real

1. Acesse: http://localhost:8000/admin/
2. Vá em **Clientes** → **Contatos**
3. Clique em **"Adicionar Contato"**
4. Preencha:
   - **Telefone**: `5511988887777`
   - **Nome**: `João da Silva`
   - **Email**: `joao@example.com`
5. Clique em **"Salvar"**

**Verifique no Notion:**
- Abra "Contatos - CRM"
- Você verá "João da Silva" com todos os dados!

### 4.2. Criar um Cliente Real

1. No Django Admin, vá em **Clientes** → **Clientes**
2. Clique em **"Adicionar Cliente"**
3. Preencha:
   - **Nome Fantasia**: `Empresa XYZ Ltda`
   - **Tipo**: `Pessoa Jurídica`
   - **Cidade**: `São Paulo`
   - **UF**: `SP`
4. Clique em **"Salvar"**

**Verifique no Notion:**
- Abra "Clientes - CRM"
- Você verá "Empresa XYZ Ltda" com todos os dados!

---

## 📊 Monitoramento

### Ver Logs de Sincronização

http://localhost:8000/admin/notion_sync/synclog/

Aqui você vê:
- ✅ Operações bem-sucedidas (verde)
- ❌ Operações com erro (vermelho)
- ⏳ Operações pendentes (amarelo)

### Ver Status de Sincronização

**Contatos:**
http://localhost:8000/admin/notion_sync/contatosync/

**Clientes:**
http://localhost:8000/admin/notion_sync/clientesync/

### Ver Configurações de Databases

http://localhost:8000/admin/notion_sync/notiondatabaseconfig/

Aqui você vê os IDs dos databases salvos no sistema.

---

## 🔍 Troubleshooting

### Erro: "property that exists"

**Causa:** Colunas não foram adicionadas no Notion ou nomes estão errados

**Solução:**
1. Verifique que as colunas estão **EXATAMENTE** com os nomes listados
2. Verifique acentos (Última, não Ultima)
3. Verifique espaços (Data Cadastro, não DataCadastro)

### Dados não aparecem no Notion

**Checklist:**
- [ ] Token está correto no .env?
- [ ] Database IDs foram salvos corretamente?
- [ ] Integração está conectada aos databases no Notion?
- [ ] Colunas foram adicionadas manualmente?
- [ ] Nomes das colunas estão EXATOS?
- [ ] Coluna "Django ID" é tipo Number?

### Ver IDs dos Databases

Execute:
```bash
python inspect_database.py
```

Isso mostrará:
- IDs dos databases
- Propriedades criadas
- Status da conexão

---

## 🎓 Como Funciona Internamente

### 1. Signal é Disparado

Quando você salva um Contato/Cliente no Django:
```python
# signals.py
@receiver(post_save, sender=Contato)
def on_contato_saved(...)
    # Cria tracking
    # Chama NotionSyncService
```

### 2. Service Sincroniza com Notion

```python
# notion_service.py
class NotionSyncService:
    def create_record(...):
        # Obtém database ID do NotionDatabaseConfig
        # Mapeia dados Django → Notion
        # Cria página no Notion
        # Salva external_id no tracking
```

### 3. Tracking é Atualizado

```python
# models.py
class ContatoSync:
    external_id: str  # ID da página no Notion
    is_synced: bool   # Status de sincronização
```

### 4. Futuras Atualizações

Quando você atualiza o Contato:
1. Signal detecta a mudança
2. Service usa `external_id` para atualizar a página no Notion
3. Tracking é atualizado

---

## 🔄 Fluxo Completo

```
┌─────────────────────────────────────┐
│ 1. Usuário salva Contato no Django │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│ 2. Signal captura e cria tracking  │
│    ContatoSync (com Django ID)     │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│ 3. NotionSyncService é chamado     │
│    - Busca database_id do Config   │
│    - Mapeia dados com Mapper       │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│ 4. Cria página no Notion via API   │
│    POST /v1/pages                  │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│ 5. Notion retorna page_id          │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│ 6. Salva page_id no tracking       │
│    ContatoSync.external_id         │
│    ContatoSync.is_synced = True    │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│ 7. Log de sucesso é registrado     │
│    SyncLog (status=success)        │
└─────────────────────────────────────┘
```

---

## 🆘 Suporte

### Se ainda não funcionar:

1. **Execute diagnóstico:**
   ```bash
   python inspect_database.py
   ```

2. **Limpe e recrie:**
   ```bash
   python cleanup_test_data_auto.py
   python setup_notion.py
   # Adicione colunas manualmente
   python test_notion_integration.py
   ```

3. **Verifique logs no Django:**
   - Terminal onde o Django está rodando
   - Logs do Loguru mostram cada etapa

4. **Verifique no Django Admin:**
   - Notion Sync → Logs de Sincronização
   - Veja qual erro específico está ocorrendo

---

## ✅ Checklist Final

Antes de considerar o setup completo, verifique:

- [ ] Script `setup_notion.py` executou sem erros
- [ ] Databases "Contatos - CRM" e "Clientes - CRM" existem no Notion
- [ ] TODAS as colunas foram adicionadas manualmente
- [ ] Nomes das colunas estão EXATOS (com acentos)
- [ ] Coluna "Django ID" é tipo Number em AMBOS os databases
- [ ] Teste `test_notion_integration.py` passou 100%
- [ ] Contato de teste apareceu no Notion
- [ ] Cliente de teste apareceu no Notion
- [ ] Logs no Admin mostram status "success"

Se TODOS os itens acima estão marcados: **🎉 PARABÉNS! Seu sistema está funcionando!**

---

## 📝 Notas Finais

### Por que não é 100% automático?

A API do Notion **não permite** criar propriedades/colunas via API em databases inline. Isso é uma limitação da própria API do Notion, não do nosso código.

### Isso vai mudar no futuro?

Possivelmente. Quando a API do Notion adicionar suporte a criar propriedades programaticamente, atualizaremos o script.

### Preciso refazer se limpar o banco?

Sim, mas é rápido:
1. Execute `setup_notion.py` (cria databases vazios)
2. Adicione colunas no Notion (5 minutos)
3. Pronto!

Os IDs ficam salvos no `NotionDatabaseConfig`, então não precisa reconfigurar o `.env`.

---

**Implementado por:** Sistema de Integração Django-Notion  
**Versão:** 1.0 Definitiva  
**Data:** 23 de Outubro de 2025