## 0.8.0
- **fix**: Correção do problema "Nenhum chunk válido encontrado" no Ollama, incluindo:
  - Bug no loop de iteração em `faiss_vetor_storage.py`.
  - Valor padrão para `FAISS_MODEL` em `service_hub.py`.
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