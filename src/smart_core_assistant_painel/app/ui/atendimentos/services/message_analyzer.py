"""Serviço de análise de mensagens.

Este módulo contém a lógica para detectar intenções, extrair entidades
e processar informações de contato a partir de mensagens.
"""

import json
from typing import TYPE_CHECKING, Any

from django.utils import timezone
from loguru import logger

from smart_core_assistant_painel.modules.ai_engine import FeaturesCompose
from smart_core_assistant_painel.modules.services import SERVICEHUB

from .interfaces import MessageAnalyzerInterface

if TYPE_CHECKING:
    from smart_core_assistant_painel.app.ui.atendimentos.models import (
        Mensagem,
    )


class MessageAnalyzer(MessageAnalyzerInterface):
    """Serviço de análise de mensagens.

    Responsabilidades:
    - Detectar intenções em mensagens
    - Extrair entidades
    - Processar dados do contato
    """

    def analyze_message_content(self, message_id: int) -> dict[str, Any]:
        """Analisa o conteúdo da mensagem para detectar intenção e entidades.

        Args:
            message_id: ID da mensagem a ser analisada.

        Returns:
            Dicionário com intenções e entidades detectadas.
        """
        try:
            from smart_core_assistant_painel.app.ui.atendimentos.models import (
                Atendimento,
                Mensagem,
            )

            mensagem: Mensagem = Mensagem.objects.get(id=message_id)
            atendimento: Atendimento = mensagem.atendimento

            # Verifica se é primeiro atendimento
            exists_atendimento_anterior = (
                Atendimento.objects.filter(contato=atendimento.contato)
                .exclude(id=atendimento.id)
                .exists()
            )

            # Carrega histórico excluindo mensagem atual
            historico_atendimento = atendimento.carregar_historico_mensagens(
                excluir_mensagem_id=message_id
            )

            # Se é primeira mensagem, dispara apresentação
            if (
                not exists_atendimento_anterior
                and not historico_atendimento.get("conteudo_mensagens")
            ):
                FeaturesCompose.mensagem_apresentacao()

            # Analisa mensagem
            from smart_core_assistant_painel.app.ui.treinamento.models import (
                QueryCompose,
            )

            intent_types = QueryCompose.build_intent_types_config()
            resultado_analise = FeaturesCompose.analise_previa_mensagem(
                historico_atendimento=historico_atendimento,
                context=mensagem.conteudo,
                valid_intent_types=intent_types,
            )

            # Salva resultados
            mensagem.intent_detectado = resultado_analise.intent_types
            mensagem.entidades_extraidas = resultado_analise.entity_types
            mensagem.save(
                update_fields=["intent_detectado", "entidades_extraidas"]
            )

            # Processa entidades do contato
            self.process_contact_entities(
                mensagem, resultado_analise.entity_types
            )

            return {
                "intent_types": resultado_analise.intent_types,
                "entity_types": resultado_analise.entity_types,
            }

        except Exception as e:
            logger.error(
                f"Erro ao analisar conteúdo da mensagem {message_id}: {e}"
            )
            return {"intent_types": [], "entity_types": []}

    def process_contact_entities(
        self,
        message: "Mensagem",
        entity_types: list[dict[str, Any]],
    ) -> None:
        """Processa entidades extraídas para atualizar dados do contato.

        Args:
            message: Mensagem contendo as entidades.
            entity_types: Lista de tipos de entidades a processar.
        """
        try:
            from smart_core_assistant_painel.app.ui.clientes.models import (
                Contato,
            )

            atendimento = message.atendimento
            contato: Contato = atendimento.contato
            contato_atualizado = False
            metadados_atualizados = False
            entidades_metadados = self._get_valid_metadata_entities()

            for entidade_dict in entity_types:
                for tipo_entidade, valor in entidade_dict.items():
                    # Atualiza nome do contato
                    if tipo_entidade.lower() == "nome_contato" and valor:
                        if not contato.nome_contato or len(
                            str(valor).strip()
                        ) > len(contato.nome_contato or ""):
                            contato.nome_contato = str(valor).strip()
                            contato_atualizado = True

                    # Atualiza metadados
                    elif (
                        tipo_entidade.lower() in entidades_metadados and valor
                    ):
                        valor_limpo = str(valor).strip()
                        if valor_limpo:
                            if not contato.metadados:
                                contato.metadados = {}
                            if (
                                tipo_entidade.lower() not in contato.metadados
                                or contato.metadados[tipo_entidade.lower()]
                                != valor_limpo
                            ):
                                contato.metadados[tipo_entidade.lower()] = (
                                    valor_limpo
                                )
                                metadados_atualizados = True

            # Salva mudanças
            if contato_atualizado or metadados_atualizados:
                update_fields = []
                if contato_atualizado:
                    update_fields.append("nome_contato")
                if metadados_atualizados:
                    update_fields.append("metadados")
                contato.ultima_interacao = timezone.now()
                update_fields.append("ultima_interacao")
                contato.save(update_fields=update_fields)

                if not contato.nome_contato:
                    FeaturesCompose.solicitacao_info_cliene()

        except Exception as e:
            logger.error(f"Erro ao processar entidades do contato: {e}")

    def _get_valid_metadata_entities(self) -> set[str]:
        """Obtém entidades válidas para metadados do contato.

        Returns:
            Conjunto de nomes de entidades válidas.
        """
        try:
            valid_entity_types = SERVICEHUB.VALID_ENTITY_TYPES
            if not valid_entity_types:
                return set()

            entidades_config: dict[str, Any] = json.loads(valid_entity_types)
            entidades_validas: set[str] = set()

            if "entity_types" in entidades_config:
                for _, entidades in entidades_config["entity_types"].items():
                    entidades_validas.update(entidades.keys())

            # Remove entidades que não devem estar em metadados
            entidades_validas.discard("contato")
            entidades_validas.discard("telefone")
            entidades_validas.discard("nome_contato")

            return entidades_validas

        except Exception as e:
            logger.error(f"Erro ao obter entidades válidas: {e}")
            return set()
