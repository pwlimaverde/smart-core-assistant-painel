#!/usr/bin/env python3
"""
Exemplo de uso das entidades extraídas com formato padronizado.

Este arquivo mostra como trabalhar com o novo formato padronizado das entidades extraídas,
que agora devem sempre ser uma lista de dicionários com chave e valor.
"""

from src.smart_core_assistant_painel.app.ui.oraculo.models import (
    Atendimento,
    Mensagem,
    TipoMensagem,
    TipoRemetente,
)


def exemplo_formato_entidades_padronizado():
    """
    Exemplo do formato padronizado para entidades extraídas.
    """
    print("=== Formato Padronizado de Entidades ===")

    # Formato correto: lista de dicionários no formato {"tipo": "valor"}
    entidades_padronizadas = [
        {"pessoa": "João Silva"},
        {"email": "joao@email.com"},
        {"telefone": "+5511999999999"},
        {"produto": "Smartphone XYZ"},
        {"data": "2025-07-19"},
        {"numero_pedido": "PED-12345"},
        {"valor_monetario": "R$ 1.299,00"}
    ]

    print("Formato correto (lista de dicionários diretos):")
    for entidade in entidades_padronizadas:
        for tipo, valor in entidade.items():
            print(f"  - {tipo}: {valor}")

    return entidades_padronizadas


def exemplo_criar_mensagem_com_entidades():
    """
    Exemplo de como criar uma mensagem com entidades no formato padronizado.
    """
    print("\n=== Criando Mensagem com Entidades ===")

    # Busca um atendimento existente
    atendimento = Atendimento.objects.first()

    if not atendimento:
        print("Nenhum atendimento encontrado")
        return

    # Entidades extraídas no formato padronizado (novo formato)
    entidades = [
        {"nome": "Maria Santos"},
        {"cpf": "123.456.789-00"},
        {"intent": "cancelar_pedido"},
        {"numero_pedido": "12345"}
    ]

    # Cria a mensagem
    mensagem = Mensagem.objects.create(
        atendimento=atendimento,
        tipo=TipoMensagem.TEXTO_FORMATADO,
        conteudo="Olá, sou Maria Santos, CPF 123.456.789-00, quero cancelar o pedido 12345",
        remetente=TipoRemetente.CLIENTE,
        intent_detectado="cancelar_pedido",
        entidades_extraidas=entidades  # Lista de dicionários no novo formato
    )

    print(f"Mensagem criada com ID: {mensagem.id}")
    print(f"Entidades salvas: {mensagem.entidades_extraidas}")

    # Testa extração de entidades
    entidades_extraidas = mensagem.extrair_entidades_formatadas()
    print(f"Entidades extraídas: {entidades_extraidas}")

    return mensagem


def exemplo_diferentes_formatos_chave_valor():
    """
    Exemplo do formato padrão único de entidades.
    """
    print("\n=== Formato Padrão de Entidades ===")

    # Formato padrão único
    formatos_aceitos = [
        # Formato padrão (único suportado)
        {"nome": "João Silva"},
        {"email": "joao@email.com"},
        {"telefone": "+5511999999999"},
        {"categoria": "produto", "nome_produto": "Smartphone", "codigo": "SM123"},
        {"pessoa": "Maria", "confianca": 0.95, "inicio": 0, "fim": 5}
    ]

    atendimento = Atendimento.objects.first()

    if not atendimento:
        print("Nenhum atendimento encontrado")
        return

    # Cria mensagem com formato padrão
    mensagem = Mensagem.objects.create(
        atendimento=atendimento,
        tipo=TipoMensagem.TEXTO_FORMATADO,
        conteudo="Mensagem de teste com formato padrão de entidades",
        remetente=TipoRemetente.CLIENTE,
        entidades_extraidas=formatos_aceitos
    )

    print(f"Mensagem criada com ID: {mensagem.id}")

    # Extrai entidades (método vai processar o formato padrão)
    entidades = mensagem.extrair_entidades_formatadas()
    print(f"Entidades processadas: {entidades}")

    return mensagem


def exemplo_historico_com_entidades_padronizadas():
    """
    Exemplo de como usar o histórico com entidades padronizadas.
    """
    print("\n=== Histórico com Entidades Padronizadas ===")

    atendimento = Atendimento.objects.first()

    if not atendimento:
        print("Nenhum atendimento encontrado")
        return

    # Carrega histórico
    historico = atendimento.carregar_historico_mensagens()

    print(f"Total de mensagens: {len(historico['conteudo_mensagens'])}")
    print(f"Intents únicos: {len(historico['intents_detectados'])}")
    print(f"Entidades únicas: {len(historico['entidades_extraidas'])}")

    if historico['entidades_extraidas']:
        print("\nEntidades encontradas no histórico:")
        for i, entidade in enumerate(
                sorted(historico['entidades_extraidas']), 1):
            print(f"  {i}. {entidade}")

    return historico


def exemplo_validacao_formato():
    """
    Exemplo de validação do formato das entidades.
    """
    print("\n=== Validação de Formato ===")

    def validar_entidades(entidades):
        """Valida se as entidades estão no formato correto."""
        if not isinstance(entidades, list):
            return False, "Entidades devem ser uma lista"

        for i, entidade in enumerate(entidades):
            if not isinstance(entidade, dict):
                return False, f"Item {i} deve ser um dicionário"

            if not entidade:
                return False, f"Item {i} está vazio"

            # Verifica se todos os valores são válidos (não vazios)
            for chave, valor in entidade.items():
                if not valor or not str(valor).strip():
                    return False, f"Item {i} tem valor vazio para chave '{chave}'"

        return True, "Formato válido"

    # Testes de validação
    testes = [
        # Formato correto
        [{"nome": "João Silva"}, {"email": "joao@email.com"}],

        # Formato incorreto - não é lista
        {"nome": "João"},

        # Formato incorreto - item não é dicionário
        ["string_simples"],

        # Formato vazio
        [],

        # Formato com valor vazio
        [{"nome": ""}],

        # Formato correto com múltiplas chaves
        [{"pessoa": "Maria", "idade": 30, "cidade": "São Paulo"}],

        # Formato com dicionário vazio
        [{}],

        # Formato com chaves personalizadas
        [{"categoria": "pessoa", "nome": "Maria"}]
    ]

    for i, teste in enumerate(testes, 1):
        valido, mensagem = validar_entidades(teste)
        status = "✅" if valido else "❌"
        print(f"Teste {i}: {status} {mensagem}")
        print(f"  Dados: {teste}")
        print()


def exemplo_formato_padrao_unico():
    """
    Exemplo demonstrando apenas o formato padrão único suportado.
    """
    print("\n=== Formato Padrão Único ===")

    # Apenas um formato é suportado: {"tipo": "valor"}
    entidades_padrao = [
        {"nome": "João Silva"},
        {"email": "joao@email.com"},
        {"telefone": "+5511999999999"},
        {"empresa": "Tech Solutions"},
        {"cargo": "Desenvolvedor"},
        {"experiencia": "5 anos"},
        {"linguagens": "Python, JavaScript"}
    ]

    print("Formato padrão único (obrigatório):")
    for entidade in entidades_padrao:
        for tipo, valor in entidade.items():
            print(f"  {tipo}: {valor}")

    # Exemplo de uso prático
    atendimento = Atendimento.objects.first()
    if atendimento:
        mensagem = Mensagem.objects.create(
            atendimento=atendimento,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            conteudo="Olá, sou João Silva da Tech Solutions, desenvolvedor com 5 anos de experiência em Python e JavaScript.",
            remetente=TipoRemetente.CLIENTE,
            entidades_extraidas=entidades_padrao)

        print(f"\nMensagem criada: ID {mensagem.id}")
        entidades_extraidas = mensagem.extrair_entidades_formatadas()
        print(f"Entidades processadas: {entidades_extraidas}")

    print("\nBeneficios do formato único:")
    print('- Simplicidade: {"tipo": "valor"}')
    print("- Clareza: chave direta para valor")
    print("- Consistência: apenas um padrão")
    print("- Facilidade de uso: sem ambiguidade")


if __name__ == "__main__":
    print("Executando exemplos de entidades padronizadas...")
    print("=" * 60)

    try:
        # Exemplo 1: Formato padronizado
        exemplo_formato_entidades_padronizado()

        # Exemplo 2: Criar mensagem
        exemplo_criar_mensagem_com_entidades()

        # Exemplo 3: Formato padrão único
        exemplo_diferentes_formatos_chave_valor()

        # Exemplo 4: Histórico
        exemplo_historico_com_entidades_padronizadas()

        # Exemplo 5: Validação
        exemplo_validacao_formato()

        # Exemplo 6: Formato padrão único
        exemplo_formato_padrao_unico()

    except Exception as e:
        print(f"Erro ao executar exemplos: {e}")
        import traceback
        traceback.print_exc()
        print(f"Erro ao executar exemplos: {e}")
        import traceback
        traceback.print_exc()
