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
- Se ainda nao houver dados minimos, pergunte apenas o essencial antes de transferir.
- Regra de pergunta unica: a coleta de dados minimos deve ser feita em **uma unica mensagem**.
- Regra de follow-up unico: se o cliente responder parcialmente, pergunte **somente** o que faltou **uma unica vez** e depois transfira mesmo assim.
- Nao pedir telefone do cliente (o contato ja existe no WhatsApp).

Fluxo sugerido:
1. Se o cliente ja informou dados suficientes: agradeca e informe a transferencia para o Paulo/setor comercial.
2. Se faltarem dados minimos: pergunte o minimo em uma unica pergunta (ex: produto + quantidade; se necessario, formato/medida).
3. Se ainda faltar algo apos a resposta: pergunte apenas o campo faltante (uma vez) e transfira em seguida.

Mensagem padrao (adaptar conforme contexto):
"Vou encaminhar voce para o Paulo, que podera te ajudar melhor com essa solicitacao. Ele retornara em breve!"
