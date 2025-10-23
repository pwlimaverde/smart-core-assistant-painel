# 🔧 Guia de Configuração - Integração Django com Notion

**Data:** 23 de Janeiro de 2025  
**Versão:** 1.0  
**Status:** Pronto para Uso

---

## 📋 Visão Geral

Este guia contém as instruções passo-a-passo para configurar a integração entre o sistema Django e o Notion. Após seguir este guia, o sistema estará sincronizando automaticamente Clientes e Contatos com seus databases no Notion.

---

## 🎯 Pré-requisitos

- ✅ Conta no Notion (Free ou paga)
- ✅ Workspace no Notion onde você tem permissões de admin
- ✅ Sistema Django instalado e funcionando
- ✅ Variáveis de ambiente configuradas (.env)

---

## 📝 Etapas de Configuração

### Etapa 1: Criar Integração no Notion (5 minutos)

#### 1.1. Acesse a página de integrações

1. Abra seu navegador
2. Acesse: https://www.notion.so/my-integrations
3. Faça login com sua conta do Notion

#### 1.2. Crie uma nova integração

1. Clique no botão **"+ New integration"**
2. Preencha os campos:
   - **Name**: `Smart Core Assistant` (ou o nome que preferir)
   - **Associated workspace**: Selecione seu workspace
   - **Logo**: (opcional) adicione um logo

#### 1.3. Configure as capacidades (Capabilities)

Na seção **Capabilities**, marque as seguintes opções:

- ✅ **Read content** (Ler conteúdo)
- ✅ **Update content** (Atualizar conteúdo)  
- ✅ **Insert content** (Inserir conteúdo)

> ⚠️ **IMPORTANTE**: Não é necessário marcar "Read user information" ou "Read comments"

#### 1.4. Configure o tipo de conteúdo

Na seção **Content Capabilities**, certifique-se que está selecionado:

- ✅ **No user information** (padrão)

#### 1.5. Submeta a integração

1. Clique no botão **"Submit"**
2. Aguarde a confirmação

#### 1.6. Copie o Token de Integração

1. Na página da integração criada, você verá uma seção chamada **"Internal Integration Token"**
2. Clique em **"Show"** para revelar o token
3. Clique em **"Copy"** para copiar o token
4. O token tem o formato: `secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`

> ⚠️ **IMPORTANTE**: Guarde este token com segurança! Não compartilhe publicamente.

**Anote aqui (temporariamente):**
```
NOTION_TOKEN=secret_seu_token_aqui
```

---

### Etapa 2: Criar Database de Contatos (10 minutos)

#### 2.1. Crie uma nova página no Notion

1. Abra o Notion
2. No workspace desejado, clique em **"+ New page"**
3. Dê o nome: `📞 Contatos - CRM`

#### 2.2. Adicione um Database

1. Digite `/database` e selecione **"Database - Inline"**
2. Ou clique no botão **"Table"** na barra de ferramentas

#### 2.3. Configure as colunas (propriedades)

O database deve ter EXATAMENTE as seguintes colunas (clique em "+" para adicionar):

| Nome da Coluna | Tipo | Observações |
|---|---|---|
| **Nome** | Title | Já vem por padrão, apenas renomeie |
| **Telefone** | Rich Text | Campo obrigatório |
| **Email** | Email | Tipo específico "Email" |
| **WhatsApp** | Rich Text | Nome do perfil no WhatsApp |
| **Ativo** | Checkbox | Status ativo/inativo |
| **Data Cadastro** | Date | Data de criação |
| **Última Interação** | Date | Data da última interação |
| **Django ID** | Number | ⚠️ OBRIGATÓRIO - Referência do Django |

#### 2.4. Configure o Django ID

Para a coluna **Django ID**:
1. Clique no título da coluna
2. Selecione "Number"
3. Em "Number format", escolha **"Number"** (sem formatação)

#### 2.5. Obtenha o Database ID

1. Clique nos **"..."** (três pontos) no canto superior direito do database
2. Selecione **"Copy link"**
3. Você receberá um link no formato:
   ```
   https://www.notion.so/workspace/1a2b3c4d5e6f7g8h9i0j?v=abc123
   ```
4. O **Database ID** é a parte entre o último `/` e o `?`:
   ```
   1a2b3c4d5e6f7g8h9i0j
   ```

**Anote aqui (temporariamente):**
```
NOTION_DATABASE_CONTATO_ID=1a2b3c4d5e6f7g8h9i0j
```

#### 2.6. Conecte a Integração ao Database

> ⚠️ **CRÍTICO**: Esta etapa é OBRIGATÓRIA! Sem ela a integração não funcionará.

1. Clique nos **"..."** (três pontos) no canto superior direito do database
2. Selecione **"Connections"** ou **"Add connections"**
3. Procure por **"Smart Core Assistant"** (o nome da sua integração)
4. Clique para conectar
5. Confirme a conexão

Você verá uma mensagem: "Smart Core Assistant can now edit and view this database"

---

### Etapa 3: Criar Database de Clientes (15 minutos)

#### 3.1. Crie uma nova página no Notion

1. No workspace, clique em **"+ New page"**
2. Dê o nome: `🏢 Clientes - CRM`

#### 3.2. Adicione um Database

1. Digite `/database` e selecione **"Database - Inline"**

#### 3.3. Configure as colunas (propriedades)

O database deve ter EXATAMENTE as seguintes colunas:

| Nome da Coluna | Tipo | Observações |
|---|---|---|
| **Nome Fantasia** | Title | Já vem por padrão, renomeie |
| **Razão Social** | Rich Text | Nome oficial |
| **Tipo** | Select | Opções: "Pessoa Física", "Pessoa Jurídica" |
| **CNPJ** | Rich Text | Formato: 12.345.678/0001-99 |
| **CPF** | Rich Text | Formato: 123.456.789-00 |
| **Telefone** | Phone Number | Tipo específico "Phone" |
| **Site** | URL | Tipo específico "URL" |
| **Ramo de Atividade** | Rich Text | Área de atuação |
| **Endereço** | Rich Text | Endereço completo formatado |
| **CEP** | Rich Text | Código postal |
| **Cidade** | Rich Text | Município |
| **UF** | Rich Text | Estado (sigla) |
| **País** | Rich Text | País |
| **Ativo** | Checkbox | Status ativo/inativo |
| **Data Cadastro** | Date | Data de criação |
| **Última Atualização** | Date | Data da última modificação |
| **Django ID** | Number | ⚠️ OBRIGATÓRIO - Referência do Django |

#### 3.4. Configure o campo Tipo (Select)

Para a coluna **Tipo**:
1. Clique no título da coluna
2. Selecione "Select"
3. Adicione as opções:
   - `Pessoa Física` (cor: azul)
   - `Pessoa Jurídica` (cor: verde)

#### 3.5. Obtenha o Database ID

1. Clique nos **"..."** (três pontos) no canto superior direito
2. Selecione **"Copy link"**
3. Extraia o Database ID do link (igual ao passo 2.5)

**Anote aqui (temporariamente):**
```
NOTION_DATABASE_CLIENTE_ID=xyz123abc456def789
```

#### 3.6. Conecte a Integração ao Database

> ⚠️ **CRÍTICO**: Repita o mesmo processo da Etapa 2.6!

1. Clique nos **"..."** → **"Connections"**
2. Adicione **"Smart Core Assistant"**
3. Confirme a conexão

---

### Etapa 4: Configurar Variáveis de Ambiente (2 minutos)

#### 4.1. Abra o arquivo .env

No diretório raiz do projeto, abra o arquivo `.env` (crie se não existir).

#### 4.2. Adicione as variáveis

Cole as três variáveis que você anotou:

```bash
# Integração com Notion
NOTION_TOKEN=secret_seu_token_completo_aqui
NOTION_DATABASE_CONTATO_ID=1a2b3c4d5e6f7g8h9i0j
NOTION_DATABASE_CLIENTE_ID=xyz123abc456def789
```

> ⚠️ **IMPORTANTE**: Substitua pelos valores reais que você copiou!

#### 4.3. Salve o arquivo

Salve e feche o arquivo `.env`.

---

### Etapa 5: Testar a Integração (5 minutos)

#### 5.1. Teste a Conexão

Execute o script de teste:

```bash
python test_notion_integration.py
```

O script irá:
1. ✅ Verificar se as configurações estão presentes
2. ✅ Testar conexão com a API do Notion
3. ✅ Criar um Contato de teste e sincronizar
4. ✅ Criar um Cliente de teste e sincronizar
5. ✅ Executar health check

#### 5.2. Resultados Esperados

Você deve ver algo como:

```
================================================================================
✅ TODOS OS TESTES PASSARAM!

A integração com o Notion está funcionando perfeitamente.
Verifique os dados no Notion!
================================================================================
```

#### 5.3. Verifique no Notion

1. Abra o database de **Contatos** no Notion
2. Você deve ver uma nova página criada: `Teste Integração Notion`
3. Abra o database de **Clientes** no Notion
4. Você deve ver: `Teste Integração Notion Ltda`

> 💡 **NOTA**: Os registros de teste são automaticamente removidos após o script.

---

## 🎉 Integração Configurada!

Parabéns! A integração está funcionando. A partir de agora:

- ✅ Quando você criar um **Contato** no Django → Sincroniza automaticamente com Notion
- ✅ Quando você criar um **Cliente** no Django → Sincroniza automaticamente com Notion
- ✅ Atualizações no Django → Refletem no Notion
- ✅ Deleções no Django → Arquivam no Notion

---

## 🧪 Testando Manualmente

### Criar um Contato Real

1. Acesse o Django Admin: http://localhost:8000/admin/
2. Vá em **Clientes** → **Contatos**
3. Clique em **"Adicionar Contato"**
4. Preencha os dados:
   - **Telefone**: 5511988887777
   - **Nome**: João da Silva
   - **Email**: joao@example.com
5. Clique em **"Salvar"**

**Verifique no Notion:**
- Abra o database de Contatos
- Você verá a página "João da Silva" com todos os dados

### Criar um Cliente Real

1. No Django Admin, vá em **Clientes** → **Clientes**
2. Clique em **"Adicionar Cliente"**
3. Preencha:
   - **Nome Fantasia**: Empresa ABC Ltda
   - **Tipo**: Pessoa Jurídica
   - **Telefone**: (11) 3000-0000
4. Clique em **"Salvar"**

**Verifique no Notion:**
- Abra o database de Clientes
- Você verá "Empresa ABC Ltda" com todos os campos preenchidos

---

## 🔍 Monitoramento e Logs

### Ver Logs de Sincronização

No Django Admin:
- Acesse: **Notion Sync** → **Logs de Sincronização**
- Você verá todas as operações realizadas

### Ver Status de Sincronização

No Django Admin:
- **Notion Sync** → **Sincronizações de Contatos** (status de cada contato)
- **Notion Sync** → **Sincronizações de Clientes** (status de cada cliente)

---

## ❓ Problemas Comuns

### Erro: "Token do Notion não encontrado"

**Causa**: Variável `NOTION_TOKEN` não está no .env  
**Solução**: Adicione a variável conforme Etapa 4

### Erro: "Database ID não configurado"

**Causa**: Variáveis `NOTION_DATABASE_*_ID` ausentes  
**Solução**: Adicione as variáveis conforme Etapa 4

### Erro: "object_not_found" ou "Could not find database"

**Causa**: Integração não está conectada ao database  
**Solução**: Repita as Etapas 2.6 e 3.6 (Conectar integração)

### Erro: "unauthorized"

**Causa**: Token inválido ou expirado  
**Solução**: Gere um novo token (Etapa 1) e atualize o .env

### Os dados não aparecem no Notion

**Checklist**:
1. ✅ Token está correto no .env?
2. ✅ Database IDs estão corretos no .env?
3. ✅ Integração está conectada aos databases?
4. ✅ Colunas do database estão exatamente como especificado?
5. ✅ Coluna "Django ID" existe e é do tipo Number?

### Logs mostram "pending" mas não sincroniza

**Causa**: Erro silencioso na sincronização  
**Solução**:
1. Verifique os logs do Django no terminal
2. Execute: `python test_notion_integration.py`
3. Verifique se há erros detalhados

---

## 🎓 Próximos Passos

Agora que a integração está funcionando:

1. **Personalize os Databases**: Adicione views, filtros e agrupamentos no Notion
2. **Crie Dashboards**: Use as relações entre databases para criar visões poderosas
3. **Automatize Workflows**: Configure automações no Notion baseadas nos dados
4. **Monitore**: Acompanhe os logs regularmente

---

## 📚 Recursos Adicionais

- [Documentação da API do Notion](https://developers.notion.com/)
- [Notion Integration Guide](https://www.notion.so/help/create-integrations-with-the-notion-api)
- [Database Properties Reference](https://developers.notion.com/reference/database)

---

## 📞 Suporte

Se encontrar problemas:

1. Consulte a seção "Problemas Comuns" acima
2. Verifique os logs no Django Admin
3. Execute o script de teste: `python test_notion_integration.py`
4. Consulte a documentação em `IMPLEMENTACAO_NOTION_SYNC_FASE1.md`

---

**Configuração criada por**: Jules (AI Assistant)  
**Data**: 23 de Janeiro de 2025  
**Versão**: 1.0