# Smart Core Assistant Painel

Um painel inteligente para assistente virtual com integração WhatsApp.

## Características

- Interface Django moderna
- Integração com Evolution API
- Suporte a MongoDB e Redis
- Processamento de linguagem natural
- Ambiente Docker completo

## Instalação

### Usando Docker (Recomendado)

```bash
# Windows
powershell -ExecutionPolicy Bypass -File scripts/start-docker.ps1

# Linux/Mac
./scripts/setup-docker.sh
```

### Desenvolvimento Local

```bash
# Instalar dependências
uv sync --dev

# Executar migrações
uv run migrate

# Iniciar servidor
uv run dev
```

## Configuração

1. Copie `.env.example` para `.env`
2. Configure suas variáveis de ambiente
3. Execute as migrações do Django
4. Inicie os serviços

## Documentação

Veja [README-Docker.md](README-Docker.md) para instruções detalhadas do Docker.

## Licença

MIT License