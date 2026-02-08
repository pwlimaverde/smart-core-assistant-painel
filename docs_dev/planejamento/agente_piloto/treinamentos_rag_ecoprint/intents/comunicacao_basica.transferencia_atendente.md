# Intent: Transferencia Para Atendente (Humano)

## Tag
`transferencia_atendente`

## Grupo
`comunicacao_basica`

## Descricao (para embedding)
Intencao de transferir a conversa do assistente virtual para um atendente humano (comercial), normalmente apos coleta minima de dados ou quando o cliente solicita falar com alguem.

## Exemplo (queries que representam a intent)
- "Quero falar com um atendente."
- "Pode me passar para o comercial?"
- "Preciso falar com o Paulo."
- "Tem alguem ai pra me atender?"
- "Quero fechar com voce, me chama um vendedor."

## Comportamento (respostas/acoes do assistente)
Objetivo: encaminhar o cliente para o Paulo (comercial) de forma cordial.

Regras:
- Seja direto e cordial.
- Nao prometa prazos que nao foram informados.
- Se ainda nao houver dados minimos (produto e quantidade), pergunte apenas o essencial antes de transferir.

Fluxo sugerido:
1. Se o cliente ja informou dados suficientes: agradeca e informe a transferencia para o Paulo/setor comercial.
2. Se faltarem dados minimos: pergunte apenas produto e quantidade, aguarde resposta e transfira.

Mensagem padrao (adaptar conforme contexto):
"Vou encaminhar voce para o Paulo, que podera te ajudar melhor com essa solicitacao. Ele retornara em breve!"
