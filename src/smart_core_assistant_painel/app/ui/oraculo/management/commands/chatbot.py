"""
Comando Django para gerenciar operações do chatbot
"""

from typing import Any
from django.core.management.base import BaseCommand

from ...models import (
    Atendimento,
    Cliente,
    FluxoConversa,
    Mensagem,
    StatusAtendimento,
    TipoMensagem,
    inicializar_atendimento_whatsapp,
    processar_mensagem_whatsapp,
)


class Command(BaseCommand):
    help = "Gerencia operações do chatbot de atendimento"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--acao",
            type=str,
            help="Ação a ser executada: inicializar, processar, estatisticas, limpar",
            required=True,
        )
        parser.add_argument(
            "--telefone", type=str, help="Número de telefone do cliente"
        )
        parser.add_argument("--mensagem", type=str, help="Mensagem a ser processada")
        parser.add_argument("--nome", type=str, help="Nome do cliente")

    def handle(self, *args: str, **options: dict[str, Any]) -> None:
        acao = str(options["acao"])

        if acao == "inicializar":
            self.inicializar_cliente(options)
        elif acao == "processar":
            self.processar_mensagem(options)
        elif acao == "estatisticas":
            self.mostrar_estatisticas()
        elif acao == "limpar":
            self.limpar_dados()
        elif acao == "demo":
            self.executar_demo()
        else:
            self.stdout.write(self.style.ERROR(f'Ação "{acao}" não reconhecida'))

    def inicializar_cliente(self, options: dict[str, Any]) -> None:
        """Inicializa um novo cliente e atendimento"""
        telefone = options.get("telefone")
        nome = options.get("nome")
        mensagem = options.get("mensagem", "Olá!")

        if not telefone:
            self.stdout.write(self.style.ERROR("Número de telefone é obrigatório"))
            return

        try:
            cliente, atendimento = inicializar_atendimento_whatsapp(
                numero_telefone=telefone, primeira_mensagem=mensagem, nome_contato=nome
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Cliente inicializado: {cliente.telefone} - {cliente.nome_contato or 'Sem nome'}"
                )
            )
            status_display = getattr(atendimento, "get_status_display", lambda: atendimento.status)()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Atendimento criado: #{atendimento.id} - Status: {status_display}"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao inicializar cliente: {e}"))

    def processar_mensagem(self, options: dict[str, Any]) -> None:
        """Processa uma mensagem de cliente"""
        telefone = options.get("telefone")
        mensagem = options.get("mensagem")

        if not telefone or not mensagem:
            self.stdout.write(self.style.ERROR("Telefone e mensagem são obrigatórios"))
            return

        try:
            # Usar argumentos obrigatórios com valores padrão
            mensagem_id = processar_mensagem_whatsapp(
                numero_telefone=telefone,
                conteudo=mensagem,
                message_type="text",  # Tipo padrão para texto
                message_id=f"chatbot_cmd_{telefone}_{mensagem[:10]}"  # ID único
            )

            # Buscar o objeto mensagem pelo ID retornado
            from ...models import Mensagem

            mensagem_obj: Mensagem = Mensagem.objects.get(id=mensagem_id)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Mensagem processada: {mensagem_obj.conteudo[:50]}..."
                )
            )
            att = getattr(mensagem_obj, "atendimento", None)
            att_id = getattr(att, "id", None)
            self.stdout.write(
                self.style.SUCCESS(f"Atendimento: #{att_id}")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao processar mensagem: {e}"))

    def mostrar_estatisticas(self) -> None:
        """Mostra estatísticas do sistema"""
        self.stdout.write(self.style.SUCCESS("\n=== ESTATÍSTICAS DO CHATBOT ==="))

        # Contadores básicos
        total_clientes = Cliente.objects.count()
        total_atendimentos = Atendimento.objects.count()
        total_mensagens = Mensagem.objects.count()

        self.stdout.write(f"Total de clientes: {total_clientes}")
        self.stdout.write(f"Total de atendimentos: {total_atendimentos}")
        self.stdout.write(f"Total de mensagens: {total_mensagens}")

        # Atendimentos por status
        self.stdout.write("\n--- Atendimentos por Status ---")
        for status in StatusAtendimento:
            count = Atendimento.objects.filter(status=status).count()
            self.stdout.write(f"{status.label}: {count}")

        # Mensagens por tipo
        self.stdout.write("\n--- Mensagens por Tipo ---")
        for tipo in TipoMensagem:
            count = Mensagem.objects.filter(tipo=tipo).count()
            self.stdout.write(f"{tipo.label}: {count}")

        # Avaliações
        from django.db.models import Avg

        avaliacao_media = Atendimento.objects.filter(avaliacao__isnull=False).aggregate(
            Avg("avaliacao")
        )["avaliacao__avg"]

        if avaliacao_media:
            self.stdout.write(f"\nAvaliação média: {avaliacao_media:.2f}")

        # Clientes mais ativos
        self.stdout.write("\n--- Top 5 Clientes Mais Ativos ---")
        from django.db.models import Count

        top_clientes = Cliente.objects.annotate(
            total_atendimentos=Count("atendimentos")
        ).order_by("-total_atendimentos")[:5]

        for cliente in top_clientes:
            total = getattr(cliente, "total_atendimentos", None)
            self.stdout.write(
                f"{cliente.telefone} ({cliente.nome_fantasia or 'Sem nome'}): {total} atendimentos"
            )

    def limpar_dados(self) -> None:
        """Limpa dados de teste (cuidado!)"""
        resposta = input(
            'Tem certeza que deseja limpar TODOS os dados? (digite "confirmar"): '
        )

        if resposta.lower() == "confirmar":
            Mensagem.objects.all().delete()
            Atendimento.objects.all().delete()
            Cliente.objects.all().delete()
            FluxoConversa.objects.all().delete()

            self.stdout.write(self.style.SUCCESS("Todos os dados foram removidos!"))
        else:
            self.stdout.write(self.style.WARNING("Operação cancelada"))

    def executar_demo(self) -> None:
        """Executa uma demonstração do sistema"""
        self.stdout.write(self.style.SUCCESS("\n=== DEMONSTRAÇÃO DO CHATBOT ==="))

        # Simula conversas
        telefones = ["+5511999999999", "+5511888888888", "+5511777777777"]
        mensagens = [
            "Olá! Preciso de ajuda com meu pedido.",
            "Qual é o status do meu pedido #12345?",
            "Quero cancelar minha compra.",
        ]

        for i, telefone in enumerate(telefones):
            self.stdout.write(f"\n--- Simulando conversa {i + 1} ---")

            # Inicializa cliente
            cliente, atendimento = inicializar_atendimento_whatsapp(
                numero_telefone=telefone,
                primeira_mensagem=mensagens[i],
                nome_contato=f"Cliente {i + 1}",
            )

            self.stdout.write(f"Cliente: {cliente.telefone}")
            self.stdout.write(f"Primeira mensagem: {mensagens[i]}")

            # Adiciona algumas mensagens de exemplo
            respostas = [
                "Vou verificar isso para você.",
                "Encontrei suas informações.",
                "Problema resolvido!",
            ]

            for resposta in respostas:
                Mensagem.objects.create(
                    atendimento=atendimento,
                    tipo=TipoMensagem.TEXTO_FORMATADO,
                    conteudo=resposta,
                    is_from_client=False,
                    metadados={"gerada_por": "demo"},
                )

            # Finaliza atendimento
            atendimento.avaliacao = 5
            atendimento.finalizar_atendimento()

            self.stdout.write(self.style.SUCCESS("Atendimento finalizado com sucesso!"))

        self.stdout.write(self.style.SUCCESS("\n=== DEMONSTRAÇÃO CONCLUÍDA ==="))
        self.stdout.write("Use --acao estatisticas para ver os resultados")
