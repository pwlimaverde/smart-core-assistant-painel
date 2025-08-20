# Guia de Setup Reprodutível - Smart Core Assistant Painel

Este guia garante que o projeto seja configurado de forma consistente e reprodutível em qualquer ambiente.

## Pré-requisitos

- Docker e Docker Compose instalados
- Git instalado
- Arquivo `firebase_key.json` válido (credenciais do Firebase)

## Passos para Setup Completo

### 1. Clonar o Repositório

```bash
git clone <url-do-repositorio>
cd smart-core-assistant-painel
```

### 2. Configurar Variáveis de Ambiente

1. Copie o arquivo de exemplo:
   ```bash
   cp .env.example .env
   ```

2. Edite o arquivo `.env` e configure as seguintes variáveis obrigatórias:
   ```env
   # Firebase
   GOOGLE_APPLICATION_CREDENTIALS=./src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json
   
   # Evolution API
   EVOLUTION_API_KEY=sua_chave_evolution_api
   
   # Outras configurações necessárias...
   ```

### 3. Configurar Credenciais do Firebase

1. Coloque seu arquivo `firebase_key.json` no caminho especificado em `GOOGLE_APPLICATION_CREDENTIALS`:
   ```bash
   mkdir -p src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/
   # Copie seu firebase_key.json para este diretório
   ```

2. **IMPORTANTE**: Verifique se o arquivo JSON está formatado corretamente (não em uma única linha).

### 4. Limpar Ambiente Docker (se necessário)

Se você já executou o projeto antes, limpe o ambiente:

```bash
# Windows
docker system prune -a --volumes

# Linux/Mac
docker system prune -a --volumes
```

### 5. Executar o Setup Automatizado

#### Windows:
```cmd
cd ambiente_docker
setup.bat
```

#### Linux/Mac:
```bash
cd ambiente_docker
chmod +x setup.sh
./setup.sh
```

### 6. Verificar se o Sistema Está Funcionando

Após o setup, verifique:

1. **Aplicação Django**: http://localhost:8000
2. **Admin Django**: http://localhost:8000/admin/ (admin/123456)
3. **Evolution API**: http://localhost:8080
4. **Logs dos containers**:
   ```bash
   docker logs smart-core-assistant-dev
   docker logs smart-core-qcluster-dev
   ```

## O que o Script de Setup Faz

1. **Validação de Ambiente**:
   - Verifica se está na raiz do projeto
   - Valida arquivo `.env`
   - Verifica credenciais Firebase
   - Valida formato JSON do Firebase

2. **Preparação do Ambiente**:
   - Configura variáveis Redis se não existirem
   - Limpa containers, volumes e redes anteriores
   - Remove migrações antigas do Django

3. **Build e Inicialização**:
   - Constrói imagens Docker com labels apropriados
   - Inicia todos os serviços
   - Aguarda conexão com banco de dados

4. **Configuração do Django**:
   - Cria e aplica migrações
   - Configura django-q
   - Cria superusuário admin
   - Inicia django-qcluster

## Estrutura de Serviços

- **django-app**: Aplicação principal Django (porta 8000)
- **django-qcluster**: Processamento de tarefas assíncronas
- **postgres-django**: Banco de dados principal (porta 5433)
- **postgres**: Banco para Evolution API
- **redis**: Cache e filas (porta 6379)
- **evolution-api**: API WhatsApp (porta 8080)

## Resolução de Problemas

### Problema: Imagens Docker `<none>`
**Solução**: As correções implementadas adicionam labels e nomes específicos às imagens para evitar este problema.

### Problema: Firebase JSON inválido
**Solução**: O script agora valida o formato JSON automaticamente.

### Problema: Dependências não instaladas
**Solução**: O Dockerfile foi otimizado para usar `uv sync` corretamente.

### Problema: Containers não iniciam
**Solução**: Verifique os logs e certifique-se de que todas as variáveis de ambiente estão configuradas.

## Comandos Úteis

```bash
# Ver logs de um serviço específico
docker logs -f smart-core-assistant-dev

# Parar todos os serviços
docker compose down

# Parar e remover volumes
docker compose down -v

# Reconstruir apenas um serviço
docker compose build django-app

# Executar comando no container
docker exec -it smart-core-assistant-dev bash

# Ver status dos containers
docker ps
```

## Notas Importantes

1. **Não instale dependências localmente**: O projeto usa Docker, todas as dependências são gerenciadas dentro dos containers.

2. **Firebase**: O arquivo `firebase_key.json` deve estar bem formatado e ser um JSON válido.

3. **Volumes**: Os volumes persistem dados entre reinicializações. Use `docker compose down -v` apenas se quiser limpar completamente.

4. **Hot Reload**: O código fonte é montado como volume, permitindo desenvolvimento com hot reload.

5. **Rede**: Todos os serviços estão na mesma rede Docker para comunicação interna.

## Suporte

Se encontrar problemas:
1. Verifique os logs dos containers
2. Confirme que todas as variáveis de ambiente estão configuradas
3. Certifique-se de que o arquivo Firebase está válido
4. Tente limpar o ambiente Docker e executar o setup novamente