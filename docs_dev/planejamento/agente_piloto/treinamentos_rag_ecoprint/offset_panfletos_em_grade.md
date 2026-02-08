# Guia Tecnico de Producao: Panfletos (Offset em Grade)

Palavras-chave: panfleto, flyer, grade, offset industrial, 10x15, 15x21, A5, 1/4 de oficio, tiragem, 4x0, 4x4, couche 90g, sangria, 300 DPI, CMYK.

## 1) O que e um panfleto e para que serve

Panfleto (ou flyer) e um impresso de marketing direto, normalmente em papel fino, feito para distribuicao em massa (rua, balcão, encartes em sacolas). Seu objetivo e comunicar uma oferta, evento ou informacao institucional de forma rapida, com texto de facil leitura e chamadas fortes (preco, data, endereco, WhatsApp).

Em producao industrial, panfletos costumam ser feitos em offset por entregar:
- alto volume com custo por unidade competitivo;
- boa definicao de texto e imagens;
- estabilidade de cor no lote (comparado a processos de pequena tiragem).

## 2) Sistema de "Grade" (conceito, por que existe e consequencias)

### O que e "grade"

Grade e um modelo de producao em que varios trabalhos de clientes diferentes sao impressos juntos na mesma chapa (matriz) e na mesma folha de papel grande. Depois, cada trabalho e cortado para virar o tamanho final.

### Por que existe

Offset tem custos fixos relevantes (chapa, acerto/registro, lavagens, setup). Ao juntar varios trabalhos na mesma rodada, esses custos se dividem, reduzindo o custo unitario para cada cliente.

### Consequencias praticas

1. Quantidades padronizadas
- Para encaixar matematicamente na folha, as quantidades tendem a ser fixas por formato.

2. Menor liberdade de personalizacao
- Papel e acabamento costumam ser padronizados. Variacoes (outro papel/gramatura, formato fora do padrao, acabamento especial) saem do modelo de grade e viram "trabalho exclusivo".

## 3) Quantidades e formatos (modelo de grade do treinamento)

### Grade 15x21 cm (A5)

- 2.000 unidades
- 4.000 unidades
- 6.000 unidades
- 10.000 unidades

### Grade 10x15 cm (1/4 de oficio)

- 4.000 unidades
- 8.000 unidades
- 12.000 unidades
- 20.000 unidades

### Excecao: "trabalho exclusivo" (orçamento personalizado)

Quando a quantidade solicitada nao corresponde ao padrao (ex: 1.500, 3.000) ou quando o volume e muito fora do modelo, o panfleto pode sair da grade e ser produzido como trabalho exclusivo (chapa e acerto dedicados).

Efeitos comuns de "exclusivo":
- custo unitario tende a ser maior do que na grade para quantidades proximas;
- mais opcoes de papel/gramatura e acabamentos;
- prazo e especificacao variam conforme complexidade.

## 4) Especificacoes tecnicas (pre-impressao) para panfletos offset

Estas especificacoes existem para evitar problemas classicos: cores apagadas, bordas brancas, textos cortados e imagens pixeladas.

### 4.1 Cor: CMYK (nao RGB)

- CMYK (Ciano, Magenta, Yellow, Black) e o padrao de impressao.
- RGB e o padrao de tela (celular/monitor). Converter RGB para CMYK pode mudar cores (principalmente tons vibrantes/neon).

Regras praticas de preto:
- Texto preto pequeno: 100% K (C0 M0 Y0 K100) para nitidez.
- Fundo preto grande: preto rico (composicao CMYK) para "preto mais profundo" (a formula exata depende do perfil; evitar somar tinta demais).

### 4.2 Resolucao: 300 DPI no tamanho final

- Imagens abaixo de 300 DPI no tamanho final tendem a ficar serrilhadas/pixeladas na impressao.
- Aumentar DPI artificialmente em software nao recria detalhe; a qualidade depende da imagem original.

### 4.3 Sangria e margem de seguranca

- Sangria (bleed): 3 mm a 5 mm alem do corte final. Evita filetes brancos se houver variacao no corte.
- Margem de seguranca: manter textos/logos 3 mm a 5 mm para dentro da borda final. Evita cortar informacao.

### 4.4 Formato de arquivo recomendado

- PDF fechado no tamanho final + sangria.
- Fontes incorporadas ou convertidas em curvas (para nao substituir fonte).
- Imagens incorporadas com qualidade (nao link quebrado).

## 5) Papel e acabamento (padrao de grade do exemplo)

Papel padrao de grade (exemplo):
- Couche brilho 90g: papel fino com brilho, comum para panfletagem de rua (boa relacao custo/volume).

Variacoes tipicas (geralmente fora da grade, via personalizado):
- Couche 115g / 150g / 170g: mais "encorpado", melhor sensacao ao toque, maior resistencia a amassar, custo maior.
- Laminacao: aumenta resistencia e acabamento, mas adiciona etapa de producao.

## 6) Configuracoes de impressao (glossario)

- 4x0: frente colorida, verso branco.
- 4x4: frente e verso coloridos.
- 1x0 / 1x1: uma cor (preto ou outra) em um lado / nos dois lados (menos comum para panfleto promocional colorido).

## 7) Prazos (referencias do modelo do treinamento)

Prazos variam conforme fila e especificacao; como referencia do modelo:
- Prazo padrao: 4 dias uteis apos aprovacao final de arte e confirmacao de pagamento.
- "Expresso" (em grade):
  - artes aprovadas ate quinta-feira 17h;
  - producao na sexta-feira;
  - entrega/retirada na sexta-feira ate 17h.

## 8) Problemas comuns (causa tecnica)

- "Borda branca apareceu": falta de sangria ou arte nao cobre ate a sangria.
- "Texto muito perto da borda": falta de margem de seguranca.
- "Foto saiu borrada": imagem com baixa resolucao no tamanho final.
- "Cor saiu diferente do celular": conversao RGB->CMYK e variacao de visualizacao em telas.

## 9) Dados tecnicos que definem a especificacao do panfleto

- Formato final (10x15 ou 15x21; ou formato fora do padrao).
- Tiragem (quantidade) e se e padrao de grade ou exclusivo.
- Cor (4x0, 4x4).
- Papel/gramatura.
- Arquivo: PDF fechado? precisa criacao/adaptacao?
- Prazo e logistica (retirada/entrega).

