#!/usr/bin/env python3
"""
Exemplo demonstrando o novo formato de entidades padronizadas.

O novo formato utiliza dicionários diretos no formato {"tipo": "valor"}
em vez do formato anterior {"tipo": "tipo", "valor": "valor"}.
"""

from src.smart_core_assistant_painel.app.ui.oraculo.models import (
    Atendimento,
    Cliente,
    Mensagem,
    TipoMensagem,
    TipoRemetente,
)


def exemplo_novo_formato_basico():
    """
    Exemplo básico do novo formato de entidades.
    """
    print("=== Novo Formato de Entidades ===")

    # Formato novo (recomendado)
    entidades_novo_formato = [
        {"pessoa": "João Silva"},
        {"email": "joao.silva@empresa.com"},
        {"telefone": "+5511999999999"},
        {"produto": "Smartphone XYZ"},
        {"numero_pedido": "PED-12345"},
        {"valor_monetario": "R$ 1.299,00"},
        {"data": "2025-07-19"},
        {"empresa": "Tech Solutions LTDA"}
    ]

    print("Formato atual (novo):")
    for entidade in entidades_novo_formato:
        for tipo, valor in entidade.items():
            print(f"  {tipo}: {valor}")

    print("\nComparação com formato anterior:")
    print("Formato antigo: {'tipo': 'pessoa', 'valor': 'João Silva'}")
    print("Formato novo:   {'pessoa': 'João Silva'}")

    return entidades_novo_formato


def exemplo_criacao_mensagem_novo_formato():
    """
    Exemplo de criação de mensagem com o novo formato.
    """
    print("\n=== Criando Mensagem com Novo Formato ===")

    # Busca um atendimento existente ou cria um novo
    atendimento = Atendimento.objects.first()
    if not atendimento:
        # Cria cliente e atendimento para teste
        cliente, created = Cliente.objects.get_or_create(
            telefone="+5511999999999",
            defaults={"nome": "Cliente Teste"}
        )
        atendimento = Atendimento.objects.create(cliente=cliente)

    # Entidades no novo formato
    entidades = [
        {"pessoa": "Maria Oliveira"},
        {"cpf": "123.456.789-00"},
        {"produto": "Notebook Gamer"},
        {"problema": "tela piscando"},
        {"urgencia": "alta"}
    ]

    # Cria mensagem
    mensagem = Mensagem.objects.create(
        atendimento=atendimento,
        tipo=TipoMensagem.TEXTO_FORMATADO,
        conteudo="Olá, sou Maria Oliveira, CPF 123.456.789-00. Meu notebook gamer está com a tela piscando, preciso de ajuda urgente!",
        remetente=TipoRemetente.CLIENTE,
        intent_detectado="suporte_tecnico",
        entidades_extraidas=entidades)

    print(f"Mensagem criada com ID: {mensagem.id}")
    print(f"Entidades salvas: {mensagem.entidades_extraidas}")

    # Testa extração
    entidades_extraidas = mensagem.extrair_entidades_formatadas()
    print(f"Entidades extraídas: {entidades_extraidas}")

    return mensagem


def exemplo_compatibilidade_formatos():
    """
    Exemplo mostrando o formato padrão único de entidades.
    """
    print("\n=== Formato Padrão de Entidades ===")

    atendimento = Atendimento.objects.first()
    if not atendimento:
        print("Nenhum atendimento encontrado")
        return

    # Mensagem com formato padrão
    mensagem = Mensagem.objects.create(
        atendimento=atendimento,
        tipo=TipoMensagem.TEXTO_FORMATADO,
        conteudo="Mensagem com formato padrão",
        remetente=TipoRemetente.CLIENTE,
        entidades_extraidas=[
            {"nome": "Ana Costa"},
            {"email": "ana@email.com"},
            {"telefone": "+5511999999999"},
            {"produto": "Smartphone Premium"}
        ]
    )

    print("Entidades extraídas (formato padrão):")
    print(mensagem.extrair_entidades_formatadas())

    return mensagem


def exemplo_historico_novo_formato():
    """
    Exemplo de uso do histórico com novo formato.
    """
    print("\n=== Histórico com Novo Formato ===")

    atendimento = Atendimento.objects.first()
    if not atendimento:
        print("Nenhum atendimento encontrado")
        return

    # Carrega histórico
    historico = atendimento.carregar_historico_mensagens()

    print(f"Total de mensagens: {len(historico['conteudo_mensagens'])}")
    print(f"Intents detectados: {historico['intents_detectados']}")
    print(f"Entidades extraídas: {historico['entidades_extraidas']}")

    # Mostra algumas entidades se existirem
    if historico['entidades_extraidas']:
        print("\nPrimeiras 5 entidades encontradas:")
        for i, entidade in enumerate(
                list(historico['entidades_extraidas'])[:5], 1):
            print(f"  {i}. {entidade}")

    return historico


def exemplo_conversao_formato():
    """
    Exemplo de como usar o formato padrão de entidades.
    """
    print("\n=== Formato Padrão de Entidades ===")

    # Formato padrão único
    entidades_padrao = [
        {"nome": "João Silva"},
        {"email": "joao@email.com"},
        {"telefone": "+5511999999999"},
        {"produto": "Laptop Gaming"},
        {"categoria": "eletrônicos"},
        {"prioridade": "alta"}
    ]

    print("Formato padrão:")
    for entidade in entidades_padrao:
        for tipo, valor in entidade.items():
            print(f"  {tipo}: {valor}")

    # Exemplo de uso
    atendimento = Atendimento.objects.first()
    if atendimento:
        mensagem = Mensagem.objects.create(
            atendimento=atendimento,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            conteudo="Olá, sou João Silva, email joao@email.com, telefone +5511999999999. Preciso de ajuda com meu Laptop Gaming na categoria eletrônicos. É prioridade alta!",
            remetente=TipoRemetente.CLIENTE,
            entidades_extraidas=entidades_padrao)

        print(f"\nMensagem criada com ID: {mensagem.id}")
        entidades_extraidas = mensagem.extrair_entidades_formatadas()
        print(f"Entidades processadas: {entidades_extraidas}")

    return entidades_padrao


def exemplo_uso_em_llm():
    """
    Exemplo de como usar as entidades extraídas com LLMs.
    """
    print("\n=== Uso com LLMs ===")

    atendimento = Atendimento.objects.first()
    if not atendimento:
        print("Nenhum atendimento encontrado")
        return

    # Carrega histórico
    historico = atendimento.carregar_historico_mensagens()

    # Prepara contexto para LLM
    contexto_llm = {
        "mensagens": historico['conteudo_mensagens'],
        "intents": list(historico['intents_detectados']),
        "entidades": list(historico['entidades_extraidas']),
        "total_mensagens": len(historico['conteudo_mensagens'])
    }

    print("Contexto preparado para LLM:")
    print(f"  Total de mensagens: {contexto_llm['total_mensagens']}")
    print(f"  Intents identificados: {len(contexto_llm['intents'])}")
    print(f"  Entidades extraídas: {len(contexto_llm['entidades'])}")

    if contexto_llm['entidades']:
        print("  Primeiras entidades:")
        for entidade in contexto_llm['entidades'][:3]:
            print(f"    - {entidade}")

    return contexto_llm


if __name__ == "__main__":
    print("Demonstração do Novo Formato de Entidades")
    print("=" * 50)

    try:
        # Executa todos os exemplos
        exemplo_novo_formato_basico()
        exemplo_criacao_mensagem_novo_formato()
        exemplo_compatibilidade_formatos()
        exemplo_historico_novo_formato()
        exemplo_conversao_formato()
        exemplo_uso_em_llm()

        print("\n" + "=" * 50)
        print("Todos os exemplos executados com sucesso!")

    except Exception as e:
        print(f"Erro ao executar exemplos: {e}")
        import traceback
        traceback.print_exc()
