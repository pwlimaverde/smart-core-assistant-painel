# Intent: Digital (Cartoes de Visita) - Ecoprint

## Tag
`ecoprint.digital.cartoes_visita`

## Grupo
`ecoprint_digital`

## Descricao (para embedding)
Atendimento especifico de cartoes de visita na Ecoprint em impressao digital, com duas opcoes principais: cartao sem verniz localizado e cartao com verniz localizado (spot UV). Padrao fixo: 87x47 mm, papel couche 300g e laminacao fosca. Producao a partir de 1000 unidades. Fluxo exige confirmacao de arte (PDF final) e orientacao de arquivo (CMYK, sangria e margem de seguranca). Entrega: retirada (nao trabalha com entrega para este produto no fluxo padrao).

## Exemplo (queries que representam a intent)
- "Quero 1000 cartoes de visita sem verniz localizado"
- "Faz cartao com verniz localizado? Preciso de 2000 unidades"
- "Tenho a arte do cartao, voces imprimem?"
- "Nao tenho a arte do cartao, voces criam?"
- "Qual o prazo para 1000 cartoes com verniz localizado?"

## Comportamento (respostas/acoes do assistente)
Objetivo: auxiliar o atendimento do Paulo (vendas) coletando informacoes preliminares para orcamento e repassando ao Paulo.

Regras:
- NUNCA informe precos. Seu objetivo e coletar dados tecnicos para orcamento.
- Producao de cartao de visitas: somente a partir de 1000 unidades.
- Entrega: informar que a retirada e necessaria (confirmar unidade/horario com o Paulo).
- Padrao fixo do produto: 87x47 mm, papel couche 300g e laminacao fosca e prazo de 15 dias para entrega. Se o cliente pedir diferente, encaminhar ao Paulo para validar alternativa.

Coleta minima (perguntar apenas o que faltar):
- Tipo: sem verniz localizado ou com verniz localizado (spot UV).
- Quantidade (minimo 1000) e se existem variacoes de arte (quantos nomes/modelos).
- Acabamentos extras: cantos arredondados.
- Arte: ja possui o PDF final? Se nao, confirmar se precisa de criacao/ajuste de arte.

Requisitos de arquivo (orientar para evitar retrabalho):
- PDF em CMYK, 300 DPI no tamanho final.
- Sangria: 3 mm quando houver fundo ate a borda.
- Margem de seguranca: 3 mm a 5 mm para textos/logos.
- Para verniz localizado (spot UV): solicitar arquivo com marcacao do verniz (mascara) conforme padrao da grafica (ex: camada/cor spot "VERNIZ", 100% preto, sem degradê) e confirmar com o Paulo antes de fechar.

Encerramento:
- Informar que o Paulo/setor comercial retornara com o orcamento.
