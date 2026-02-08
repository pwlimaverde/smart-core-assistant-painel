# Intent: Flexo (Rotulos e Etiquetas Autoadesivas) - Ecoprint

## Tag
`ecoprint.flexo.rotulos_etiquetas_autoadesivas`

## Grupo
`ecoprint_flexo`

## Descricao (para embedding)
Atendimento de rotulos e etiquetas autoadesivas em bobina (flexografia). Abrange definicao de substrato (papel couche autoadesivo, BOPP branco), tipo de adesivo (permanente, removivel, alta aderencia), ambiente de uso (umidade, gelo, freezer, oleo, limpeza), e requisitos de bobina para aplicacao manual ou automatica (tubete, diametro do rolo, sentido de enrolamento, gap/passo, face-in/face-out). Considera cor em CMYK ou Pantone quando ha cor critica de marca, e arquivos com die line/contorno de corte, area de seguranca e sangria.

## Exemplo (queries que representam a intent)
- "Quero rotulos em BOPP para produto que vai na geladeira"
- "Preciso de etiquetas em rolo para aplicadora, qual tubete?"
- "Etiqueta removivel para promocao em vidro"
- "Rotulo com cor Pantone da marca, voces fazem?"
- "Orcamento de etiquetas 5x3 cm em bobina"

## Comportamento (respostas/acoes do assistente)
Objetivo: auxiliar o atendimento do Paulo (vendas) coletando informacoes preliminares para orcamento e repassando ao Paulo.

Regras:
- NUNCA informe precos. Foque em coletar especificacao para orcamento.
- Se houver aplicadora/maquina, priorize coletar parametros do rolo.

Coleta minima:
- Medida (L x A) e formato (retangular/redondo/especial).
- Quantidade (unidades, rolos ou metragem).
- Material (papel couche autoadesivo, BOPP branco, etc).
- Adesivo (permanente, removivel, alta aderencia).
- Ambiente de uso (agua/gelo/freezer/oleo/quimicos) e superficie (vidro/plastico/metal/papelao).
- Aplicacao manual ou por maquina. Se maquina:
  - tubete/core (ex: 3" / 76 mm ou 1.5"),
  - diametro maximo do rolo,
  - sentido de enrolamento/orientacao e face-in/face-out,
  - gap/passo.
- Cor (CMYK ou Pantone) e se existe cor critica.
- Arquivo: PDF fechado (CMYK/Pantone), com contorno de corte/die line e sangria.

Encerramento:
- Confirmar o resumo tecnico e informar que o Paulo/setor comercial retornara com o orcamento.
