# Relações e Rollups no Notion – Guia Completo para Integração Django/Python

## 📘 Visão Geral  
No Notion, duas propriedades fundamentais permitem conectar e agregar dados entre bancos de dados:

- **Relation (Relação)** → conecta itens entre diferentes bancos de dados (ou no mesmo banco).  
- **Rollup (Agregação)** → coleta e sintetiza informações de registros relacionados via *Relation*.

Essas propriedades são essenciais para criar relacionamentos lógicos e sumarizar dados, especialmente quando você integra o Notion a um backend como **Django/Python via API**.

---

## 🧩 1. Conceito no Notion (Interface)

### 🔗 Relation (Relação)
Uma **relação** conecta registros de um banco de dados a registros de outro.  
Por exemplo:
- Banco **“Clientes”** com uma relação para o banco **“Pedidos”**.  
Cada cliente pode ter uma lista de pedidos associados.

**Características:**
- Pode ser **bidirecional** (two-way): a relação aparece em ambos os bancos.
- Pode ser **auto-referenciada** (self-relation), ligando registros dentro do mesmo banco.
- Pode conter **múltiplos valores** (uma lista de páginas relacionadas).

**Exemplo prático:**
> Banco “Projetos” → campo “Tarefas” (relation) → banco “Tarefas”.  
> Cada projeto mostra as tarefas relacionadas, e cada tarefa tem o campo “Projeto”.

---

### 📊 Rollup (Agregação)
O **rollup** permite *buscar* e *agregar* informações de registros conectados por uma relação.  
Ele utiliza:
1. Uma propriedade de **Relation** existente.
2. Uma propriedade **do banco relacionado**.
3. Uma **função agregadora** (sum, average, count, etc).

**Exemplo prático:**
> Banco “Clientes” com relação a “Pedidos”.  
> Crie um *Rollup* “Total gasto” que soma o campo “Valor” dos pedidos.

**Funções comuns:**
- **Contagem:** `count_all`, `count_unique`, `count_not_empty`
- **Numéricas:** `sum`, `average`, `min`, `max`, `range`
- **Datas:** `earliest_date`, `latest_date`, `date_range`
- **Texto:** `show_original`, `unique`, `concatenate`

---

## 🧠 2. Relações e Rollups via API (Versão Atualizada)

### 🚀 Mudanças Importantes
Segundo o Upgrade Guide (2025-09-03):
- Agora é possível **criar e atualizar** propriedades *relation* e *rollup* diretamente pela API.
- O banco de dados relacionado deve estar **compartilhado** com a integração (token de acesso).

---

### 🧱 Estrutura JSON (Schema da API)

#### Exemplo de propriedade Relation:
```json
"relation": {
  "data_source_id": "UUID-do-banco-relacionado",
  "dual_property": {
    "synced_property_name": "Nome no banco oposto",
    "synced_property_id": "ID da propriedade no banco oposto"
  }
}
```

#### Exemplo de propriedade Rollup:
```json
"rollup": {
  "relation_property_id": "ID-da-relação",
  "relation_property_name": "Nome-da-relação",
  "rollup_property_id": "ID-da-propriedade-agregada",
  "rollup_property_name": "Nome-da-propriedade-agregada",
  "function": "sum"
}
```

---

### 🔍 Leitura de Relações via API

**Endpoint:**  
`GET /v1/pages/{page_id}` ou `POST /v1/databases/{database_id}/query`

**Retorno típico:**
```json
"Cliente": {
  "id": "abc123",
  "type": "relation",
  "relation": [
    { "id": "page-id-1" },
    { "id": "page-id-2" }
  ],
  "has_more": false
}
```

**Criação ou atualização de uma relação:**
```json
"properties": {
  "Cliente": {
    "relation": [{ "id": "UUID-pagina-cliente" }]
  }
}
```

---

### 💾 Leitura de Rollups via API

**Retorno típico:**
```json
"Total Gasto": {
  "id": "xyz456",
  "type": "rollup",
  "rollup": {
    "type": "number",
    "number": 1000,
    "function": "sum"
  }
}
```

**Observações:**
- Rollups **não podem ser atualizados** diretamente (valores derivados).  
- Caso haja mais de **25 itens relacionados**, o resultado pode ser paginado.

---

### 🏗️ Criação de Bancos com Relações e Rollups
```json
{
  "parent": { "type": "page_id", "page_id": "…" },
  "title": [{ "type": "text", "text": { "content": "Projects" } }],
  "properties": {
    "Name": { "title": {} },
    "Tasks": {
      "type": "relation",
      "relation": {
        "data_source_id": "<db-tasks-id>"
      }
    },
    "Total Estimated Time": {
      "type": "rollup",
      "rollup": {
        "relation_property_name": "Tasks",
        "rollup_property_name": "Estimated Time",
        "function": "sum"
      }
    }
  }
}
```

---

## 🐍 3. Exemplo Prático: Integração Django ↔ Notion

### Estrutura Django
```python
# models.py
class Project(models.Model):
    name = models.CharField(max_length=255)
    notion_page_id = models.CharField(max_length=255, blank=True, null=True)

class Task(models.Model):
    name = models.CharField(max_length=255)
    estimated_time = models.FloatField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    notion_page_id = models.CharField(max_length=255, blank=True, null=True)
```

### Criação de página Notion para Task
```python
properties = {
    "Name": {"title": [{"text": {"content": task.name}}]},
    "Project": {"relation": [{"id": notion_project_page_id}]},
    "Estimated Time": {"number": task.estimated_time}
}

notion.pages.create(
    parent={"database_id": tasks_db_id},
    properties=properties
)
```

### Leitura do rollup no Project
```python
page = notion.pages.retrieve(project_page_id)
total_est = page["properties"]["Total Estimated Time"]["rollup"]["number"]
```

---

## ⚠️ 4. Limitações e Boas Práticas

### Limitações
- Bancos relacionados devem estar **compartilhados** com a integração.  
- Rollups **não são editáveis** via API (somente leitura).  
- Rollups complexos (como `median`, `unique`) podem retornar `null`.  
- Relações com mais de **25 registros** exigem paginação.  
- Clientes Python (como `notion-py-client`) podem não suportar as versões mais recentes da API.

### Boas Práticas
✅ Documente seu esquema **Notion ↔ Django**.  
✅ Armazene `notion_page_id` em cada modelo sincronizado.  
✅ Teste manualmente a configuração **Relation + Rollup** no Notion antes da automação.  
✅ Crie funções Python para encapsular chamadas (**create/update/read**).  
✅ Evite *“rollup de rollup”* — são lentos e limitados via API.  
✅ Sempre trate erros e valores nulos ao ler rollups.

---

## 🧭 5. Checklist de Implementação

1. Configure os bancos de dados no Notion (**Projects** e **Tasks**).  
2. Crie propriedades **Relation** e **Rollup**.  
3. Gere o token de integração e **compartilhe ambos os bancos**.  
4. Armazene `page_id` dos registros Django.  
5. Use a API para **criar/atualizar páginas** e sincronizar relações.  
6. Leia os rollups no Django para **relatórios ou dashboards**.  
7. Implemente **controle de erros e paginação**.  
8. Versione o mapeamento entre **campos Django ↔ Notion**.

---

## 📚 6. Referências Oficiais

- Relations & Rollups – Notion Help Center
- Property Object – Notion API Docs
- Retrieve a Page Property – Notion API
- Upgrade Guide (2025-09-03)
- Changelog: Relation and Rollup Support
- Python Client (notion-py-client)

---

## 🧩 Conclusão
As propriedades **Relation** e **Rollup** são os pilares da modelagem relacional dentro do Notion.  
Combinadas à API oficial, elas permitem construir **integrações robustas com Django/Python**, mantendo consistência entre dados locais e a base visual do Notion.

Este guia fornece a base técnica para implementar essas conexões de forma **segura, escalável e documentada**.
