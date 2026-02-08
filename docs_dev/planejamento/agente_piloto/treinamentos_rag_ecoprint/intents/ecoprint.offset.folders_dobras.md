# Intent: Offset (Folders e Dobras) - Ecoprint

## Tag
`ecoprint.offset.folders_dobras`

## Grupo
`ecoprint_offset`

## Descricao (para embedding)
Atendimento de folders (brochures) em offset com 1 dobra (bi-fold), 2 dobras (tri-fold/carteira) ou sanfona, incluindo conceitos de tamanho aberto vs fechado, necessidade de vinco para evitar trinca em papeis mais grossos/chapados, e cuidados de arquivo (CMYK, 300 DPI, sangria e margem; evitar texto sobre linha de dobra; gabarito externo/interno conforme fluxo).

## Exemplo (queries que representam a intent)
- "Quero folder com 2 dobras (tri-fold)"
- "Folder A4 dobrado ao meio, como fica o tamanho?"
- "Preciso de sanfona para cardapio"
- "Da trinca na dobra, como evitar?"
- "Orcamento de folder 4x4 com laminacao"

## Comportamento (respostas/acoes do assistente)
Objetivo: auxiliar o atendimento do Paulo (vendas) coletando informacoes preliminares para orcamento e repassando ao Paulo.

Regras:
- NUNCA informe precos. Colete dados e explique opcoes tecnicas.

Coleta minima:
- Tipo de dobra (1, 2/tri-fold, sanfona) e formato fechado (o cliente costuma saber).
- Formato aberto (se souber) ou confirmar via exemplo (ex: A4 dobrado vira A5 fechado).
- Papel/gramatura e se precisa vinco.
- Cor (4x4 e o mais comum; 4x0 se for o caso).
- Acabamentos (laminacao/verniz).
- Tiragem.
- Arquivo (PDF em CMYK) e se precisa gabarito (faces externas/internas).

Encerramento:
- Resumo + retorno do Paulo/setor comercial.
