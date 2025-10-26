# Guia de Integração com Notion - Relacionamentos Dinâmicos

## Visão Geral

Este guia explica como configurar a integração com o Notion para sincronização de Contatos e Clientes com relacionamentos dinâmicos, utilizando a API 2025-09-03.

## Pré-requisitos

### 1. Integração no Notion
1. Acesse https://www.notion.so/my-integrations
2. Crie uma nova integração com:
   - Nome: "Smart Core Assistant"
   - Permissões: "Read content", "Update content", "Insert content"
3. Copie o "Internal Integration Token"
4. Adicione capacidades necessárias para suas databases

### 2. Página no Notion
1. Crie uma página para hospedar as databases
2. Compartilhe a página com sua integração:
   - Click em "Share" → "Invite"
   - Selecione sua integração
   - Dê permissões de "Full access"
3. Copie o ID da página:
   - Abra a página no navegador
   - Copie a parte final da URL após o último `/`

### 3. Configuração do Ambiente
```bash
# Criar arquivo .env a partir do exemplo
cp temp/.env.example .env

# Editar com suas credenciais
nano .env
```

## Execução do Script

### Método 1: Via Django Shell (Recomendado)
```bash
uv run python manage.py shell < notion_sync/scripts/script_constructor_notion.py
```

### Método 2: Direto
```bash
uv run python -m notion_sync.scripts.script_constructor_notion
```

## O que o Script Faz

### 1. Criação das Databases
- **👥 Contatos CRM**: Database para sincronização de contatos
- **🏢 Clientes CRM**: Database para sincronização de clientes

### 2. Configuração de Relacionamentos
- **Contatos → Clientes**: Campo "Empresas Relacionadas" (relation)
- **Clientes → Contatos**: Campo "Contatos Relacionados" (relation)

### 3. Configuração no Django
- Salva configurações em `NotionDatabaseConfig`
- Inclui `data_source_ids` para relacionamentos
- Prepara mapeamentos de campos

### 4. Teste de Funcionalidade
- Cria páginas de exemplo
- Testa relacionamentos bidirecionais
- Valida configuração completa

## Estrutura das Databases

### Database de Contatos
| Campo | Tipo | Descrição |
|-------|------|-----------|
| Nome Contato | Title | Nome principal do contato |
| Telefone | Phone | Telefone formatado |
| Email | Email | Endereço de email |
| Nome Perfil WhatsApp | Rich Text | Nome no WhatsApp |
| Ativo | Checkbox | Status do contato |
| Data Cadastro | Date | Data de cadastro |
| Última Interação | Date | Última interação |
| **Empresas Relacionadas** | **Relation** | **Empresas vinculadas** |

### Database de Clientes
| Campo | Tipo | Descrição |
|-------|------|-----------|
| Nome Fantasia | Title | Nome comercial |
| Razão Social | Rich Text | Nome legal |
| Tipo | Select | fisica/juridica |
| CNPJ | Rich Text | CNPJ formatado |
| CPF | Rich Text | CPF formatado |
| Telefone | Phone | Telefone formatado |
| Site | URL | Website |
| Ramo Atividade | Rich Text | Área de atuação |
| CEP | Rich Text | CEP |
| Logradouro | Rich Text | Endereço |
| Número | Rich Text | Número |
| **Contatos Relacionados** | **Relation** | **Contatos vinculados** |

## Como Funciona o Relacionamento

### No Django
```python
# Cliente com múltiplos contatos
cliente = Cliente.objects.get(id=1)
contatos = cliente.contatos.all()  # ManyToMany

# Contato com múltiplos clientes
contato = Contato.objects.get(id=1)
clientes = contato.clientes.all()  # ManyToMany
```

### No Notion
- O relacionamento usa `data_source_id` (API 2025-09-03)
- Bidirecional e automático
- Sincronizado via mappers

## Mappers de Sincronização

### ClienteMapper
```python
# Converte ClienteSync para Notion
from notion_sync.services.mappers.cliente_mapper import ClienteMapper

properties = ClienteMapper.to_notion_properties(cliente_sync)
# Inclui automaticamente:
# - Contatos Relacionados (relation)
# - Metadados de backup
```

### ContatoMapper
```python
# Converte ContatoSync para Notion
from notion_sync.services.mappers.contato_mapper import ContatoMapper

properties = ContatoMapper.to_notion_properties(contato_sync)
# Inclui automaticamente:
# - Empresas Relacionadas (relation)
# - Metadados de backup
```

## Verificação

### 1. No Notion
- Confirme que as databases foram criadas
- Verifique os campos de relacionamento
- Teste criando páginas manualmente

### 2. No Django
```python
# Verificar configurações
from notion_sync.models import NotionDatabaseConfig

contato_config = NotionDatabaseConfig.objects.get(slug="ui_clientes_contato")
cliente_config = NotionDatabaseConfig.objects.get(slug="ui_clientes_cliente")

print(f"Contato DB ID: {contato_config.notion_database_id}")
print(f"Contato DS ID: {contato_config.data_source_id}")
print(f"Cliente DB ID: {cliente_config.notion_database_id}")
print(f"Cliente DS ID: {cliente_config.data_source_id}")
```

### 3. Logs do Script
O script gera logs detalhados:
```
✅ Database de Contatos criada: 897e5a76-ae52-4b48-9fdf-e71f5945d1af
✅ Database de Clientes criada: 6c4240a9-a3ce-413e-9fd0-8a51a4d0a49b
✅ Campo 'Contatos Relacionados' adicionado na database de Clientes
✅ Campo 'Empresas Relacionadas' adicionado na database de Contatos
✅ Relacionamento bidirecional configurado com sucesso
```

## Troubleshooting

### Erros Comuns

1. **"NOTION_TOKEN e NOTION_PAGE_ID devem ser definidos"**
   - Verifique se o arquivo `.env` existe e está preenchido

2. **"Data source IDs não encontrados"**
   - A database pode não ter sido criada corretamente
   - Verifique se a página pai está compartilhada com a integração

3. **"Erro ao configurar relacionamentos"**
   - Verifique se as databases existem
   - Confirme se a integração tem permissões de atualização

4. **"Campo de relacionamento não encontrado"**
   - Pode ser um atraso na API do Notion
   - Execute o script novamente

### Debug

```bash
# Verificar logs detalhados
uv run python -m notion_sync.scripts.script_constructor_notion

# Testar configuração manualmente
uv run python manage.py shell
>>> from notion_sync.scripts.script_constructor_notion import NotionDatabaseConstructor
>>> import asyncio
>>> constructor = NotionDatabaseConstructor()
>>> asyncio.run(constructor.construct_all_databases())
```

## Fluxo de Sincronização

### 1. Criação no Django
```python
# Criar cliente
cliente = Cliente.objects.create(
    nome_fantasia="Empresa Exemplo",
    tipo="juridica"
)

# Criar contato
contato = Contato.objects.create(
    nome_contato="João Silva",
    email="joao@exemplo.com"
)

# Vincular
cliente.contatos.add(contato)
```

### 2. Sincronização Automática
```python
# Processo automático (implementado via signals)
# 1. Cliente/Contato criado/atualizado no Django
# 2. Sync correspondente criado/atualizado
# 3. Mapper prepara dados para Notion
# 4. API do Notion atualizada
# 5. Relacionamentos sincronizados
```

### 3. Verificação de Status
```python
# Verificar sincronização
from notion_sync.models import ClienteSync, ContatoSync

# Status do cliente
cliente_sync = ClienteSync.objects.get(cliente=cliente)
print(f"Status: {cliente_sync.sync_status}")
print(f"ID Externo: {cliente_sync.external_id}")

# Status do contato
contato_sync = ContatoSync.objects.get(contato=contato)
print(f"Status: {contato_sync.sync_status}")
print(f"ID Externo: {contato_sync.external_id}")
```

## Próximos Passos

### 1. Configurar Sincronização Automática
- Implementar signals do Django para criação/atualização
- Configurar task queue (Django-Q2 já configurado)
- Agendar sincronizações periódicas

### 2. Monitoramento
- Logs de sincronização em `SyncLog`
- Dashboard de status no admin do Django
- Alertas de falhas

### 3. Segurança
- Não expor tokens em logs
- Limitar permissões da integração
- Monitorar acessos

## Referências

- [API Notion 2025-09-03](https://developers.notion.com/docs/upgrade-guide-2025-09-03)
- [Notion Python Client](https://pypi.org/project/notion-py-client/)
- [Documentação do Projeto](docs/)

## Suporte

Em caso de problemas:
1. Verifique os logs do script
2. Confirme as configurações no Notion
3. Teste com o modo debug
4. Consulte a seção Troubleshooting