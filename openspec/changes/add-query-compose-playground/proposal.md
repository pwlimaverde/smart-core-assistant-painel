# Change: Adicionar Playground de Simulação de Query Compose

## Why

Atualmente não há forma de testar as respostas do assistente baseadas nas intenções (QueryCompose) cadastradas sem enviar mensagens reais via WhatsApp, o que é lento, gera dados de produção desnecessários e não oferece visibilidade sobre o raciocínio interno da IA.

## What Changes

- **ADDED**: Nova seção de Playground na página `verificar-query-compose`
- **ADDED**: Endpoint AJAX `POST /treinamento/playground-query-compose/` para simulação
- **ADDED**: Campo de input para simular mensagem do usuário
- **ADDED**: Visualização do fluxo de processamento (intent detectado, prompt usado)
- **ADDED**: Visualização da resposta final do assistente
- **ADDED**: Opção de incluir busca semântica (RAG) na simulação
- **ADDED**: Métricas de confiabilidade e tempo de processamento
- Nenhuma persistência de dados durante simulação

## Impact

- **Affected specs**: 
  - `playground-simulacao` (nova capability)
- **Affected code**:
  - `treinamento/views.py` - nova view `playground_query_compose()`
  - `treinamento/urls.py` - nova rota
  - `treinamento/templates/treinamento/verificar_query_compose.html` - nova seção UI

## Escopo Detalhado

### Incluído
- Seção de Playground na página `verificar-query-compose`
- Campo de input para simular mensagem do usuário
- Visualização do fluxo de processamento (intent detectado, prompt usado)
- Visualização da resposta final do assistente
- Opção de executar busca semântica (RAG) opcionalmente
- Nenhuma persistência de dados

### Excluído
- Integração com WhatsApp real
- Histórico de simulações (não persiste)
- Edição de intents diretamente no playground

## Análise Técnica

### Componentes Envolvidos

1. **views.py** (`treinamento/views.py`):
   - Nova view `playground_query_compose()` com endpoint AJAX
   - Lógica de simulação isolada (sem persistência)

2. **templates** (`verificar_query_compose.html`):
   - Nova seção UI para o playground
   - Formulário com input de texto
   - Área de visualização dos resultados

3. **FeaturesCompose** (`modules/ai_engine`):
   - Reutilização de `generate_embeddings()`
   - Reutilização de `analise_previa_mensagem()` ou lógica similar
   - Reutilização de `analise_mensage()`

4. **QueryCompose** (`treinamento/models.py`):
   - Reutilização de `buscar_comportamento_similar()`
   - Reutilização de `build_intent_types_config()`

### Fluxo de Processamento Atual (Referência)

O fluxo de atendimento atual (`attendance_orchestrator.py`) faz:

```
1. Recebe mensagem → analisa conteúdo (intent/entidades)
2. Gera embedding da mensagem
3. Busca comportamento similar via QueryCompose.buscar_comportamento_similar()
4. Busca documentos RAG via Documento.buscar_documentos_similares()
5. Monta prompt com intents + comportamentos + RAG
6. Chama LLM para gerar resposta
7. Registra resposta no banco
```

O **Playground simulará os passos 1-6**, omitindo o passo 7 (registro).

## UI Proposta

```
┌──────────────────────────────────────────────────────────┐
│ 🧪 Playground - Simular Atendimento                       │
├──────────────────────────────────────────────────────────┤
│ Digite uma mensagem de teste:                             │
│ ┌────────────────────────────────────────────────────────┐│
│ │ Qual é o preço do produto X?                           ││
│ └────────────────────────────────────────────────────────┘│
│ ☑ Incluir busca RAG (documentos)                         │
│                                                           │
│ [▶ Simular Resposta]                                     │
├──────────────────────────────────────────────────────────┤
│ 📊 Resultado da Simulação:                               │
│                                                           │
│ ✅ Intent Detectado: orcamento (confiança: 0.92)         │
│                                                           │
│ 📚 Comportamento Ativado:                                │
│ ┌────────────────────────────────────────────────────────┐│
│ │ Quando o cliente perguntar sobre preço, solicitar      ││
│ │ mais detalhes sobre o produto desejado...              ││
│ └────────────────────────────────────────────────────────┘│
│                                                           │
│ 📝 Contexto RAG:                                         │
│ ┌────────────────────────────────────────────────────────┐│
│ │ [1] Tabela de preços - produto X: R$ 99,90             ││
│ │ [2] Promoção vigente - 10% de desconto                 ││
│ └────────────────────────────────────────────────────────┘│
│                                                           │
│ 🤖 Resposta do Assistente:                               │
│ ┌────────────────────────────────────────────────────────┐│
│ │ Olá! O produto X está disponível por R$ 99,90.         ││
│ │ Atualmente temos uma promoção de 10% de desconto...    ││
│ └────────────────────────────────────────────────────────┘│
│                                                           │
│ ⚡ Confiabilidade: 0.87 | Tempo: 1.2s                    │
└──────────────────────────────────────────────────────────┘
```

## Considerações de Segurança

- Nenhum dado é persistido no banco
- Tokens de API são consumidos normalmente (LLM/Embeddings)
- Acesso restrito aos mesmos usuários que podem acessar `verificar-query-compose`
- Rate limiting pode ser considerado para evitar abuso

## Dependências

- OpenAI/Groq API para geração de embeddings e resposta LLM
- Nenhuma nova dependência externa necessária

## Arquivos Relacionados

| Arquivo | Modificação |
|---------|-------------|
| `treinamento/views.py` | Nova view/endpoint para playground |
| `treinamento/urls.py` | Nova rota para playground |
| `treinamento/templates/treinamento/verificar_query_compose.html` | Nova seção UI |
| `modules/ai_engine/features/features_compose.py` | Possível nova função de simulação |
