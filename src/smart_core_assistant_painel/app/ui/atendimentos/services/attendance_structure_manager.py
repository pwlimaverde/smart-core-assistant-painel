"""Gerenciador de estrutura de atendimento.

Este módulo contém a lógica para garantir a existência de departamentos,
fluxos e etapas necessários para o funcionamento do sistema de atendimentos.
"""

from typing import TYPE_CHECKING

from loguru import logger

from .interfaces import AttendanceStructureManagerInterface

if TYPE_CHECKING:
    from smart_core_assistant_painel.app.ui.atendimentos.models import (
        Atendimento,
        StatusAtendimento,
    )
    from smart_core_assistant_painel.app.ui.operacional.models import (
        Departamento,
        FluxoAtendimento,
        TipoEtapa,
    )


class AttendanceStructureManager(AttendanceStructureManagerInterface):
    """Gerenciador de estrutura de atendimento.

    Responsabilidades:
    - Garantir estrutura padrão existe
    - Gerenciar fluxos disponíveis
    - Configurar atendimentos
    """

    def ensure_default_structure(
        self,
    ) -> tuple["Departamento", "FluxoAtendimento"]:
        """Garante que exista a estrutura padrão de atendimento.

        Cria o departamento 'Atendimento' e o fluxo 'Atendimento Inicial'
        se não existirem.

        Returns:
            Tupla com (departamento, fluxo) criados ou existentes.
        """
        try:
            from smart_core_assistant_painel.app.ui.operacional.models import (
                Departamento,
                FluxoAtendimento,
            )

            # Verifica/cria departamento Atendimento
            departamento, created_departamento = (
                Departamento.objects.get_or_create(
                    nome="Atendimento",
                    defaults={
                        "descricao": (
                            "Departamento usado para centralizar o atendimento via mensagens "
                            "e fazer seu processamento antes de seguir para os outros departamentos."
                        ),
                        "ativo": True,
                    },
                )
            )

            if created_departamento:
                logger.info(
                    f"Departamento 'Atendimento' criado com ID {departamento.id}"
                )
            else:
                logger.debug(
                    f"Departamento 'Atendimento' já existe (ID {departamento.id})"
                )

            # Verifica/cria fluxo Atendimento Inicial
            fluxo, created_fluxo = FluxoAtendimento.objects.get_or_create(
                departamento=departamento,
                nome="Atendimento Inicial",
                defaults={
                    "descricao": "Fluxo responsável pelo processamento inicial dos atendimentos",
                    "ativo": True,
                },
            )

            if created_fluxo:
                logger.info(
                    f"Fluxo 'Atendimento Inicial' criado com ID {fluxo.id}"
                )
            else:
                logger.debug(
                    f"Fluxo 'Atendimento Inicial' já existe (ID {fluxo.id})"
                )

            return departamento, fluxo

        except Exception as e:
            logger.error(
                f"Erro ao garantir estrutura de atendimento padrão: {e}"
            )
            raise

    def get_available_flows(self) -> dict[str, str]:
        """Retorna fluxos de atendimento disponíveis.

        Returns:
            Dicionário no formato {"nome_fluxo - nome_departamento": "descrição"}.
        """
        try:
            from smart_core_assistant_painel.app.ui.operacional.models import (
                FluxoAtendimento,
            )

            fluxos_disponiveis: dict[str, str] = {}

            # Busca todos os fluxos ativos (exceto o padrão)
            fluxos_queryset = (
                FluxoAtendimento.objects.filter(ativo=True)
                .exclude(
                    nome="Atendimento Inicial",
                    departamento__nome="Atendimento",
                )
                .select_related("departamento")
                .order_by("departamento__nome", "nome")
            )

            for fluxo in fluxos_queryset:
                # Formata a chave como "nome_fluxo - nome_departamento"
                chave = f"{fluxo.nome} - {fluxo.departamento.nome}"

                # Usa a descrição do fluxo como valor
                valor = (
                    fluxo.descricao
                    or f"Fluxo de {fluxo.nome} para {fluxo.departamento.nome}"
                )

                fluxos_disponiveis[chave] = valor

            logger.info(
                f"Gerado dicionário com {len(fluxos_disponiveis)} fluxos disponíveis"
            )
            return fluxos_disponiveis

        except Exception as e:
            logger.error(
                f"Erro ao gerar dicionário de fluxos disponíveis: {e}"
            )
            return {}

    def configure_default_attendance(self, attendance: "Atendimento") -> None:
        """Configura um atendimento para usar a estrutura padrão.

        Args:
            attendance: Atendimento a ser configurado.
        """
        try:
            from smart_core_assistant_painel.app.ui.operacional.models import (
                TipoEtapa,
            )

            departamento, fluxo = self.ensure_default_structure()

            # Atualiza o departamento do atendimento
            attendance.departamento = departamento

            # Busca a etapa "Fila de Atendimento" do fluxo
            etapa_fila = fluxo.etapas.filter(
                nome="Fila de Atendimento", tipo_etapa=TipoEtapa.FILA
            ).first()

            if etapa_fila:
                attendance.etapa_atual = etapa_fila
                logger.debug(
                    f"Atendimento {attendance.id} configurado para etapa '{etapa_fila.nome}'"
                )
            else:
                logger.warning(
                    f"Etapa 'Fila de Atendimento' não encontrada no fluxo {fluxo.id}"
                )

            # Salva as alterações apenas nos campos modificados
            attendance.save(update_fields=["departamento", "etapa_atual"])

        except Exception as e:
            logger.error(
                f"Erro ao configurar atendimento padrão {attendance.id}: {e}"
            )
            raise

    def _update_attendance_status_ongoing(
        self,
        attendance: "Atendimento",
    ) -> None:
        """Atualiza o status e etapa do atendimento para "Em Atendimento".

        Args:
            attendance: Objeto Atendimento a ser atualizado.
        """
        try:
            from smart_core_assistant_painel.app.ui.atendimentos.models import (
                StatusAtendimento,
            )
            from smart_core_assistant_painel.app.ui.operacional.models import (
                TipoEtapa,
            )

            # Garante que a estrutura padrão exista
            _, fluxo = self.ensure_default_structure()

            # Atualiza o status do atendimento
            attendance.status = StatusAtendimento.EM_ATENDIMENTO

            # Busca a etapa "Em Atendimento" do fluxo
            etapa_em_atendimento = fluxo.etapas.filter(
                nome="Em Atendimento", tipo_etapa=TipoEtapa.TRABALHO
            ).first()

            if etapa_em_atendimento:
                attendance.etapa_atual = etapa_em_atendimento
                logger.debug(
                    f"Atendimento {attendance.id} movido para etapa '{etapa_em_atendimento.nome}'"
                )
            else:
                logger.warning(
                    f"Etapa 'Em Atendimento' não encontrada no fluxo {fluxo.id}"
                )

            # Salva as alterações apenas nos campos modificados
            attendance.save(update_fields=["status", "etapa_atual"])

            logger.info(
                f"Atendimento {attendance.id} atualizado para status 'Em Atendimento'"
            )

        except Exception as e:
            logger.error(
                f"Erro ao atualizar status do atendimento {attendance.id}: {e}"
            )
            raise
