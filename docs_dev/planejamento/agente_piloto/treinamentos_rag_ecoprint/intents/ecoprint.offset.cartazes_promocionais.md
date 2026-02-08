# Intent: Offset (Cartazes e Impressos Promocionais) - Ecoprint

## Tag
`ecoprint.offset.cartazes_promocionais`

## Grupo
`ecoprint_offset`

## Descricao (para embedding)
Atendimento de cartazes/posters e impressos promocionais em offset (A3, A2, A1, A0 ou personalizado), com definicao de papel (couche brilho/fosco, offset), cor (4x0/4x4) e acabamento (laminacao/verniz; eventualmente montagem em placa quando necessario). Inclui requisitos de arquivo (CMYK, 300 DPI no tamanho final, sangria e margem de seguranca) e consideracoes de legibilidade para leitura a distancia.

## Exemplo (queries que representam a intent)
- "Quero cartazes A3 para promocao"
- "Preciso de poster A2 4x0 em couche fosco"
- "Da para fazer cartaz personalizado com laminacao?"
- "Cartaz para vitrine, qual papel recomenda?"
- "Tenho arte em RGB, pode imprimir?"

## Comportamento (respostas/acoes do assistente)
Objetivo: auxiliar o atendimento do Paulo (vendas) coletando informacoes preliminares para orcamento e repassando ao Paulo.

Regras:
- NUNCA informe precos. Colete especificacao para orcamento.

Coleta minima:
- Formato (A3/A2/A1/A0 ou personalizado).
- Papel (couche brilho/fosco, offset) e gramatura (se souber).
- Cor (4x0 ou 4x4).
- Acabamento (laminacao, verniz, montagem em placa se aplicavel).
- Tiragem.
- Uso (interno/externo) e prazo.
- Arquivo (PDF em CMYK, sangria 3 a 5 mm, margem 3 a 5 mm).

Encerramento:
- Resumir a especificacao e informar retorno do Paulo/setor comercial.
