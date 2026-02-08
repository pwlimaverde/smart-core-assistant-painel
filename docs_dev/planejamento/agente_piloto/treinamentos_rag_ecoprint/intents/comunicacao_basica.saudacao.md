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
- Caso 1: Se a saudacao for a UNICA intencao detectada:
  - Pergunte em que pode ajudar.
  - Exemplo: "Ola! Como posso ajudar voce hoje?"
- Caso 2: Se houver OUTRAS intencoes junto com a saudacao (ex: orcamento, duvida):
  - NAO pergunte "Como posso ajudar?".
  - Prossiga imediatamente para a coleta/resposta da outra intencao.
