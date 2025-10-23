# 🔧 Troubleshooting: Propriedades do Notion não são criadas

## 🚨 O Problema

Ao executar o script `setup_notion.py`, você pode encontrar o seguinte erro:

```
→ Criando database: Contatos - CRM
  ✓ Database criado: 4011146d-f8c2-40f1-80ea-9832a83bed8c
  • Validando propriedades criadas...
  ⚠ Tentativa 1/3: apenas 0 propriedades encontradas
  ⚠ Tentativa 2/3: apenas 0 propriedades encontradas
  ⚠ Tentativa 3/3: apenas 0 propriedades encontradas

Erro: Falha ao criar propriedades para Contatos - CRM. Esperado: 8, Encontrado: 0
```

## 🔍 Por que Acontece

A API do Notion tem uma **limitação/comportamento peculiar** com databases inline:

1. **Databases Inline**: Quando criados dentro de uma página (parent type = `page_id`), as propriedades podem não ser criadas imediatamente via API
2. **API Response**: A API retorna sucesso (200 OK) mas não cria as propriedades
3. **Delay**: Não é questão de delay - mesmo aguardando minutos, as propriedades não aparecem
4. **Full-page vs Inline**: Databases full-page (workspace parent) têm comportamento diferente

### Evidências no Log

```
INFO:httpx:HTTP Request: POST https://api.notion.com/v1/databases "HTTP/1.1 200 OK"
  ✓ Database criado: 4011146d-f8c2-40f1-80ea-9832a83bed8c
INFO:httpx:HTTP Request: GET https://api.notion.com/v1/databases/... "HTTP/1.1 200 OK"
  ⚠ Tentativa 1/3: apenas 0 propriedades encontradas
```

Note que o GET retorna 200 OK, mas `properties` está vazio.

## 🛠️ Soluções

### Solução 1: Criar Página de Exemplo (Script Atualizado)

O script foi atualizado para criar automaticamente uma página de exemplo que força a criação das propriedades.

**Como funciona:**
1. Cria o database
2. Se propriedades não aparecem, cria uma página de exemplo
3. A página força o Notion a criar as colunas
4. Remove a página de exemplo (opcional)

**Executar:**
```bash
python setup_notion.py
```

O script agora tenta automaticamente essa estratégia.

### Solução 2: Criar Propriedades Manualmente (Recomendado)

Se a automação falhar, crie as propriedades manualmente:

#### Para Database de **Contatos**:

1. Abra o database "Contatos - CRM" no Notion
2. Clique em "+" para adicionar propriedade
3. Adicione as seguintes propriedades:

| Nome                | Tipo       | Observações           |
|---------------------|------------|-----------------------|
| Nome                | Title      | Já existe (padrão)    |
| Telefone            | Text       |                       |
| Email               | Email      |                       |
| WhatsApp            | Text       |                       |
| Ativo               | Checkbox   |                       |
| Data Cadastro       | Date       |                       |
| Última Interação    | Date       |                       |
| Django ID           | Number     | Format: Number        |

#### Para Database de **Clientes**:

1. Abra o database "Clientes - CRM" no Notion
2. Clique em "+" para adicionar propriedade
3. Adicione as seguintes propriedades:

| Nome                | Tipo         | Observações                          |
|---------------------|--------------|--------------------------------------|
| Nome Fantasia       | Title        | Já existe (padrão)                   |
| Razão Social        | Text         |                                      |
| Tipo                | Select       | Opções: Pessoa Física, Pessoa Jurídica |
| CNPJ                | Text         |                                      |
| CPF                 | Text         |                                      |
| Telefone            | Phone        |                                      |
| Site                | URL          |                                      |
| Ramo de Atividade   | Text         |                                      |
| Endereço            | Text         |                                      |
| CEP                 | Text         |                                      |
| Cidade              | Text         |                                      |
| UF                  | Text         |                                      |
| País                | Text         |                                      |
| Ativo               | Checkbox     |                                      |
| Data Cadastro       | Date         |                                      |
| Última Atualização  | Date         |                                      |
| Django ID           | Number       | Format: Number                       |

### Solução 3: Usar Database Existente

Se você já tem um database no Notion com as colunas corretas:

1. Copie o ID do database existente
2. Execute no Django shell:

```python
python manage.py shell

# Dentro do shell:
from smart_core_assistant_painel.app.notion_sync.models import NotionDatabaseConfig

# Para Contatos
NotionDatabaseConfig.set_database(
    model_name="Contato",
    database_id="SEU_DATABASE_ID_AQUI",
    database_name="Contatos - CRM",
    properties_schema={}  # Será preenchido automaticamente
)

# Para Clientes
NotionDatabaseConfig.set_database(
    model_name="Cliente",
    database_id="SEU_DATABASE_ID_AQUI",
    database_name="Clientes - CRM",
    properties_schema={}
)
```

## 🔍 Como Diagnosticar

### 1. Inspecionar Database Criado

Use o script de inspeção:

```bash
python inspect_database_created.py
```

Isso mostrará:
- ✓ Quantas propriedades foram realmente criadas
- ✓ Estrutura completa retornada pela API
- ✓ Diagnóstico do problema

### 2. Validar Configuração Completa

Após resolver o problema de propriedades:

```bash
python validate_notion_setup.py
```

Esse script verifica:
- ✓ Variáveis de ambiente
- ✓ NotionDatabaseConfig no Django
- ✓ Conexão com Notion
- ✓ Databases e suas propriedades
- ✓ NotionSyncService funcionando

### 3. Verificar Manualmente no Notion

1. Abra a página onde os databases foram criados
2. Você deve ver "Contatos - CRM" e "Clientes - CRM"
3. Abra cada database
4. Verifique se as colunas aparecem no topo
5. Se não aparecer, está vazio → precisa criar manualmente

## 📝 Checklist de Resolução

Use este checklist para resolver o problema:

- [ ] Database foi criado no Notion? (verifique na página)
- [ ] ID do database foi salvo no NotionDatabaseConfig? (valide com script)
- [ ] Propriedades aparecem no database do Notion? (abra e veja colunas)
- [ ] Se propriedades não aparecem:
  - [ ] Tentou criar página de exemplo via script?
  - [ ] Criou propriedades manualmente?
  - [ ] Usou database existente com ID?
- [ ] Executou `validate_notion_setup.py` e tudo passou?
- [ ] Testou criar contato no Django e apareceu no Notion?

## 🎯 Workaround Rápido

Se você quer resolver AGORA e continuar trabalhando:

1. **Crie uma página manualmente no database:**
   - Abra o database "Contatos - CRM" no Notion
   - Clique em "New" (ou "+")
   - Preencha alguns campos
   - As colunas serão criadas automaticamente

2. **Salve o ID do database:**
   ```bash
   python manage.py shell
   
   from smart_core_assistant_painel.app.notion_sync.models import NotionDatabaseConfig
   
   # O ID já deve estar salvo se o script criou o database
   # Verifique:
   config = NotionDatabaseConfig.objects.get(model_name="Contato")
   print(f"Database ID: {config.database_id}")
   ```

3. **Teste a sincronização:**
   ```python
   from smart_core_assistant_painel.app.user_management.models import Contato
   
   contato = Contato.objects.create(
       nome="Teste Sync",
       telefone="11999999999",
       email="teste@notion.com"
   )
   
   # Verifique no Notion se apareceu!
   ```

## 🚀 Próximos Passos Após Resolver

1. ✅ Valide tudo com: `python validate_notion_setup.py`
2. ✅ Teste criar contatos/clientes no Django Admin
3. ✅ Verifique se aparecem no Notion automaticamente
4. ✅ Monitore os logs de sincronização:

```python
from smart_core_assistant_painel.app.notion_sync.models import SyncLog

# Ver últimos logs
logs = SyncLog.objects.all().order_by('-timestamp')[:10]
for log in logs:
    print(f"[{log.status}] {log.operation} - {log.model_name}")
```

## 💡 Entendendo o Comportamento da API

### Por que isso acontece?

A documentação oficial do Notion não deixa claro, mas observamos:

1. **Inline Databases**: Têm limitações na criação via API
2. **Schema vs Content**: API separa schema (propriedades) de content (páginas)
3. **Lazy Creation**: Algumas propriedades só são "materializadas" quando uma página é criada
4. **Integration Permissions**: Algumas operações dependem de permissões específicas

### O que funciona:

✅ Criar database inline (estrutura básica)
✅ Criar páginas com propriedades
✅ Ler databases e suas propriedades
✅ Atualizar páginas existentes

### O que tem limitações:

⚠️ Adicionar propriedades via UPDATE em databases inline vazios
⚠️ Modificar schema de databases inline sem páginas
⚠️ Algumas operações bulk em databases inline

## 📚 Referências

- [Notion API - Create Database](https://developers.notion.com/reference/create-a-database)
- [Notion API - Update Database](https://developers.notion.com/reference/update-a-database)
- [Notion API - Database Properties](https://developers.notion.com/reference/property-object)

## 🆘 Ainda com Problemas?

1. **Verifique os logs completos:**
   ```bash
   python setup_notion.py 2>&1 | tee setup_log.txt
   ```

2. **Inspecione o database criado:**
   ```bash
   python inspect_database_created.py
   ```

3. **Valide toda a configuração:**
   ```bash
   python validate_notion_setup.py
   ```

4. **Consulte a documentação completa:**
   - [NOTION_SETUP_GUIDE.md](NOTION_SETUP_GUIDE.md)
   - [NOTION_QUICK_START.md](NOTION_QUICK_START.md)

---

**Última atualização:** 2024-01-15
**Status:** Documentado e com workarounds funcionais