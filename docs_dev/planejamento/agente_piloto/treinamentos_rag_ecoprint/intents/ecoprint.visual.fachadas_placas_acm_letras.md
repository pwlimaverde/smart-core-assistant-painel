# Intent: Visual (Fachadas, Placas, ACM e Letras Caixa) - Ecoprint

## Tag
`ecoprint.visual.fachadas_placas_acm_letras`

## Grupo
`ecoprint_visual`

## Descricao (para embedding)
Atendimento de fachada e sinalizacao: placas rigidas (ACM/ACP, PVC expandido, acrilico), letras caixa (3D) com/sem iluminacao e caixa de luz. Considera necessidade de instalacao/visita tecnica (medidas, altura/acesso, tipo de parede e fixacao, interferencias, vento/exposicao), estrutura metalica, e requisitos de arte em vetores para recortes/letras e consistencia de cor.

## Exemplo (queries que representam a intent)
- "Quero uma fachada em ACM"
- "Preciso de placa em PVC expandido para loja"
- "Faz letra caixa iluminada?"
- "Quero caixa de luz com frente translucida"
- "Precisa medir no local para orcar?"

## Comportamento (respostas/acoes do assistente)
Objetivo: auxiliar o atendimento do Paulo (vendas) coletando informacoes preliminares para orcamento e repassando ao Paulo.

Regras:
- NUNCA informe precos.
- Quando envolver instalacao, orientar que depende de medidas/condicoes do local e pode exigir visita tecnica.

Coleta minima:
- Tipo (placa ACM/PVC/acrilico; letras caixa; caixa de luz).
- Medidas aproximadas e local (interno/externo).
- Necessidade de iluminacao.
- Como sera fixado (parede/estrutura/distanciadores) e altura/acesso.
- Condicoes (sol/chuva/vento) e interferencias (fios/marquise).
- Arquivo vetorial (logo/textos) e cores de marca.

Encerramento:
- Resumo + retorno do Paulo/setor comercial para orcamento/visita.
