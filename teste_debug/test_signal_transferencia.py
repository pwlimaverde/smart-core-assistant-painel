"""
Script de teste manual para o signal de transferência com saudação.

Este script demonstra como testar manualmente o signal que monitora
mudanças no campo `atendente_humano` do modelo Atendimento.

IMPORTANTE: Execute este script através do Django shell ou como
um comando de gerenciamento.

Uso:
    uv run task shell
    >>> exec(open('teste_debug/test_signal_transferencia.py').read())
"""

from smart_core_assistant_painel.app.atendimentos.models import Atendimento
from smart_core_assistant_painel.app.operacional.models import Atendente


def test_signal_transferencia_humano() -> None:
    """
    Testa o signal de transferência para atendente humano.

    Este teste:
    1. Busca um atendimento ativo
    2. Busca um atendente disponível
    3. Atribui o atendente ao atendimento
    4. O signal deve detectar a mudança e logar informações
    """
    print("=" * 60)
    print("TESTE DO SIGNAL DE TRANSFERÊNCIA PARA HUMANO")
    print("=" * 60)

    # Busca um atendimento ativo
    atendimento = (
        Atendimento.objects.filter(atendente_humano__isnull=True)
        .order_by("-data_inicio")
        .first()
    )

    if not atendimento:
        print(
            "\n❌ Nenhum atendimento sem atendente encontrado. "
            "Crie um atendimento primeiro."
        )
        return

    print(f"\n✓ Atendimento encontrado: ID {atendimento.id}")
    print(f"  - Status: {atendimento.status}")
    print(f"  - Contato: {atendimento.contato.telefone}")

    # Busca um atendente disponível
    atendente = Atendente.objects.filter(ativo=True).first()

    if not atendente:
        print(
            "\n❌ Nenhum atendente ativo encontrado. Crie um atendente primeiro."
        )
        return

    print(f"\n✓ Atendente encontrado: {atendente.nome} (ID: {atendente.id})")

    # Testa o signal através da função transferir_para_humano_com_saudacao
    print("\n" + "=" * 60)
    print(
        "EXECUTANDO: atendimento.transferir_para_humano_com_saudacao("
        f"atendente_id={atendente.id})"
    )
    print("=" * 60)
    print(
        "\nObserve os logs para ver o signal em ação. "
        "A mensagem de saudação deve ser criada."
    )
    print("\nExecutando...")

    try:
        atendimento.transferir_para_humano_com_saudacao(
            atendente_id=atendente.id,
            observacao="Teste manual do signal de transferência",
        )
        print("\n✅ Transferência executada com sucesso!")
        print(f"   - Atendente: {atendimento.atendente_humano.nome}")
        print(f"   - Status: {atendimento.status}")
        print(f"   - Bot pode atender: {atendimento.bot_pode_atender}")

        # Verifica a última mensagem criada
        ultima_mensagem = atendimento.mensagens.order_by("-timestamp").first()
        if ultima_mensagem and ultima_mensagem.resposta_bot:
            print(f"\n✅ Mensagem de saudação criada:")
            print(f'   "{ultima_mensagem.resposta_bot}"')

    except Exception as e:
        print(f"\n❌ Erro ao executar transferência: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_signal_transferencia_humano()
