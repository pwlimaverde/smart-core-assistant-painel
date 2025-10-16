from __future__ import annotations

from typing import Any

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    Mensagem,
    StatusAtendimento,
    TipoMensagem,
    TipoRemetente,
)
from smart_core_assistant_painel.app.ui.clientes.models import Contato
from smart_core_assistant_painel.app.ui.operacional.models import (
    AtendenteHumano,
    Departamento,
)


class Command(BaseCommand):
    help = (
        "Semear dados mínimos de desenvolvimento: Departamento, Usuário, "
        "AtendenteHumano, Contatos, Atendimentos e Mensagens."
    )

    def add_arguments(self, parser: Any) -> None:
        # Sem argumentos por enquanto
        return None

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        """
        Executa a criação de dados mínimos de desenvolvimento.

        Observação: Apenas executa quando settings.DEBUG é True.
        """
        if not settings.DEBUG:
            self.stdout.write(
                self.style.ERROR(
                    "Operação bloqueada: este comando só pode ser executado em ambiente de desenvolvimento (DEBUG=True)."
                )
            )
            return

        # 1) Departamento
        suporte_dep, _ = Departamento.objects.get_or_create(
            nome="Suporte",
            defaults={
                "descricao": "Departamento de suporte técnico",
                "ativo": True,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"Departamento OK: {suporte_dep.nome}"))

        # 2) Usuário Django
        user, created_user = User.objects.get_or_create(
            username="agent1",
            defaults={
                "email": "agent1@example.com",
                "is_active": True,
            },
        )
        if created_user:
            user.set_password("123456")  # Apenas DEV
            user.save()
            self.stdout.write(self.style.SUCCESS("Usuário criado: agent1/123456"))
        else:
            # Garantir senha em dev
            user.set_password("123456")
            user.save(update_fields=["password"])
            self.stdout.write(self.style.WARNING("Usuário existente atualizado com senha padrão DEV."))

        # 3) AtendenteHumano vinculado ao usuário
        agente, created_agente = AtendenteHumano.objects.get_or_create(
            usuario_sistema="agent1",
            defaults={
                "nome": "Agente 1",
                "email": "agent1@example.com",
                "telefone": "5511988887777",
                "departamento": suporte_dep,
                "ativo": True,
                "disponivel": True,
                "max_atendimentos_simultaneos": 3,
            },
        )
        if created_agente:
            self.stdout.write(self.style.SUCCESS("AtendenteHumano criado: agent1"))
        else:
            # Garantir que está no departamento certo
            if agente.departamento_id != suporte_dep.id:
                agente.departamento = suporte_dep
                agente.save(update_fields=["departamento"])
            self.stdout.write(self.style.WARNING("AtendenteHumano já existia. Dados checados."))

        # 4) Contatos de teste
        contatos_data: list[dict[str, str]] = [
            {"telefone": "5511999990001", "nome_contato": "João Teste"},
            {"telefone": "5511999990002", "nome_contato": "Maria Teste"},
            {"telefone": "5511999990003", "nome_contato": "Carlos Teste"},
            {"telefone": "5511999990004", "nome_contato": "Ana Teste"},
        ]
        contatos: list[Contato] = []
        for data in contatos_data:
            contato, _ = Contato.objects.get_or_create(
                telefone=data["telefone"],
                defaults={
                    "nome_contato": data["nome_contato"],
                    "ativo": True,
                },
            )
            contatos.append(contato)
        self.stdout.write(self.style.SUCCESS(f"Contatos OK: {len(contatos)} criados/obtidos"))

        # 5) Atendimentos de teste (uma por coluna do Kanban)
        # - Fila: aguardando_atendente, sem atendente
        fila, _ = Atendimento.objects.get_or_create(
            contato=contatos[0],
            departamento=suporte_dep,
            status=StatusAtendimento.AGUARDANDO_ATENDENTE,
            defaults={
                "assunto": "Problema de conexão",
                "prioridade": "normal",
            },
        )
        Mensagem.objects.get_or_create(
            atendimento=fila,
            conteudo="Olá, estou com problemas de conexão.",
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.CONTATO,
        )

        # - Meus: em_andamento, atribuído ao agente
        meus, _ = Atendimento.objects.get_or_create(
            contato=contatos[1],
            departamento=suporte_dep,
            status=StatusAtendimento.EM_ANDAMENTO,
            atendente_humano=agente,
            defaults={
                "assunto": "Erro no aplicativo",
                "prioridade": "alta",
            },
        )
        Mensagem.objects.get_or_create(
            atendimento=meus,
            conteudo="Estou analisando o erro e retorno em breve.",
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.ATENDENTE_HUMANO,
        )

        # - Aguardando Cliente: aguardando_contato, atribuído ao agente
        aguardando_cliente, _ = Atendimento.objects.get_or_create(
            contato=contatos[2],
            departamento=suporte_dep,
            status=StatusAtendimento.AGUARDANDO_CONTATO,
            atendente_humano=agente,
            defaults={
                "assunto": "Solicitação de documentos",
                "prioridade": "normal",
            },
        )
        Mensagem.objects.get_or_create(
            atendimento=aguardando_cliente,
            conteudo="Por favor, envie os documentos solicitados.",
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.ATENDENTE_HUMANO,
        )

        # - Finalizados: resolvido, atribuído ao agente
        finalizado, _ = Atendimento.objects.get_or_create(
            contato=contatos[3],
            departamento=suporte_dep,
            status=StatusAtendimento.RESOLVIDO,
            atendente_humano=agente,
            defaults={
                "assunto": "Configuração concluída",
                "prioridade": "baixa",
            },
        )
        Mensagem.objects.get_or_create(
            atendimento=finalizado,
            conteudo="Configuração realizada com sucesso!",
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.BOT,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed concluído: Departamento, Usuário, AtendenteHumano, Contatos, Atendimentos e Mensagens."
            )
        )