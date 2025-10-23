# 🚀 Setup Rápido - Notion (Manual)

**Tempo estimado:** 15 minutos

---

## ⚠️ IMPORTANTE

A API do Notion tem comportamento inconsistente ao criar databases programaticamente.
**A forma mais confiável é criar os databases manualmente no Notion.**

---

## 📋 Passo 1: Criar Integração (se ainda não fez)

1. Acesse: https://www.notion.so/my-integrations
2. Clique em **"+ New integration"**
3. Nome: `Smart Core Assistant`
4. Workspace: Selecione seu workspace
5. Capabilities: Marque **Read**, **Update** e **Insert content**
6. Clique em **"Submit"**
7. **COPIE O TOKEN** (começa com `secret_`)

---

## 📝 Passo 2: Criar Database de Contatos

### 2.1. Criar a Página

1. No Notion, abra a página onde quer os databases
2. Digite `/database` → Selecione **"Database - Full page"**
3. Nome: `📞 Contatos - CRM`

### 2.2. Adicionar Colunas (EXATAMENTE nesta ordem e nomes)

| Nome da Coluna | Tipo | Como Criar |
|---|---|---|
| `Nome` | Title | Já vem criado, apenas renomeie |
| `Telefone` | Text | Clique em "+" → Text |
| `Email` | Email | Clique em "+" → Email |
| `WhatsApp` | Text | Clique em "+" → Text |
| `Ativo` | Checkbox | Clique em "+" → Checkbox |
| `Data Cadastro` | Date | Clique em "+" → Date |
| `Última Interação` | Date | Clique em "+" → Date |
| `Django ID` | Number | Clique em "+" → Number |

### 2.3. Configurar Django ID

- Clique no nome da coluna `Django ID`
- Em "Number format" escolha: **Number** (sem vírgulas/decimais)

### 2.4. Conectar a Integração

1. Clique nos **"..."** (três pontos) no canto superior direito
2. Selecione **"Connections"** ou **"Add connections"**
3. Busque por: **"Smart Core Assistant"**
4. Clique para conectar

### 2.5. Copiar o Database ID

1. Clique nos **"..."** (três pontos) novamente
2. Selecione **"Copy link"**
3. O link terá formato: `https://www.notion.so/xxxxxxxxx?v=yyyyyyy`
4. O Database ID é a parte `xxxxxxxxx` (entre o último `/` e o `?`)

**ANOTE AQUI:**
```
NOTION_DATABASE_CONTATO_ID=xxxxxxxxx
```

---

## 🏢 Passo 3: Criar Database de Clientes

### 3.1. Criar a Página

1. Volte à página inicial
2. Digite `/database` → Selecione **"Database - Full page"**
3. Nome: `🏢 Clientes - CRM`

### 3.2. Adicionar Colunas (EXATAMENTE nesta ordem e nomes)

| Nome da Coluna | Tipo | Observações |
|---|---|---|
| `Nome Fantasia` | Title | Renomeie o campo título |
| `Razão Social` | Text | |
| `Tipo` | Select | Opções: "Pessoa Física", "Pessoa Jurídica" |
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

### 3.3. Configurar o Campo "Tipo"

1. Clique no nome da coluna `Tipo`
2. Adicione as opções:
   - `Pessoa Física` (cor azul)
   - `Pessoa Jurídica` (cor verde)

### 3.4. Conectar a Integração

**REPITA OS MESMOS PASSOS** do database de Contatos (item 2.4)

### 3.5. Copiar o Database ID

**REPITA OS MESMOS PASSOS** do database de Contatos (item 2.5)

**ANOTE AQUI:**
```
NOTION_DATABASE_CLIENTE_ID=yyyyyyyyy
```

---

## 🔧 Passo 4: Configurar .env

Abra o arquivo `.env` e adicione/atualize:

```bash
# Integração com Notion
NOTION_TOKEN=secret_seu_token_aqui
NOTION_DATABASE_CONTATO_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_CLIENTE_ID=yyyyyyyyyyyyyyyyyyyyyyyyyyyyy
```

---

## ✅ Passo 5: Testar

Execute o teste de integração:

```bash
python test_notion_integration.py
```

Se tudo estiver correto, você verá:

```
✅ TODOS OS TESTES PASSARAM!
```

---

## 🎯 Teste Real

### Criar um Contato

1. Acesse o Django Admin: http://localhost:8000/admin/
2. Vá em **Clientes** → **Contatos**
3. Clique em **"Adicionar Contato"**
4. Preencha:
   - Telefone: `5511999888777`
   - Nome: `João da Silva`
   - Email: `joao@example.com`
5. Clique em **"Salvar"**

**Verifique no Notion:**
- Abra o database "Contatos - CRM"
- Você deve ver "João da Silva" com todos os dados preenchidos!

### Criar um Cliente

1. No Django Admin, vá em **Clientes** → **Clientes**
2. Clique em **"Adicionar Cliente"**
3. Preencha:
   - Nome Fantasia: `Empresa ABC Ltda`
   - Tipo: `Pessoa Jurídica`
   - Telefone: `(11) 3000-0000`
   - Cidade: `São Paulo`
   - UF: `SP`
4. Clique em **"Salvar"**

**Verifique no Notion:**
- Abra o database "Clientes - CRM"
- Você deve ver "Empresa ABC Ltda" com todos os campos!

---

## 🐛 Solução de Problemas

### Erro: "property that exists"

**Causa:** Nome das colunas não está exato  
**Solução:** Verifique que os nomes das colunas estão **EXATAMENTE** como listado acima

### Erro: "unauthorized"

**Causa:** Token inválido ou integração não conectada  
**Solução:** 
1. Verifique o token no .env
2. Verifique se conectou a integração aos databases (Passo 2.4 e 3.4)

### Dados não aparecem no Notion

**Checklist:**
- [ ] Token está correto no .env?
- [ ] Database IDs estão corretos no .env?
- [ ] Integração está conectada aos dois databases?
- [ ] Nomes das colunas estão exatos (incluindo acentos)?
- [ ] Coluna "Django ID" existe e é tipo Number?

---

## 📊 Monitoramento

### Ver Logs no Django Admin

1. Acesse: http://localhost:8000/admin/
2. Vá em **Notion Sync** → **Logs de Sincronização**
3. Você verá todas as operações de sincronização

### Ver Status de Sincronização

1. **Notion Sync** → **Sincronizações de Contatos**
2. **Notion Sync** → **Sincronizações de Clientes**

Aqui você vê quais registros estão sincronizados e quais falharam.

---

## 🎉 Pronto!

Agora toda vez que você:
- ✅ Criar um Contato no Django → Aparece no Notion
- ✅ Atualizar um Contato → Atualiza no Notion
- ✅ Criar um Cliente no Django → Aparece no Notion
- ✅ Atualizar um Cliente → Atualiza no Notion
- ✅ Deletar → Arquiva no Notion

**A sincronização é automática e em tempo real!**

---

## 📞 Suporte

Se tiver problemas:
1. Execute: `python inspect_database.py` para ver as propriedades dos databases
2. Verifique os logs no Django Admin
3. Consulte `CONFIGURACAO_NOTION.md` para instruções detalhadas

---

**Criado em:** 23 de Janeiro de 2025  
**Versão:** 1.0