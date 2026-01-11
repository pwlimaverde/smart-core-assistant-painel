# Tasks - Query Compose Playground

## Visão Geral

Implementação do Playground de Simulação para testar respostas do assistente na tela `verificar-query-compose`.

---

## Fase 1: Backend

### 1.1. [BACKEND] Criar endpoint para simulação
**Prioridade:** Alta  
**Estimativa:** 2-3h  
**Dependências:** Nenhuma

- [ ] Adicionar nova rota em `treinamento/urls.py`:
  - `path("playground-query-compose/", views.playground_query_compose, name="playground_query_compose")`
- [ ] Implementar view `playground_query_compose()` em `views.py`:
  - Validar permissões via `_can_access_training()`
  - Parsear JSON do request body
  - Validar mensagem (não vazia, max 4000 chars)
  - Retornar `JsonResponse` em todos os casos
- [ ] Implementar decorador `@require_POST` para segurança

**Validação:**
- Endpoint retorna 403 para usuários sem permissão
- Endpoint retorna 400 para JSON inválido
- Endpoint aceita POST com `{"mensagem": "...", "incluir_rag": bool}`

---

### 1.2. [BACKEND] Implementar lógica de simulação
**Prioridade:** Alta  
**Estimativa:** 3-4h  
**Dependências:** 1.1

- [ ] Gerar embedding da mensagem via `FeaturesCompose.generate_embeddings()`
- [ ] Buscar comportamento similar via `QueryCompose.buscar_comportamento_similar()`
- [ ] Obter intent types via `QueryCompose.build_intent_types_config()`
- [ ] Executar análise prévia via `FeaturesCompose.analise_previa_mensagem()`
- [ ] (Condicional) Buscar documentos RAG via `Documento.buscar_documentos_similares()`
- [ ] Montar histórico vazio (simulação sem contexto)
- [ ] Executar análise de mensagem via `FeaturesCompose.analise_mensage()`
- [ ] Medir tempo total de processamento
- [ ] Estruturar resposta JSON conforme design

**Validação:**
- Retorna JSON com todos os campos esperados
- Tempo de processamento é medido corretamente
- Nenhum dado é persistido no banco

---

### 1.3. [BACKEND] Tratamento de erros e edge cases
**Prioridade:** Média  
**Estimativa:** 1-2h  
**Dependências:** 1.2

- [ ] Tratar exceções de LLM (timeout, API error)
- [ ] Tratar exceções de embedding
- [ ] Retornar mensagens de erro amigáveis
- [ ] Logar erros com `logger.error()` para diagnóstico
- [ ] Implementar timeout de 30 segundos

**Validação:**
- Erros de LLM retornam JSON de erro adequado
- Logs são gerados para debugging

---

## Fase 2: Frontend

### 2.1. [FRONTEND] Criar seção Playground no template
**Prioridade:** Alta  
**Estimativa:** 2-3h  
**Dependências:** 1.1

- [ ] Adicionar nova `<section>` após tabelas existentes em `verificar_query_compose.html`
- [ ] Criar formulário com:
  - `<textarea>` para mensagem de teste
  - `<input type="checkbox">` para incluir RAG
  - `<button>` para enviar simulação
- [ ] Criar área de resultados (inicialmente oculta)
- [ ] Aplicar estilos Tailwind consistentes com o restante da página

**Validação:**
- Seção aparece corretamente na página
- Formulário é responsivo
- Estilos seguem o padrão existente

---

### 2.2. [FRONTEND] Implementar JavaScript para chamada AJAX
**Prioridade:** Alta  
**Estimativa:** 2-3h  
**Dependências:** 2.1, 1.2

- [ ] Capturar submit do formulário (prevent default)
- [ ] Obter CSRF token do cookie
- [ ] Fazer `fetch()` POST para o endpoint
- [ ] Mostrar loading durante processamento
- [ ] Tratar resposta de sucesso
- [ ] Tratar resposta de erro
- [ ] Desabilitar botão durante processamento

**Validação:**
- Requisição AJAX funciona corretamente
- Loading é exibido durante processamento
- Erros de rede são tratados graciosamente

---

### 2.3. [FRONTEND] Renderizar resultados da simulação
**Prioridade:** Alta  
**Estimativa:** 2-3h  
**Dependências:** 2.2

- [ ] Renderizar seção "Intent Detectado" com tag e confiança
- [ ] Renderizar seção "Comportamento Ativado" com prompt completo
- [ ] Renderizar seção "Contexto RAG" (se incluído) com documentos
- [ ] Renderizar seção "Resposta do Assistente" com texto formatado
- [ ] Exibir métricas (confiabilidade, tempo de processamento)
- [ ] Aplicar formatação visual (cores, ícones, espaçamento)

**Validação:**
- Todos os campos são renderizados corretamente
- UI é clara e legível
- Seções opcionais (RAG) são ocultadas quando vazias

---

## Fase 3: Polimento

### 3.1. [UX] Melhorar feedback visual
**Prioridade:** Média  
**Estimativa:** 1-2h  
**Dependências:** 2.3

- [ ] Adicionar animação de loading (spinner ou skeleton)
- [ ] Adicionar transições suaves ao exibir resultados
- [ ] Destacar visualmente seções importantes
- [ ] Adicionar tooltips explicativos

**Validação:**
- UX é fluida e profissional
- Usuário entende o estado do sistema em todo momento

---

### 3.2. [DOCS] Atualizar documentação
**Prioridade:** Baixa  
**Estimativa:** 1h  
**Dependências:** 3.1

- [ ] Documentar nova funcionalidade no README ou docs
- [ ] Adicionar docstrings completas na view
- [ ] Comentar código JavaScript se necessário

**Validação:**
- Desenvolvedor consegue entender o código rapidamente

---

## Checklist Final

- [ ] Endpoint funcional e seguro
- [ ] UI integrada e responsiva
- [ ] Nenhum dado persistido
- [ ] Erros tratados graciosamente
- [ ] Testes manuais realizados
- [ ] Código formatado (`ruff format`)
- [ ] Tipos verificados (`pyright`)
