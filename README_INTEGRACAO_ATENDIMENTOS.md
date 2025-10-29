# Integração de Atendimentos e Mensagens com Notion

## Overview

Este documento descreve a implementação da integração de atendimentos e mensagens com o Notion, seguindo o mesmo padrão das integrações existentes de clientes/contatos e operacional (departamentos/atendentes).

## Estrutura Implementada

### 1. Nova Classe: `NotionAtendimentosDatabaseConstructor`

Localização: `src/smart_core_assistant_painel/app/notion_sync/scripts/script_constructor_notion.py`

Esta classe é responsável por criar e configurar as databases de Atendimentos e Mensagens no Notion, com todos os relacionamentos necessários.

### 2. Databases Criadas

#### Database de Atendimentos
- **Nome**: 🎯 Atendimentos CRM
- **Slug**: `ui_atendimentos_atendimento`
- **Relacionamentos**:
  - Contato (com database existente)
  - Departamento (com database existente)
  - Atendente (com database existente)
  - Mensagens Relacionadas (relacionamento bidirecional)

#### Database de Mensagens
- **Nome**: 💬 Mensagens CRM
- **Slug**: `ui_atendimentos_mensagem`
- **Relacionamentos**:
  - Atendimento Relacionado (relacionamento bidirecional)

### 3. Campos Mapeados

#### Atendimentos
- Protocolo (título)
- Contato (relacionamento)
- Departamento (relacionamento)
- Atendente (relacionamento)
- Status (select: fila, em_atendimento, aguardando_retorno, resolvido, cancelado)
- Prioridade (select: baixa, normal, alta, urgente)
- Assunto (rich_text)
- Data Início (date)
- Data Fim (date)
- Data Última Mensagem (date)
- Canal (select: whatsapp, email, telefone, web)
- Tags (multi_select)
- Avaliação (number)
- Feedback (rich_text)
- Mensagens Relacionadas (relation)

#### Mensagens
- Conteúdo (título)
- Atendimento Relacionado (relation)
- Tipo (select: Texto, Imagem, Vídeo, Áudio, Documento, Sticker, Localização, Contato, Lista, Botões, Enquete, Reação)
- Remetente (select: contato, bot, atendente_humano)
- Timestamp (date)
- Message ID WhatsApp (rich_text)
- Respondida (checkbox)
- Resposta Bot (rich_text)
- Confiança Resposta (percent)
- Metadados (rich_text)

## Como Usar

### Pré-requisitos

1. Ter executado anteriormente a construção de clientes/contatos e operacional:
   ```python
   asyncio.run(run_construction_operacional())
   ```

2. Configurar variáveis de ambiente:
   - `NOTION_TOKEN`: Token de autenticação da API do Notion
   - `NOTION_PAGE_ID`: ID da página pai onde as databases serão criadas

### Opções de Execução

#### 1. Executar Apenas Atendimentos (após operacional)
```python
from notion_sync.scripts.script_constructor_notion import run_atendimentos
run_atendimentos()
```

#### 2. Execução Completa (recomendado)
```python
from notion_sync.scripts.script_constructor_notion import run_full
run_full()
```

#### 3. Usando a função run
```python
from notion_sync.scripts.script_constructor_notion import run
run("full")  # ou "clientes", "operacional", "atendimentos"
```

#### 4. Testar a Construção
```python
from notion_sync.scripts.script_constructor_notion import test_atendimentos_construction
test_atendimentos_construction()
```

## Exemplo de Script Completo

Veja o arquivo `exemplo_execucao_atendimentos.py` na raiz do projeto para um exemplo interativo de execução.

## Fluxo de Execução Recomendado

1. **Primeira Execução** (se ainda não existirem databases):
   ```python
   from notion_sync.scripts.script_constructor_notion import run_full
   run_full()
   ```

2. **Execuções Posteriores** (apenas se necessário reconstruir):
   ```python
   # Se apenas atendimentos precisar ser reconstruído
   from notion_sync.scripts.script_constructor_notion import run_atendimentos
   run_atendimentos()
   ```

## Configurações Salvas

Após a execução, as seguintes configurações serão salvas no modelo `NotionDatabaseConfig`:

### Atendimentos
- **Slug**: `ui_atendimentos_atendimento`
- **Prioridade de Sync**: 7 (alta)
- **Direção**: Bidirecional
- **Modelo Django**: `ui.atendimentos.Atendimento`

### Mensagens
- **Slug**: `ui_atendimentos_mensagem`
- **Prioridade de Sync**: 8 (muito alta)
- **Direção**: Bidirecional
- **Modelo Django**: `ui.atendimentos.Mensagem`

## Validação

Após a execução, você pode verificar:

1. **No Notion**: As databases devem aparecer com todos os campos e relacionamentos configurados
2. **No Django**: As configurações devem estar prontas para sincronização:
   ```python
   from notion_sync.models import NotionDatabaseConfig
   
   atendimento_config = NotionDatabaseConfig.objects.get(slug="ui_atendimentos_atendimento")
   mensagem_config = NotionDatabaseConfig.objects.get(slug="ui_atendimentos_mensagem")
   
   print(f"Atendimento pronto para sync: {atendimento_config.is_ready_for_sync()}")
   print(f"Mensagem pronto para sync: {mensagem_config.is_ready_for_sync()}")
   ```

## Páginas de Exemplo

O script cria páginas de exemplo para demonstrar o funcionamento:

- Um atendimento de exemplo com protocolo "ATT-2024-001"
- Uma mensagem relacionada a este atendimento
- Relacionamento bidirecional configurado corretamente

## Troubleshooting

### Erro Comum: Database não encontrada
```
❌ Database de configuração não encontrada: NotionDatabaseConfig matching query does not exist.
```

**Solução**: Execute primeiro a construção completa com `run_full()` para garantir que todas as databases dependentes sejam criadas.

### Erro Comum: Variáveis de ambiente não configuradas
```
❌ NOTION_TOKEN e NOTION_PAGE_ID devem ser definidos no .env
```

**Solução**: Configure as variáveis de ambiente no arquivo `.env` do projeto.

## Notas Importantes

1. A implementação segue exatamente o mesmo padrão das classes existentes para garantir consistência
2. Os relacionamentos são configurados como bidirecionais, permitindo navegação em ambas as direções
3. A prioridade de sincronização foi definida como alta para atendimentos e muito alta para mensagens devido à sua importância no sistema
4. O script valida a existência das databases dependentes antes de tentar criar os relacionamentos

## Próximos Passos

Após a criação das databases:

1. Configure os mappers de sincronização se ainda não existirem
2. Teste a sincronização bidirecional
3. Monitore os logs para garantir que os dados estão fluindo corretamente
4. Ajuste as configurações de prioridade se necessário