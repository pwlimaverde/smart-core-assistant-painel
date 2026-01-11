## ADDED Requirements

### Requirement: Endpoint de Simulação
O sistema SHALL fornecer um endpoint HTTP para simular respostas do assistente baseadas nas intenções cadastradas, sem persistir dados no banco.

#### Scenario: Simulação bem-sucedida com RAG
- **WHEN** usuário autenticado envia POST para "/treinamento/playground-query-compose/" com mensagem e incluir_rag=true
- **THEN** sistema retorna HTTP 200 com JSON contendo intent_detectado, comportamento, contexto_rag e resposta_bot

#### Scenario: Simulação sem RAG
- **WHEN** usuário autenticado envia POST para "/treinamento/playground-query-compose/" com mensagem e incluir_rag=false
- **THEN** sistema retorna HTTP 200 com JSON contendo intent_detectado, comportamento, contexto_rag vazio e resposta_bot

#### Scenario: Usuário sem permissão
- **WHEN** usuário sem permissão de treinamento envia POST para "/treinamento/playground-query-compose/"
- **THEN** sistema retorna HTTP 403 Forbidden

#### Scenario: Mensagem vazia
- **WHEN** usuário autenticado envia POST com mensagem vazia
- **THEN** sistema retorna HTTP 400 com erro "Mensagem é obrigatória"

#### Scenario: Mensagem muito longa
- **WHEN** usuário autenticado envia POST com mensagem maior que 4000 caracteres
- **THEN** sistema retorna HTTP 400 com erro sobre limite de caracteres

---

### Requirement: Interface do Playground
A tela de verificação de Query Compose SHALL incluir uma seção de Playground para testes interativos sem persistência de dados.

#### Scenario: Exibição da seção Playground
- **WHEN** usuário acessa "/treinamento/verificar-query-compose/"
- **THEN** página exibe seção "Playground - Simular Atendimento" com campo de texto, checkbox "Incluir busca RAG" e botão "Simular Resposta"

#### Scenario: Execução de simulação via interface
- **WHEN** usuário preenche campo de texto e clica "Simular Resposta"
- **THEN** botão fica desabilitado, loading é exibido, e resultados aparecem após resposta

#### Scenario: Visualização de resultados
- **WHEN** simulação é executada com sucesso
- **THEN** tela exibe Intent Detectado, Comportamento Ativado, Contexto RAG, Resposta do Assistente, confiabilidade e tempo de processamento

#### Scenario: Exibição de erro
- **WHEN** simulação é executada e ocorre erro
- **THEN** tela exibe mensagem de erro descrevendo o problema

---

### Requirement: Métricas de Simulação
O sistema SHALL fornecer métricas sobre a simulação executada no response JSON.

#### Scenario: Métricas incluídas no response
- **WHEN** simulação é executada com sucesso
- **THEN** response JSON inclui confiabilidade (0-1), tempo_processamento_ms e comportamento.distancia
