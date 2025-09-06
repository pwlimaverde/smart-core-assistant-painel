-- Script de inicialização do PostgreSQL
-- Executado automaticamente quando o container é criado pela primeira vez

-- Habilita extensões necessárias para o smart-core-assistant-painel

-- Extensão para vetores (pgvector) - busca semântica
CREATE EXTENSION IF NOT EXISTS vector;

-- Extensão UUID para geração de identificadores únicos
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Extensão para funções de trigrama (busca textual)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Extensão para índices GIN/GiST avançados
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Log de confirmação
\echo 'Extensões PostgreSQL instaladas com sucesso para smart-core-assistant-painel'