#!/usr/bin/env python3
"""
Exemplo de uso do método carregar_historico_mensagens simplificado.

Este exemplo demonstra como usar o método carregar_historico_mensagens
atualizado para obter o histórico completo de mensagens, intents e entidades.
"""

from src.smart_core_assistant_painel.app.ui.oraculo.models import (
    Atendimento,
    Mensagem,
    TipoRemetente,
)


def exemplo_carregar_historico_completo():
    """
    Exemplo de como carregar o histórico completo de um atendimento.
    """
    # Busca um atendimento específico
    atendimento = Atendimento.objects.first()

    if not atendimento:
        print("Nenhum atendimento encontrado")
        return

    # Carrega o histórico completo - método simplificado sem parâmetros
    historico = atendimento.carregar_historico_mensagens()

    print(f"=== Histórico do Atendimento {atendimento.id} ===")
    print(
        f"Cliente: {
            atendimento.cliente.nome or atendimento.cliente.telefone}")
    print(f"Status: {atendimento.get_status_display()}")
    print()

    # Mostra estatísticas
    print("=== Estatísticas ===")
    print(f"Total de mensagens: {len(historico['conteudo_mensagens'])}")
    print(f"Intents únicos detectados: {len(historico['intents_detectados'])}")
    print(
        f"Entidades únicas extraídas: {len(historico['entidades_extraidas'])}")
    print()

    # Mostra intents detectados
    if historico['intents_detectados']:
        print("=== Intents Detectados ===")
        for intent in sorted(historico['intents_detectados']):
            print(f"- {intent}")
        print()

    # Mostra entidades extraídas
    if historico['entidades_extraidas']:
        print("=== Entidades Extraídas ===")
        for entidade in sorted(historico['entidades_extraidas']):
            print(f"- {entidade}")
        print()

    # Mostra as mensagens (limitando a 5 para o exemplo)
    print("=== Últimas 5 Mensagens ===")
    for i, conteudo in enumerate(historico['conteudo_mensagens'][-5:], 1):
        print(f"{i}. {conteudo[:100]}{'...' if len(conteudo) > 100 else ''}")

    return historico


def exemplo_entidades_por_mensagem():
    """
    Exemplo de como extrair entidades de mensagens individuais.
    """
    # Busca mensagens com entidades extraídas
    mensagens_com_entidades = Mensagem.objects.exclude(
        entidades_extraidas__isnull=True
    ).exclude(
        entidades_extraidas={}
    )[:5]

    print("=== Entidades por Mensagem ===")

    for mensagem in mensagens_com_entidades:
        entidades = mensagem.extrair_entidades_formatadas()

        print(f"Mensagem {mensagem.id}:")
        print(
            f"  Conteúdo: {mensagem.conteudo[:50]}{'...' if len(mensagem.conteudo) > 50 else ''}")
        print(f"  Intent: {mensagem.intent_detectado or 'Não detectado'}")
        print(
            f"  Entidades: {
                ', '.join(
                    sorted(entidades)) if entidades else 'Nenhuma'}")
        print()


def exemplo_analise_conversa():
    """
    Exemplo de análise mais avançada usando o histórico.
    """
    atendimento = Atendimento.objects.first()

    if not atendimento:
        print("Nenhum atendimento encontrado")
        return

    # Carrega o histórico completo
    historico = atendimento.carregar_historico_mensagens()

    print(f"=== Análise da Conversa - Atendimento {atendimento.id} ===")

    # Análise por tipo de remetente
    mensagens_cliente = []
    mensagens_bot = []
    mensagens_atendente = []

    for mensagem in historico['mensagens']:
        if mensagem.remetente == TipoRemetente.CLIENTE:
            mensagens_cliente.append(mensagem)
        elif mensagem.remetente == TipoRemetente.BOT:
            mensagens_bot.append(mensagem)
        elif mensagem.remetente == TipoRemetente.ATENDENTE_HUMANO:
            mensagens_atendente.append(mensagem)

    print(f"Mensagens do cliente: {len(mensagens_cliente)}")
    print(f"Mensagens do bot: {len(mensagens_bot)}")
    print(f"Mensagens do atendente: {len(mensagens_atendente)}")
    print()

    # Análise de tipos de mensagem
    tipos_mensagem = {}
    for mensagem in historico['mensagens']:
        tipo = mensagem.get_tipo_display()
        tipos_mensagem[tipo] = tipos_mensagem.get(tipo, 0) + 1

    print("=== Tipos de Mensagem ===")
    for tipo, quantidade in sorted(tipos_mensagem.items()):
        print(f"{tipo}: {quantidade}")
    print()

    # Top intents
    if historico['intents_detectados']:
        print("=== Top Intents ===")
        for intent in sorted(historico['intents_detectados']):
            count = historico['mensagens'].filter(
                intent_detectado=intent).count()
            print(f"{intent}: {count} ocorrências")
        print()

    # Resumo da conversa
    total_caracteres = sum(len(conteudo)
                           for conteudo in historico['conteudo_mensagens'])
    media_caracteres = total_caracteres / \
        len(historico['conteudo_mensagens']) if historico['conteudo_mensagens'] else 0

    print("=== Resumo ===")
    print(f"Total de caracteres: {total_caracteres}")
    print(f"Média de caracteres por mensagem: {media_caracteres:.1f}")
    print(
        f"Duração da conversa: {
            atendimento.data_fim -
            atendimento.data_inicio if atendimento.data_fim else 'Em andamento'}")


def exemplo_uso_simples():
    """
    Exemplo de uso mais simples e direto do método.
    """
    # Busca um atendimento
    atendimento = Atendimento.objects.first()

    if not atendimento:
        print("Nenhum atendimento encontrado")
        return

    print("=== Uso Simples do Método ===")

    # Carrega o histórico - agora é muito mais simples!
    historico = atendimento.carregar_historico_mensagens()

    # Acesso direto aos dados
    print(f"📱 Total de mensagens: {len(historico['conteudo_mensagens'])}")
    print(f"🎯 Intents detectados: {len(historico['intents_detectados'])}")
    print(f"🔍 Entidades extraídas: {len(historico['entidades_extraidas'])}")

    # Exemplo de como usar os dados
    if historico['conteudo_mensagens']:
        print(
            f"\n📝 Primeira mensagem: {historico['conteudo_mensagens'][0][:80]}...")
        print(
            f"📝 Última mensagem: {historico['conteudo_mensagens'][-1][:80]}...")

    if historico['intents_detectados']:
        print(
            f"\n🎯 Intents encontrados: {
                ', '.join(
                    list(
                        historico['intents_detectados'])[
                        :3])}...")

    if historico['entidades_extraidas']:
        print(
            f"🔍 Entidades encontradas: {
                ', '.join(
                    list(
                        historico['entidades_extraidas'])[
                        :3])}...")


def exemplo_uso_para_ia():
    """
    Exemplo de como usar o histórico para alimentar uma IA/LLM.
    """
    atendimento = Atendimento.objects.first()

    if not atendimento:
        print("Nenhum atendimento encontrado")
        return

    print("=== Uso para IA/LLM ===")

    # Carrega o histórico
    historico = atendimento.carregar_historico_mensagens()

    # Cria contexto para IA
    contexto_conversa = "\n".join(historico['conteudo_mensagens'])
    intents_contexto = ", ".join(historico['intents_detectados'])
    entidades_contexto = ", ".join(historico['entidades_extraidas'])

    # Exemplo de prompt para IA
    prompt_ia = f"""
    Histórico da conversa:
    {contexto_conversa}

    Intents detectados: {intents_contexto}
    Entidades identificadas: {entidades_contexto}

    Com base neste contexto, responda à próxima mensagem do cliente.
    """

    print("📤 Prompt preparado para IA:")
    print(f"   - {len(historico['conteudo_mensagens'])} mensagens no contexto")
    print(f"   - {len(historico['intents_detectados'])} intents únicos")
    print(f"   - {len(historico['entidades_extraidas'])} entidades únicas")
    print(f"   - Total de caracteres: {len(prompt_ia)}")

    return {
        'prompt': prompt_ia,
        'historico': historico
    }


if __name__ == "__main__":
    print("Executando exemplos do método carregar_historico_mensagens otimizado...")
    print("=" * 70)

    try:
        # Exemplo 1: Uso simples
        print("1. Uso Simples e Otimizado")
        exemplo_uso_simples()
        print("\n" + "=" * 70 + "\n")

        # Exemplo 2: Uso para IA/LLM
        print("2. Uso para IA/LLM")
        exemplo_uso_para_ia()
        print("\n" + "=" * 70 + "\n")

        # Exemplo 3: Histórico completo
        print("3. Histórico Completo")
        exemplo_carregar_historico_completo()
        print("\n" + "=" * 70 + "\n")

        # Exemplo 4: Entidades por mensagem
        print("4. Entidades por Mensagem")
        exemplo_entidades_por_mensagem()
        print("\n" + "=" * 70 + "\n")

        # Exemplo 5: Análise da conversa
        print("5. Análise da Conversa")
        exemplo_analise_conversa()

    except Exception as e:
        print(f"Erro ao executar exemplos: {e}")
        import traceback
        traceback.print_exc()
