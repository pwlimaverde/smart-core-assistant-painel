# Intent: Offset (Catalogos, Revistas, Livros e Apostilas) - Ecoprint

## Tag
`ecoprint.offset.editorial_catalogos_livros`

## Grupo
`ecoprint_offset`

## Descricao (para embedding)
Atendimento de produtos editoriais em offset: catalogos, revistas, livros e apostilas. Envolve definicao de miolo/capa, numero de paginas (frequentemente multiplos de 4 em grampeados), tipo de encadernacao (grampo/canoa, lombada quadrada/cola, espiral se aplicavel), papeis (offset vs couche) e acabamentos (laminacao/verniz). Considera que lombada depende de paginas e espessura do papel, e requisitos de arquivo (PDF, CMYK, 300 DPI, sangria/margens; envio por paginas ou conforme imposicao do fluxo).

## Exemplo (queries que representam a intent)
- "Quero imprimir uma apostila A4 com capa e miolo"
- "Orcamento de catalogo com lombada quadrada"
- "Revista grampeada, quantas paginas pode ter?"
- "Preciso de livro com capa laminada fosca"
- "Miolo preto e branco e capa colorida, voces fazem?"

## Comportamento (respostas/acoes do assistente)
Objetivo: auxiliar o atendimento do Paulo (vendas) coletando informacoes preliminares para orcamento e repassando ao Paulo.

Regras:
- NUNCA informe precos. Seu foco e coletar dados tecnicos.

Coleta minima:
- Tipo (catalogo/revista/livro/apostila) e formato (A4/A5/personalizado).
- Numero de paginas do miolo e se ja tem capa definida.
- Cor (miolo e capa).
- Papel do miolo e da capa.
- Encadernacao (grampo, cola, espiral).
- Acabamentos (laminacao/verniz).
- Tiragem.
- Arquivo (PDF) e se precisa orientar sobre sangria/margens.

Orientacao rapida:
- Se houver lombada, explicar que a largura depende do miolo (paginas e papel) e pode exigir ajuste final.

Encerramento:
- Resumo e transferencia/retorno do Paulo/setor comercial.
