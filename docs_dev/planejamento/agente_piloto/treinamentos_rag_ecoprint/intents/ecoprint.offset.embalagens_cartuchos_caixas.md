# Intent: Offset (Embalagens em Cartao: Cartuchos e Caixas) - Ecoprint

## Tag
`ecoprint.offset.embalagens_cartuchos_caixas`

## Grupo
`ecoprint_offset`

## Descricao (para embedding)
Atendimento de embalagens em cartao (cartuchos/caixas dobraveis) em offset industrial, que exigem faca (die cut) e gabarito (die line) com cortes/vincos, reserva de cola, e consideracoes de montagem/tolerancia. Envolve materiais (duplex/triplex, kraft, microondulado), acabamentos (laminacao, verniz total/local, hot stamping, relevo, janela) e requisitos de arquivo (CMYK/Pantone, 300 DPI, sangria; gabarito em camada separada; afastar textos de dobras/cola; area limpa para codigo de barras).

## Exemplo (queries que representam a intent)
- "Preciso de caixa/cartucho com faca e vinco"
- "Tenho a faca pronta (dieline), voces imprimem e montam?"
- "Quero embalagem kraft com verniz localizado"
- "Caixa com janela para ver o produto, da pra fazer?"
- "Orcamento de cartucho com hot stamping"

## Comportamento (respostas/acoes do assistente)
Objetivo: auxiliar o atendimento do Paulo (vendas) coletando informacoes preliminares para orcamento e repassando ao Paulo.

Regras:
- NUNCA informe precos.
- Sempre validar se existe gabarito/faca pronta; se nao, coletar info para desenvolvimento.

Coleta minima:
- Tipo (cartucho, caixa, luva, berco interno).
- Dimensoes (C x L x A) e se sao internas/externas.
- Produto a ser embalado (peso/fragilidade/uso).
- Tiragem.
- Material (tipo de cartao/papel e gramatura/espessura).
- Faca/gabarito: existe pronto ou precisa criar?
- Acabamentos (laminacao, verniz local/total, hot stamping, relevo, janela).
- Itens obrigatorios (codigo de barras, lote, validade, composicao).
- Arquivo (PDF) + gabarito em camada separada (quando houver).

Encerramento:
- Resumir e informar retorno do Paulo/setor comercial.
