# 📖 Planejamento de Implantação — QueryCompose (Controle de Intents com Embeddings)

## 1. Caso de uso

A central de controle de atendimento precisa identificar a **intenção** (intent) por trás de cada mensagem recebida do cliente.  

Cada intent terá:  
- **description** → usado para gerar o embedding e classificar mensagens  
- **tag** → rótulo auxiliar para organizar intents  
- **comportamento** → instruções que definem o comportamento da LLM  
- **embedding** → vetor armazenado no Postgres com `pgvector`  

### Objetivo
Garantir que cada mensagem seja conciliada com o intent mais adequado e que a LLM responda seguindo o **prompt system** definido para esse intent.

---

## 2. Fluxo lógico do sistema

1. **Cadastro do intent (prévio)**
   - Exemplo:
     - tag: `orcamento`
     - description: `"Solicitação de orçamento de produtos e serviços"`
     - comportamento: `"Você deve responder como um orçamentista, pedindo detalhes do produto e quantidade."`
   - Uma *feature separada* gera o embedding da `description` e preenche o campo `embedding`.

---

2. **Recebimento da mensagem do cliente**
   - Exemplo de mensagem:  
     `"quero um orçamento para 10 caixas de papelão"`

   - O sistema gera o embedding da mensagem recebida.

---

3. **Pesquisa por similaridade (no banco)**
   - Busca realizada no Postgres com `pgvector`:
     ```python
     matches = (
         QueryCompose.objects
         .exclude(embedding__isnull=True)
         .order_by("embedding__cosine_distance", message_embedding)[:1]
     )
     best_match = matches[0]
     ```

   - Exemplo de resultado:  
     - tag: `orcamento`  
     - similaridade: `0.92`

---

4. **Seleção do comportamento e repasse para LLM**
   - Prompt associado ao intent é carregado:
     - `"Você deve responder como um orçamentista, pedindo detalhes do produto e quantidade."`

   - Esse prompt é injetado no *system prompt* da LLM.

---

5. **Resposta ao cliente**
   - A LLM responde de acordo com o comportamento definido no prompt.

---

## 3. Vantagens do design

- **Simplicidade** → apenas campos essenciais, fácil manutenção.  
- **Escalabilidade** → `pgvector` com índice `ivfflat` permite buscas rápidas mesmo com milhares de intents.  
- **Flexibilidade** → novos intents podem ser cadastrados sem alterar o código.  
- **Controle do comportamento da LLM** → cada intent define seu próprio *system prompt*.  

---

## 4. Exemplo lógico do fluxo

```text
Usuário → "quero um orçamento"
↓
Sistema → gera embedding da mensagem
↓
Banco (pgvector) → encontra descrição mais parecida
   - "Solicitação de orçamento de produtos e serviços"
↓
Sistema → pega o prompt associado:
   - "Você deve responder como um orçamentista..."
↓
LLM → responde ao usuário como orçamentista
