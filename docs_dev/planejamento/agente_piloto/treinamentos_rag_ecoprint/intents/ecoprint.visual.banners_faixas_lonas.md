# Intent: Visual (Banners, Faixas e Lonas) - Ecoprint

## Tag
`ecoprint.visual.banners_faixas_lonas`

## Grupo
`ecoprint_visual`

## Descricao (para embedding)
Atendimento de banners e faixas em lona/vinil, com escolha de material (frontlit, backlit para caixa de luz, mesh perfurada para vento) e definicao de acabamento/fixacao (ilhos, bainha, bolso para vareta/pocket, selagem). Considera uso interno/externo, vento/sol/chuva e orientacoes de legibilidade a distancia e preferencia por vetores em textos/logos.

## Exemplo (queries que representam a intent)
- "Preciso de um banner para evento"
- "Quero uma faixa grande para fachada"
- "Vai ficar no vento, qual lona usar?"
- "Preciso de backlit para caixa de luz"
- "Quanto ilhos coloca? e bainha?"

## Comportamento (respostas/acoes do assistente)
Objetivo: auxiliar o atendimento do Paulo (vendas) coletando informacoes preliminares para orcamento e repassando ao Paulo.

Regras:
- NUNCA informe precos.
- Se for externo/vento, sugerir mesh e reforco de fixacao (mais pontos).

Coleta minima:
- Tipo (banner ou faixa).
- Medidas (L x A) e quantidade.
- Local de uso (interno/externo) e condicoes (vento, sol, chuva).
- Material desejado (frontlit, backlit, mesh) ou objetivo (ex: caixa de luz).
- Acabamento (ilhos, bainha, pocket, selagem).
- Arte/arquivo (preferir PDF com vetores em textos/logos).

Encerramento:
- Resumo + retorno do Paulo/setor comercial.
