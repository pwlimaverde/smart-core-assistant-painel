# Intent: Digital - Ecoprint

## Tag
`ecoprint.digital`

## Grupo
`ecoprint_digital`

## Descricao (para embedding)
Intencao para atendimento de impressao digital em papel (grafica rapida/pequena tiragem) na Ecoprint: vouchers/vales, apostilas, catalogos/livretos, panfletos e cartazes em pequena tiragem, com formato maximo 66x33 cm (330x660 mm), papel ate 300g, e acabamentos simples (sem corte especial/faca). Inclui opcoes como laminacao BOPP brilho/fosca, dobra (com vinco se necessario) e furacao. Arquivo preferencial: PDF em CMYK, com sangria e margem de seguranca.

## Exemplo (queries que representam a intent)
- "Quero imprimir 500 panfletos A5 4x4 com laminacao fosca"
- "Voces imprimem voucher numerado em pequena tiragem?"
- "Preciso de 30 apostilas com capa mais grossa e furacao"
- "Da pra imprimir catalogo pequeno com dobra?"
- "Quero panfletos poucos, tamanho A5, em papel mais firme"

## Comportamento (respostas/acoes do assistente)
Objetivo: auxiliar o atendimento do Paulo (vendas) coletando informacoes preliminares para orcamento e repassando ao Paulo.

1. Confirmar se o pedido entra no escopo do Digital: material em papel, ate 300g, tamanho ate 66x33 cm, sem corte especial/faca (apenas cortes retos; dobra/furacao ok).
2. Coletar os dados do pedido (perguntar apenas o que faltar) usando **pergunta unica** (nao virar interrogatorio):
- Produto (voucher/vale/apostila/catalogo/livreto/panfleto/cartaz)
- Formato final (L x A) e se tem dobra (qual)
- Quantidade (e variacoes de arte, se houver)
- Cor (4x0 ou 4x4), se aplicavel
- Papel/gramatura (ate 300g), se for relevante para o orcamento
- Acabamentos (BOPP brilho/fosca, dobra com/sem vinco, furacao), se houver
- Logistica: retirada ou entrega (se entrega: cidade e bairro)
- Nao pedir telefone do cliente (o contato ja existe no WhatsApp)
3. Se estiver fora do limite (maior que 66x33, acima de 300g, ou exigir faca/corte especial), explicar de forma objetiva e oferecer alternativa:
- Ajustar formato/gramatura/acabamento para caber no Digital, ou
- Direcionar para Offset/outro fluxo quando for tiragem alta, houver necessidade de acabamento industrial ou corte especial.
4. Orientar padrao de arquivo para evitar retrabalho:
- Cor: CMYK
- Imagens: 300 DPI no tamanho final (para materiais vistos de perto)
- Sangria: 3 mm quando houver fundo ate a borda
- Margem de seguranca: 3 mm a 5 mm para textos/logos
- PDF fechado, com fontes incorporadas ou convertidas em curvas
Para QR code/codigo de barras: bom contraste, tamanho adequado, longe de bordas e dobras; evitar BOPP muito refletivo se a leitura for critica.
5. Encerrar com resumo do que foi entendido e lista do que falta para orcar/produzir (ex: confirmar X, Y e enviar o PDF).

Encerramento (importante):
- Evite resumo longo repetindo todos os dados.
- Se ja houver o minimo para encaminhar, transfira e deixe o Paulo confirmar detalhes finos.
