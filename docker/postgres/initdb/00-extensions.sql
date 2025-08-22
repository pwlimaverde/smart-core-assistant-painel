-- Habilita extensões necessárias no PostgreSQL na criação inicial do banco
-- Executado automaticamente pelo entrypoint do container (initdb)

-- Vetores (pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

-- Linguagem Python não-confiável para UDFs (necessário para pgai)
CREATE EXTENSION IF NOT EXISTS plpython3u;

-- Extensão pgai (Timescale) para operações de IA direto no Postgres
CREATE EXTENSION IF NOT EXISTS ai;