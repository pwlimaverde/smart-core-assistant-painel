## 0.8.3

### Fixed
- Resolvidos conflitos de merge priorizando a branch `bugfix/fix-apps-django` nos arquivos:
  - `src/smart_core_assistant_painel/app/ui/oraculo/admin.py`
  - `src/smart_core_assistant_painel/app/ui/oraculo/signals.py`

### Tests
- Removido o teste obsoleto `test_vetor_storage_not_set`, que referenciava a
  propriedade descontinuada `vetor_storage`.
- Suíte de testes executada localmente com `uv run task test-all`: 295 testes
  aprovados; relatório de cobertura HTML gerado em `tests/htmlcov`.

### Chore
- Limpeza de referências a `vetor_storage` em testes e código legado.

## 0.8.2
### Added
- Nova documentação de setup completa e unificada no `README.md`.
- Scripts de setup (`ambiente_docker/`) atualizados e corrigidos para uma instalação mais fluida.
- Guia de validação para garantir que o setup funcione em um ambiente limpo do zero.

### Changed
- Refatorado e simplificado todo o processo de instalação via Docker.
- Unificados múltiplos arquivos de documentação em um `README.md` centralizado para facilitar a consulta.

### Fixed
- Corrigidos bugs no `Dockerfile` que causavam loops e falhas durante a construção da imagem.
- Resolvido problema na geração automática do arquivo `firebase_key.json`.

## 0.8.1
- **fix**: Adição do campo email ao modelo Contato (migração 0003_add_email_to_contato)
- **fix**: Correção dos testes que utilizavam o campo email no modelo Contato
- **docs**: Atualização do README-Docker.md com instruções sobre migrações
- **test**: Execução bem-sucedida da suíte de testes no Docker (305 testes passados)
- **fix**: Resolução do problema de contêineres Docker reiniciando, incluindo:
  - Correção do erro `uv: 1: [/usr/local/bin/docker-entrypoint.sh]: not found` no `smart-core-qcluster-dev`.
  - Resolução da incompatibilidade de versão do PostgreSQL (`database files are incompatible with server`) no `postgres-dev` e `evolution-api-dev` através da remoção dos volumes de dados e reinicialização dos contêineres.
- **test**: Verificação de que todos os contêineres Docker (`smart-core-qcluster-dev`, `evolution-api-dev`, `smart-core-assistant-dev`, `postgres-dev`, `redis-dev`, `postgres-django-dev`) estão em estado `running`.

## 0.8.0
- **fix**: Correção do problema "Nenhum chunk válido encontrado" no Ollama, incluindo:
  - Bug no loop de iteração em `faiss_vetor_storage.py`.
  - Valor padrão para `EMBEDDINGS_MODEL` em `service_hub.py`.
  - Configuração dinâmica da URL do Ollama em `faiss_vetor_storage.py`.
  - Integração da configuração do Ollama com Firebase Remote Config em `features_compose.py`.
  - Configuração local da `OLLAMA_BASE_URL` no arquivo `.env`.
- **docs**: Atualização da documentação `CORREÇÕES_OLLAMA.md` para refletir que o Ollama roda localmente e é acessado via `host.docker.internal` por containers Docker.
- **fix**: Ajuste da configuração de coverage para ignorar pastas de testes de apps Django, via `.coveragerc` e `pytest.ini`.
- Migração do processamento das mensagens para o cluster

## 0.7.0
- **feat**: Configuração completa do ambiente Docker com PostgreSQL e Redis
- **fix**: Correção do problema de geração de QR code na Evolution API
- **fix**: Implementação de tratamento robusto de encoding UTF-8 no webhook WhatsApp
- **fix**: Correção de caminhos Docker e configuração do ambiente de desenvolvimento
- **docs**: Atualização completa da documentação Docker (README-Docker.md)
- **docs**: Documentação para arquitetura PostgreSQL+Redis
- **feat**: Configuração otimizada do QR Code da Evolution API (30s limite, cor personalizada)
- **feat**: Implementação de cache Redis para Evolution API
- **feat**: Configuração de webhook global para Evolution API
- **feat**: Bypass do Firebase Remote Config em modo DEBUG
- **refactor**: Ajustes nas variáveis de ambiente e finalização da configuração Docker
- **refactor**: Revisão do fluxo de recebimento de mensagens
- **refactor**: Atualização do diagrama webhook_whatsapp

## 0.6.0
- **feat**: Adicionada a chave "historico_atendimentos" na função `carregar_historico_mensagens` em `src/smart_core_assistant_painel/app/models.py`.
- **fix**: Removido o campo `Data fim` da lista `readonly_fields` da classe `AtendimentoAdmin` para permitir edição.
- **fix**: Resolvidas falhas nos testes, incluindo a atualização do teste `test_call_non_str`.
- **refactor**: Ajustes gerais de tipo e formatação de código.
- **test**: Ajustados testes para refletir o novo formato de histórico de atendimento.
- **test**: Adicionados testes para cobertura das linhas 138 e 150 do método `_formatar_historico_atendimento`.

## 0.5.0
1 - Correções gerais no dicionario
2 - Simplificação da feature analise_previa_mensagem para rodar em llms menores

## 0.4.0
1 - Refatoração do model treinamento para setar e carregar os documentos do langchain
2 - Criação de modelos para controle de atendimento em Oraculo
3 - Criação de diagrama de relacionamento Oraculo
4 - Criação de diagrama de fluxo de atendimento Oraculo
5 - Feature analise_previa_mensagem para extração dos intents e entity das mensagens 

## 0.3.0
1 - Migração dos metodos em signals para features em ai_engine
2 - Refatoração e melhoria dos códigos para treinamento

## 0.2.0
1 - Services configurado
2 - Features ai_engine implantado

## 0.1.0
Configuração inicial do projeto.
1 - Start e configuração do Django.
2 - Initial load configurado