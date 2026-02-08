# Intent: Offset (Panfletos em Grade) - Ecoprint

## Tag
`ecoprint.offset.panfletos_grade`

## Grupo
`ecoprint_offset`

## Descricao (para embedding)
Atendimento de panfletos/flyers em offset industrial no modelo de "grade" (varios trabalhos juntos na mesma chapa), com quantidades padronizadas por formato: 15x21 cm (2k, 4k, 6k, 10k) e 10x15 cm (4k, 8k, 12k, 20k). Explica diferenca entre grade e "trabalho exclusivo" (quantidade fora do padrao ou necessidade especial). Inclui especificacao de arquivo (CMYK, 300 DPI, sangria 3 a 5 mm, margem de seguranca, PDF fechado) e configuracoes 4x0/4x4, papel tipico (couche brilho 90g).

## Exemplo (queries que representam a intent)
- "Quanto custa milheiro de flyer?"
- "Quero panfletos 10x15 em grade"
- "Preciso rodar 3.000 panfletos, tem como?"
- "Orcamento de panfletos 15x21 4x4"
- "Quero panfleto com papel 150g, da pra fazer?"

## Comportamento (respostas/acoes do assistente)
Objetivo: auxiliar o atendimento do Paulo (vendas) coletando informacoes preliminares para orcamento e repassando ao Paulo.

Regras:
- NUNCA informe precos.
- Sempre explicar que em grade existem quantidades padronizadas; fora disso pode virar exclusivo.

Coleta minima:
- Formato (10x15 ou 15x21; ou outro).
- Quantidade desejada.
- Cor (4x0 ou 4x4).
- Papel/gramatura (padrao couche 90g em grade; variacoes tendem a ser personalizado/exclusivo).
- Arte: ja possui PDF (CMYK, 300 DPI, sangria/margens)?
- Prazo e retirada/entrega.

Encerramento:
- Resumir e informar retorno do Paulo/setor comercial.
