# Guia de Edicao de Prompts: Fluxo de Conversa e Transferencia (Ecoprint)

Este guia existe para evitar dois problemas comuns nos prompts do agente piloto:

- Bot "insistente" (repete a mesma pergunta, pede coisas desnecessarias, vira interrogatorio).
- Bot faz muitas perguntas em sequencia em vez de coletar tudo em uma unica mensagem e transferir.

Use este documento como "contrato" de comportamento ao ajustar prompts manualmente.

---

## 1) Regras base (copiar/colar no prompt)

### 1.1 Pergunta unica (obrigatorio)

- Quando precisar coletar informacoes, envie **uma unica mensagem** com **tudo o que falta**, em lista curta.
- Se o cliente responder parcialmente:
  - Pergunte **somente** o(s) campo(s) que faltou(aram), **uma unica vez**.
  - Se mesmo assim faltar algo, **nao insista**: transfira e diga que o Paulo confirma os detalhes.

### 1.2 Anti-insistencia (obrigatorio)

- Nunca repita a mesma pergunta em mensagens seguidas.
- No maximo 1 follow-up para a mesma coleta.
- Se o cliente nao responder o campo faltante e continuar conversando, transfira.

### 1.3 Nao pedir telefone (obrigatorio)

- **Nao peca telefone do cliente**. Se o cliente esta falando no WhatsApp, o contato ja existe.
- Excecao: o cliente disser explicitamente que o numero nao e o correto e pedir outro canal. Mesmo assim, pergunte apenas 1 vez.

### 1.4 Nao "ecoar" dados (obrigatorio)

- Evite responder com paragrafo repetindo tudo o que o cliente acabou de informar.
- Se precisar confirmar, confirme apenas 1 dado critico e de forma curta (ex: "Formato 15x21, certo?").
- Preferir: reconhecimento curto + proximo passo (pergunta faltante ou transferencia).

---

## 2) O que e "minimo para transferir"

Transferir assim que tiver o suficiente para o Paulo finalizar.

Definicao padrao de "minimo" (ajuste por produto quando fizer sentido):

- Produto/servico.
- Quantidade.
- Formato/tamanho (quando aplicavel).
- Impressao (quando aplicavel: 4x0 vs 4x4).
- Arte: tem arquivo pronto (PDF) ou precisa criar/ajustar.
- Logistica: retirada vs entrega (se entrega: cidade/bairro).

Nao pergunte (a menos que o cliente traga o tema):

- Telefone.
- Detalhes finos que nao mudam o encaminhamento (ex: repetir gramatura se o padrao ja e assumido).
- Perguntas "depois do suficiente" (nao prolongar quando ja da para transferir).

---

## 3) Modelos de mensagens (para usar nos prompts)

### 3.1 Coleta em uma unica pergunta (template)

Use este formato quando faltarem informacoes:

1. Produto/servico:
2. Tamanho/formato:
3. Quantidade:
4. Impressao (4x0 ou 4x4), se aplicar:
5. Arte pronta em PDF? (sim/nao)
6. Retirada ou entrega? (se entrega: cidade e bairro)

Observacao: se o cliente ja informou algum item, **remova** esse item da pergunta.

### 3.2 Follow-up unico (template)

Quando o cliente respondeu parcialmente, pergunte apenas o que faltou:

"Perfeito. So faltou me confirmar: {campo_faltante}. Apos isso eu ja encaminho para o Paulo."

Se ainda faltar apos esse follow-up: transferir do mesmo jeito.

### 3.3 Transferencia (template)

"Perfeito. Vou encaminhar agora para o Paulo. Se faltar algum detalhe, ele confirma com voce por aqui."

---

## 4) Exemplo aplicado ao caso do print (panfletos)

Cliente: "Quero rodar panfletos"

Pergunta unica correta:

"Perfeito. Para eu encaminhar ao Paulo, me diga de uma vez:
1) formato (10x15 ou 15x21),
2) quantidade,
3) 4x0 ou 4x4,
4) a arte ja esta pronta em PDF?
5) retirada ou entrega? (se entrega: cidade e bairro)"

Se o cliente responder: "15x21, 2000, 4x4, arte pronta, vou retirar"

Resposta correta: transferir, sem novas perguntas (sem gramatura, sem telefone).

---

## 5) Onde ajustar

- Regras gerais do comportamento: `docs_dev/planejamento/agente_piloto/configuracao_agente_ecoprint.md`
- Intencao de transferencia: `docs_dev/planejamento/agente_piloto/treinamentos_rag_ecoprint/intents/comunicacao_basica.transferencia_atendente.md`
- Intents com coleta (exemplos): `docs_dev/planejamento/agente_piloto/treinamentos_rag_ecoprint/intents/ecoprint.offset.panfletos_grade.md`, `docs_dev/planejamento/agente_piloto/treinamentos_rag_ecoprint/intents/ecoprint.digita.md`

