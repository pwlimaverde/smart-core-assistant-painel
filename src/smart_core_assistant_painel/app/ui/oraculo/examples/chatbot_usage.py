"""
Exemplo de uso dos modelos de chatbot para atendimento ao cliente
"""
from smart_core_assistant_painel.app.ui.oraculo.models import (
    Atendimento,
    Cliente,
    FluxoConversa,
    Mensagem,
    StatusAtendimento,
    TipoMensagem,
    buscar_atendimento_ativo,
    inicializar_atendimento_whatsapp,
    processar_mensagem_whatsapp,
)


def exemplo_primeiro_contato():
    """
    Exemplo de como processar o primeiro contato de um cliente via WhatsApp
    """
    print("=== EXEMPLO: PRIMEIRO CONTATO ===")

    # Simula primeira mensagem recebida do WhatsApp
    numero_telefone = "+5511999999999"
    primeira_mensagem = "Olá! Preciso de ajuda com meu pedido."

    # Inicializa cliente e atendimento
    cliente, atendimento = inicializar_atendimento_whatsapp(
        numero_telefone=numero_telefone,
        primeira_mensagem=primeira_mensagem,
        nome_cliente="João Silva"  # Opcional, se conhecido
    )

    print(f"Cliente: {cliente}")
    print(f"Atendimento: {atendimento}")
    print(f"Status: {atendimento.get_status_display()}")

    # Busca mensagens do atendimento
    mensagens = atendimento.mensagens.all()
    print(f"Mensagens no atendimento: {mensagens.count()}")

    return cliente, atendimento


def exemplo_conversa_continuada():
    """
    Exemplo de como continuar uma conversa existente
    """
    print("\n=== EXEMPLO: CONVERSA CONTINUADA ===")

    numero_telefone = "+5511999999999"

    # Busca atendimento ativo
    atendimento = buscar_atendimento_ativo(numero_telefone)

    if atendimento:
        print(f"Atendimento ativo encontrado: {atendimento}")

        # Processa nova mensagem
        nova_mensagem = processar_mensagem_whatsapp(
            numero_telefone=numero_telefone,
            conteudo="Meu pedido é o número 12345",
            tipo_mensagem=TipoMensagem.TEXTO
        )

        print(f"Nova mensagem: {nova_mensagem}")

        # Atualiza contexto da conversa
        atendimento.atualizar_contexto('numero_pedido', '12345')
        atendimento.atualizar_contexto(
            'etapa_conversa', 'identificacao_pedido')

        # Simula resposta do bot
        resposta_bot = "Encontrei seu pedido #12345. Como posso ajudá-lo?"

        # Registra resposta do bot
        mensagem_bot = Mensagem.objects.create(
            atendimento=atendimento,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            conteudo=resposta_bot,
            is_from_client=False,
            metadados={'gerada_por': 'chatbot_ia'}
        )

        print(f"Resposta do bot: {mensagem_bot}")

        return atendimento
    else:
        print("Nenhum atendimento ativo encontrado")
        return None


def exemplo_transferencia_humano():
    """
    Exemplo de como transferir para atendente humano
    """
    print("\n=== EXEMPLO: TRANSFERÊNCIA PARA HUMANO ===")

    numero_telefone = "+5511999999999"
    atendimento = buscar_atendimento_ativo(numero_telefone)

    if atendimento:
        # Cliente solicita atendente humano
        processar_mensagem_whatsapp(
            numero_telefone=numero_telefone,
            conteudo="Quero falar com um atendente humano",
            tipo_mensagem=TipoMensagem.TEXTO
        )

        # Atualiza status para transferido
        atendimento.status = StatusAtendimento.TRANSFERIDO
        atendimento.atendente_humano = "Maria Santos"
        atendimento.adicionar_historico_status(
            StatusAtendimento.TRANSFERIDO,
            "Transferido para atendente humano a pedido do cliente"
        )
        atendimento.save()

        print(f"Atendimento transferido para: {atendimento.atendente_humano}")

        # Mensagem automática informando transferência
        mensagem_sistema = Mensagem.objects.create(
            atendimento=atendimento,
            tipo=TipoMensagem.SISTEMA,
            conteudo="Você foi transferido para um atendente humano. Aguarde um momento.",
            is_from_client=False,
            metadados={
                'tipo_sistema': 'transferencia'})

        print(f"Mensagem do sistema: {mensagem_sistema}")


def exemplo_finalizacao_atendimento():
    """
    Exemplo de como finalizar um atendimento
    """
    print("\n=== EXEMPLO: FINALIZAÇÃO DO ATENDIMENTO ===")

    numero_telefone = "+5511999999999"
    atendimento = buscar_atendimento_ativo(numero_telefone)

    if atendimento:
        # Cliente indica que o problema foi resolvido
        processar_mensagem_whatsapp(
            numero_telefone=numero_telefone,
            conteudo="Obrigado! Problema resolvido.",
            tipo_mensagem=TipoMensagem.TEXTO
        )

        # Solicita avaliação
        mensagem_avaliacao = Mensagem.objects.create(
            atendimento=atendimento,
            tipo=TipoMensagem.SISTEMA,
            conteudo="Que bom que conseguimos resolver! Por favor, avalie nosso atendimento de 1 a 5.",
            is_from_client=False,
            metadados={
                'tipo_sistema': 'solicitacao_avaliacao'})

        # Simula avaliação do cliente
        processar_mensagem_whatsapp(
            numero_telefone=numero_telefone,
            conteudo="5",
            tipo_mensagem=TipoMensagem.TEXTO
        )

        # Registra avaliação e finaliza
        atendimento.avaliacao = 5
        atendimento.feedback = "Atendimento excelente!"
        atendimento.finalizar_atendimento(StatusAtendimento.RESOLVIDO)

        print(f"Atendimento finalizado com avaliação: {atendimento.avaliacao}")
        print(f"Data de finalização: {atendimento.data_fim}")


def exemplo_estatisticas():
    """
    Exemplo de como gerar estatísticas do atendimento
    """
    print("\n=== EXEMPLO: ESTATÍSTICAS ===")

    # Estatísticas gerais
    total_clientes = Cliente.objects.count()
    total_atendimentos = Atendimento.objects.count()
    atendimentos_resolvidos = Atendimento.objects.filter(
        status=StatusAtendimento.RESOLVIDO
    ).count()

    print(f"Total de clientes: {total_clientes}")
    print(f"Total de atendimentos: {total_atendimentos}")
    print(f"Atendimentos resolvidos: {atendimentos_resolvidos}")

    # Avaliações médias
    from django.db.models import Avg
    avaliacao_media = Atendimento.objects.filter(
        avaliacao__isnull=False
    ).aggregate(Avg('avaliacao'))['avaliacao__avg']

    if avaliacao_media:
        print(f"Avaliação média: {avaliacao_media:.2f}")

    # Atendimentos por status
    from django.db.models import Count
    status_counts = Atendimento.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')

    print("\nAtendimentos por status:")
    for item in status_counts:
        status_display = StatusAtendimento(item['status']).label
        print(f"  {status_display}: {item['count']}")


def exemplo_fluxo_conversa():
    """
    Exemplo de como criar um fluxo de conversa estruturado
    """
    print("\n=== EXEMPLO: FLUXO DE CONVERSA ===")

    # Cria um fluxo para dúvidas sobre pedidos
    fluxo_pedidos = FluxoConversa.objects.create(
        nome="Dúvidas sobre Pedidos",
        descricao="Fluxo para resolver dúvidas sobre pedidos de clientes",
        condicoes_entrada={
            "palavras_chave": ["pedido", "compra", "ordem", "status"],
            "intent": "consulta_pedido"
        },
        estados={
            "inicio": {
                "mensagem": "Vou te ajudar com seu pedido! Qual é o número do seu pedido?",
                "proximo_estado": "coletando_numero_pedido"
            },
            "coletando_numero_pedido": {
                "validacao": "numero_pedido",
                "mensagem_erro": "Por favor, informe um número de pedido válido.",
                "proximo_estado": "consultando_pedido"
            },
            "consultando_pedido": {
                "acao": "consultar_sistema_pedidos",
                "proximo_estado": "informando_status"
            },
            "informando_status": {
                "mensagem": "Encontrei seu pedido! Status: {status_pedido}",
                "opcoes": ["Mais informações", "Alterar pedido", "Cancelar pedido"],
                "proximo_estado": "aguardando_escolha"
            }
        }
    )

    print(f"Fluxo criado: {fluxo_pedidos}")

    # Exemplo de uso do fluxo
    numero_telefone = "+5511888888888"
    cliente, atendimento = inicializar_atendimento_whatsapp(
        numero_telefone=numero_telefone,
        primeira_mensagem="Preciso saber o status do meu pedido"
    )

    # Atualiza contexto com o fluxo atual
    atendimento.atualizar_contexto('fluxo_atual', 'Dúvidas sobre Pedidos')
    atendimento.atualizar_contexto('estado_atual', 'inicio')

    print(f"Cliente {cliente.telefone} entrou no fluxo: {fluxo_pedidos.nome}")


if __name__ == "__main__":
    # Executa todos os exemplos
    exemplo_primeiro_contato()
    exemplo_conversa_continuada()
    exemplo_transferencia_humano()
    exemplo_finalizacao_atendimento()
    exemplo_estatisticas()
    exemplo_fluxo_conversa()
