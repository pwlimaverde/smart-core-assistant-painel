# Smart Core Assistant Painel

Um painel inteligente para assistente virtual com integração WhatsApp.

## Características

- Interface Django moderna
- Integração com Evolution API com tratamento UTF-8 robusto
- Suporte a MongoDB e Redis
- Processamento de linguagem natural
- Ambiente Docker completo
- Webhook WhatsApp com fallback de encoding automático
- QR Code Evolution API otimizado

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

Veja [ambiente_docker/README-Docker.md](ambiente_docker/README-Docker.md) para instruções detalhadas do Docker.

### Correções Recentes

- ✅ **Webhook WhatsApp**: Implementado tratamento robusto de encoding UTF-8 com fallback automático
- ✅ **Evolution API**: Configuração otimizada para geração de QR Code
- ✅ **Validação JSON**: Prevenção de erros de atributo em objetos string
- ✅ **Logging**: Sistema de logs detalhado para debugging

Para detalhes completos das correções, consulte a seção [Correções Implementadas](ambiente_docker/README-Docker.md#-correções-implementadas) na documentação Docker.

## Licença

MIT License