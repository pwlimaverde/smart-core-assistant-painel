# Intent: Visual (Outdoor, Blueback e Midia Externa) - Ecoprint

## Tag
`ecoprint.visual.outdoor_blueback_ooh`

## Grupo
`ecoprint_visual`

## Descricao (para embedding)
Atendimento de midia externa (outdoor/OOH), com foco em papel blueback (verso azul para opacidade) e opcoes em lona conforme o ponto. Inclui instalacao por colagem (papel) e possibilidade de painelizacao/emendas, criterios de leitura a distancia (mensagem curta, alto contraste, letras grandes) e resolucao adequada para grande formato (pode ser menor que 300 DPI dependendo da distancia).

## Exemplo (queries que representam a intent)
- "Quero imprimir outdoor em blueback"
- "Meu outdoor precisa ser dividido em partes, voces fazem painelizacao?"
- "E outdoor em lona, tem como?"
- "Qual DPI usar para outdoor grande?"
- "Orcamento de outdoor para determinada cidade/ponto"

## Comportamento (respostas/acoes do assistente)
Objetivo: auxiliar o atendimento do Paulo (vendas) coletando informacoes preliminares para orcamento e repassando ao Paulo.

Regras:
- NUNCA informe precos.
- Sempre coletar cidade/ponto e tipo de midia (blueback vs lona), pois muda medida/padrao.

Coleta minima:
- Cidade e ponto (ou padrao/medida do local).
- Tipo de midia (papel blueback vs lona).
- Medida final e se precisa painelizacao/emendas.
- Periodo de veiculacao (tempo de exposicao).
- Arquivo final e se o layout esta adequado para leitura a distancia.

Encerramento:
- Resumo + retorno do Paulo/setor comercial.
