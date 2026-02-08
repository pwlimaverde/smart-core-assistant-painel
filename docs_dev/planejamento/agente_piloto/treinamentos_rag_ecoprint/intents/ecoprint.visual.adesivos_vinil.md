# Intent: Visual (Adesivos em Vinil: Impresso, Recorte, Perfurado) - Ecoprint

## Tag
`ecoprint.visual.adesivos_vinil`

## Grupo
`ecoprint_visual`

## Descricao (para embedding)
Atendimento de adesivos vinil para comunicacao visual: vinil impresso (arte impressa), vinil recorte (letras/formas sem fundo) e vinil perfurado/one-way vision (vidros). Inclui orientacao sobre superficie de aplicacao (vidro/parede/metal/plastico), ambiente (interno/externo), necessidade de laminacao, emendas em pecas grandes, e selecao de material (cast vs calendered) quando houver curvas/relevos e necessidade de durabilidade.

## Exemplo (queries que representam a intent)
- "Quero adesivo para vitrine com promocao"
- "Preciso de vinil recorte com logo e horario"
- "Adesivo perfurado para vidro de loja (one-way vision)"
- "Vai aplicar em parede, precisa laminacao?"
- "Tem curva/relevo, qual vinil usar?"

## Comportamento (respostas/acoes do assistente)
Objetivo: auxiliar o atendimento do Paulo (vendas) coletando informacoes preliminares para orcamento e repassando ao Paulo.

Regras:
- NUNCA informe precos. Colete dados e oriente tecnicamente.

Coleta minima:
- Tipo (impresso, recorte, perfurado).
- Medidas (L x A) e quantidade.
- Onde vai aplicar (vidro/parede/metal/plastico) e se e interno/externo.
- Tempo de uso (temporario vs longo) e exposicao (sol/chuva/limpeza).
- Precisa laminacao? (externo/toque/limpeza geralmente pede).
- Existe curva/relevo? (pode exigir cast).
- Arte: possui arquivo? (preferir PDF/vetores para textos/logos).

Encerramento:
- Resumo + retorno do Paulo/setor comercial.
