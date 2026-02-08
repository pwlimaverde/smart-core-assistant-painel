# Intent: Saudacao

## Tag
`saudacao`

## Grupo
`comunicacao_basica`

## Descricao (para embedding)
Expressoes usadas para abrir uma interacao ou iniciar uma conversa, reconhecendo a presenca do interlocutor de forma cordial.

## Exemplo (queries que representam a intent)
- "Ola, Ecoprint!"
- "Bom dia, gostaria de atendimento."
- "Oi, tudo bem?"
- "Boa tarde."
- "Oi!"

## Comportamento (respostas/acoes do assistente)
Objetivo: iniciar a conversa de forma cordial e contextual.

Regras de contexto (importante):
- Se for a PRIMEIRA interacao na conversa (primeira mensagem do contato):
  - Faca uma apresentacao curta, deixando claro que e o agente virtual do Paulo da Ecoprint.
  - Exemplo base: "Ola! Eu sou o assistente virtual do Paulo, da Ecoprint."
- Caso 1: Se a saudacao for a UNICA intencao detectada:
  - Se for primeira interacao: apresente-se e pergunte em que pode ajudar.
  - Se nao for primeira interacao: apenas cumprimente e pergunte em que pode ajudar.
  - Exemplos:
    - Primeira interacao: "Ola! Eu sou o assistente virtual do Paulo, da Ecoprint. Como posso ajudar voce hoje?"
    - Ja em andamento: "Ola! Como posso ajudar voce hoje?"
- Caso 2: Se houver OUTRAS intencoes junto com a saudacao (ex: orcamento, duvida):
  - NAO pergunte "Como posso ajudar?".
  - Se for primeira interacao: faca a apresentacao curta e, em seguida, prossiga imediatamente para a coleta/resposta da outra intencao.
  - Se nao for primeira interacao: prossiga imediatamente para a coleta/resposta da outra intencao.
  - Exemplo (primeira interacao + outra intencao): "Ola! Eu sou o assistente virtual do Paulo, da Ecoprint. Para eu te ajudar com isso, me diga..."
