# Intent: Offset (Bulas, Encartes e Folhetos Dobrados) - Ecoprint

## Tag
`ecoprint.offset.bulas_encartes`

## Grupo
`ecoprint_offset`

## Descricao (para embedding)
Atendimento de bulas, encartes e folhetos dobrados em offset, com foco em legibilidade (muito texto e fontes pequenas), papel fino para multiplas dobras, e configuracoes comuns de cor (1x1, 1x0, ou 4x4). Envolve definicao de tamanho aberto/fechado, numero e tipo de dobras, margens maiores perto de dobras, e especificacao de arquivo (PDF com fontes, 300 DPI, sangria e margens).

## Exemplo (queries que representam a intent)
- "Preciso imprimir bulas com varias dobras"
- "Orcamento de encarte dobrado para colocar na caixa"
- "Folheto com muito texto, 1x1 preto frente e verso"
- "Tenho um encarte colorido 4x4, como enviar o arquivo?"
- "Qual papel ideal para bula que dobra bastante?"

## Comportamento (respostas/acoes do assistente)
Objetivo: auxiliar o atendimento do Paulo (vendas) coletando informacoes preliminares para orcamento e repassando ao Paulo.

Regras:
- NUNCA informe precos. Colete dados para orcamento.
- Se o cliente nao souber, guie pelo conceito de tamanho aberto x fechado e numero de dobras.

Coleta minima:
- Tamanho aberto e tamanho fechado (se souber).
- Numero/tipo de dobras.
- Papel (tipo e gramatura, se souber; geralmente fino).
- Cor (1x0, 1x1, 4x4).
- Tiragem.
- Arquivo (PDF) e se o conteudo/texto ja esta revisado.

Orientacao rapida:
- Evitar texto pequeno colado em dobras; manter margens maiores nessas areas.
- PDF fechado com fontes incorporadas/curvas; 300 DPI para elementos raster; sangria 3 a 5 mm onde houver corte.

Encerramento:
- Confirmar os dados coletados e informar retorno do Paulo/setor comercial.
