# Plano de Implementação: Smart Core Knowledge (Technical View)

## Objetivo
Viabilizar o módulo "Oráculo Interno" utilizando a infraestrutura atual de `ai_engine` do Smart Core Assistant Painel, adicionando camadas de permissionamento e gestão de contexto.

## Arquitetura Proposta

### 1. Modelo de Dados (`KnowledgeBase`)
Precisamos evoluir o armazenamento de documentos para suportar "Contextos" e "Permissões".

*   **Entidade `KnowledgeCollection`**: Agrupador de documentos (ex: "Manual RH", "Procedimentos Fiscais").
    *   Campos: `name`, `description`, `allowed_groups` (Link com Django Groups), `allowed_departments`.
*   **Entidade `DocumentChunk` (Atualização)**:
    *   Adicionar metadados de permissão herdados da `KnowledgeCollection` nos vetores (para filtro no `pgvector`).

### 2. Pipeline de Ingestão (Evolução do `ai_engine`)
Aproveitar os módulos existentes em `src/smart_core_assistant_painel/modules/ai_engine`:
*   `load_document_file`: Manter lógica de extração (PDF, TXT).
*   `generate_chunks`: Ajustar para incluir metadados de permissão no payload do chunk.
*   `generate_embeddings`: Garantir que o vetor guarde o ID da Collection/Tenant.

### 3. Pipeline de RAG (Retrieval Augmented Generation)
O "segredo" do permissionamento está na **Busca (Retrieval)**.

*   **Input**: Pergunta do Usuário + User Context (ID, Groups, Department).
*   **Filtering**: Ao consultar o `pgvector` (ou Vector DB em uso), aplicar filtro rígido:
    ```sql
    WHERE strategies.collection_id IN (user_allowed_collections)
    ```
*   **Generation**: O LLM recebe apenas os chunks que o usuário tem permissão para ver.

### 4. Interface (UI/UX)
*   **Gestão (Admin)**: Tela para criar Coleções, Upload de Arquivos e Selecionar Grupos/Departamentos permitidos.
*   **Chat (User)**: Interface de chat que identifica automaticamente o contexto do usuário.

## Roadmap de Desenvolvimento

1.  **Refatoração do Modelo de Dados**: Criar tabelas de `Collection` e permissões.
2.  **Ajuste na Ingestão**: Atualizar scripts de `load_document` para salvar metadados.
3.  **Ajuste no Retriever**: Implementar lógica de filtro por permissão na busca vetorial.
4.  **Backend API**: Endpoint `v1/oracle/ask` que recebe a pergunta e valida o user.
5.  **Frontend**: Telas de gestão e chat.

## Tecnologias Já Disponíveis no Projeto
*   `langchain`, `pgvector`, `openai`, `django-role-permissions`.
*   Estrutura de `ai_engine` (`generate_chunks`, `generate_embeddings`).

Isso torna o desenvolvimento altamente viável e rápido, focando mais na **lógica de negócio (permissões)** do que em infraestrutura de IA.
