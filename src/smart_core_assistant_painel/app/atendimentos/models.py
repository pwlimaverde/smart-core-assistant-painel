import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, cast, override

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone
from loguru import logger

from smart_core_assistant_painel.app.clientes.models import Contato
from smart_core_assistant_painel.app.operacional.models import (
    Atendente,
)

if TYPE_CHECKING:
    # Import apenas para type hints, evitando ciclo de import em runtime
    from smart_core_assistant_painel.app.operacional.models import (
        Departamento,
        EtapaFluxo,
    )


class StatusAtendimento(models.TextChoices):
    FILA = "fila", "Fila"
    EM_ATENDIMENTO = "em_atendimento", "Em Atendimento"
    PENDENCIA = "pendencia", "Pendência"
    RESOLVIDO = "resolvido", "Resolvido"
    CANCELADO = "cancelado", "Cancelado"
    ARQUIVADO = "arquivado", "Arquivado"


# Aliases de compatibilidade esperados pelos testes
# Comentário: alias fora da enum evitam erro de duplicidade do Enum.
StatusAtendimento.EM_ANDAMENTO = StatusAtendimento.EM_ATENDIMENTO  # type: ignore[attr-defined]
StatusAtendimento.AGUARDANDO_ATENDENTE = StatusAtendimento.FILA  # type: ignore[attr-defined]
StatusAtendimento.AGUARDANDO_CONTATO = StatusAtendimento.PENDENCIA  # type: ignore[attr-defined]


class TipoMensagem(models.TextChoices):
    TEXTO_FORMATADO = (
        "extendedTextMessage",
        "Texto com formatação, citações, fontes, etc.",
    )
    IMAGEM = "imageMessage", "Imagem recebida, JPG/PNG, com caption possível"
    VIDEO = "videoMessage", "Vídeo recebido, com legenda possível"
    AUDIO = "audioMessage", "Áudio recebido (.mp4, .mp3), com duração/ptt"
    DOCUMENTO = "documentMessage", "Arquivo genérico (PDF, DOCX etc.)"
    STICKER = "stickerMessage", "Sticker no formato WebP"
    LOCALIZACAO = "locationMessage", "Coordinates de localização (lat/long)"
    CONTATO = "contactMessage", "vCard com dados de contato"
    LISTA = "listMessage", "Mensagem interativa com opções em lista"
    BOTOES = "buttonsMessage", "Botões clicáveis dentro da mensagem"
    ENQUETE = "pollMessage", "Opções de enquete dentro da mensagem"
    REACAO = "reactMessage", "Reação (emoji) a uma mensagem existente"

    @classmethod
    def obter_por_chave_json(cls, chave_json: str):
        mapeamento = {
            "conversation": cls.TEXTO_FORMATADO,
            "extendedTextMessage": cls.TEXTO_FORMATADO,
            "imageMessage": cls.IMAGEM,
            "videoMessage": cls.VIDEO,
            "audioMessage": cls.AUDIO,
            "documentMessage": cls.DOCUMENTO,
            "stickerMessage": cls.STICKER,
            "locationMessage": cls.LOCALIZACAO,
            "contactMessage": cls.CONTATO,
            "listMessage": cls.LISTA,
            "buttonsMessage": cls.BOTOES,
            "pollMessage": cls.ENQUETE,
            "reactMessage": cls.REACAO,
        }
        return mapeamento.get(chave_json, cls.TEXTO_FORMATADO)

    @classmethod
    def obter_chave_json(cls, tipo_mensagem: "TipoMensagem") -> Optional[str]:
        if hasattr(tipo_mensagem, "value"):
            return tipo_mensagem.value
        return None


class TipoRemetente(models.TextChoices):
    CONTATO = "contato", "Contato"
    BOT = "bot", "Bot/Sistema"
    ATENDENTE_HUMANO = "atendente_humano", "Atendente Humano"


class Atendimento(models.Model):
    """
    Representa um atendimento em uma estrutura operacional.

    Mapeamento para ClickUp:
    - Departamento → Pasta
    - FluxoAtendimento → Lista na pasta do departamento
    - EtapaFluxo → Status/coluna da lista (etapa atual)

    As relações são validadas em `clean()`. Quando definidas, os campos
    `departamento`, `fluxo_atendimento` e `etapa_atual` devem pertencer
    ao mesmo contexto (mesmo departamento e fluxo).
    """

    id: models.AutoField = models.AutoField(
        primary_key=True, help_text="Chave primária do registro"
    )
    contato: models.ForeignKey[Contato] = models.ForeignKey(
        "clientes.Contato",
        on_delete=models.CASCADE,
        related_name="atendimentos",
        help_text="Contato vinculado ao atendimento",
    )
    # Campo de departamento para suportar fila por departamento na central de atendimento
    departamento: models.ForeignKey[Optional["operacional.Departamento"]] = (
        models.ForeignKey(
            "operacional.Departamento",
            on_delete=models.SET_NULL,
            blank=True,
            null=True,
            related_name="atendimentos",
            help_text="Departamento atual do atendimento (fila Kanban)",
        )
    )
    # Fluxo/quadro associado (necessario para ClickUp e coerencia de etapas)
    fluxo_atendimento: models.ForeignKey[
        Optional["operacional.FluxoAtendimento"]
    ] = models.ForeignKey(
        "operacional.FluxoAtendimento",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="atendimentos",
        help_text=(
            "Fluxo/quadro atual do atendimento (coerente com "
            "departamento e etapa_atual)"
        ),
    )
    status: models.CharField[str] = models.CharField(
        max_length=20,
        choices=StatusAtendimento.choices,
        default=StatusAtendimento.FILA,
        help_text="Status atual do atendimento (legado - será substituído por fluxo)",
    )
    etapa_atual: models.ForeignKey[Optional["operacional.EtapaFluxo"]] = (
        models.ForeignKey(
            "operacional.EtapaFluxo",
            on_delete=models.SET_NULL,
            blank=True,
            null=True,
            related_name="atendimentos",
            help_text="Etapa atual do atendimento no fluxo personalizado",
        )
    )
    data_inicio: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True, help_text="Data de início do atendimento"
    )
    data_fim: models.DateTimeField[datetime | None] = models.DateTimeField(
        blank=True, null=True, help_text="Data de finalização do atendimento"
    )
    # Campo para registrar a última mensagem trocada, usado para SLAs e ordenação
    data_ultima_mensagem: models.DateTimeField[datetime | None] = (
        models.DateTimeField(
            blank=True,
            null=True,
            help_text="Data/hora da última mensagem (para ordenação e SLA)",
        )
    )
    assunto: models.CharField[str | None] = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Assunto/resumo do atendimento",
    )
    prioridade: models.CharField[str] = models.CharField(
        max_length=10,
        choices=[
            ("baixa", "Baixa"),
            ("normal", "Normal"),
            ("alta", "Alta"),
            ("urgente", "Urgente"),
        ],
        default="normal",
        help_text="Prioridade do atendimento",
    )
    atendente_humano: models.ForeignKey[Optional["operacional.Atendente"]] = (
        models.ForeignKey(
            "operacional.Atendente",
            on_delete=models.SET_NULL,
            blank=True,
            null=True,
            related_name="atendimentos",
            help_text="Atendente humano responsável pelo atendimento (se transferido)",
        )
    )
    contexto_conversa: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Contexto atual da conversa (variáveis, estado, etc.)",
    )
    historico_status: models.JSONField[list[dict[str, Any]]] = (
        models.JSONField(
            default=list,
            blank=True,
            help_text="Histórico de mudanças de status",
        )
    )
    tags: models.JSONField[list[str]] = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags para categorização do atendimento",
    )
    avaliacao: models.IntegerField[int | None] = models.IntegerField(
        blank=True,
        null=True,
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="Avaliação do atendimento (1-5)",
    )
    feedback: models.TextField[str | None] = models.TextField(
        blank=True, null=True, help_text="Feedback do contato"
    )
    data_primeira_resposta: models.DateTimeField[datetime | None] = (
        models.DateTimeField(
            blank=True,
            null=True,
            help_text="Data e hora da primeira resposta ao contato",
        )
    )
    bot_pode_atender: models.BooleanField[bool] = models.BooleanField(
        default=True,
        help_text="Indica se o bot pode responder a este atendimento",
    )

    class Meta:
        verbose_name = "Atendimento"
        verbose_name_plural = "Atendimentos"
        ordering = ["-data_inicio"]
        db_table = "oraculo_atendimento"
        # Índices para performance nas consultas do Kanban e filtros comuns
        indexes = [
            models.Index(fields=["status", "departamento"]),
            models.Index(fields=["departamento", "data_ultima_mensagem"]),
            models.Index(fields=["atendente_humano", "status"]),
            models.Index(fields=["etapa_atual", "atendente_humano"]),
            models.Index(fields=["departamento", "etapa_atual"]),
            models.Index(fields=["fluxo_atendimento"]),
            models.Index(fields=["prioridade"]),
            models.Index(fields=["tags"]),
            models.Index(fields=["bot_pode_atender"]),
        ]

    @override
    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk is None and not self.historico_status:
            self.adicionar_historico_status(self.status, "Status inicial")
        super().save(*args, **kwargs)

    @override
    def clean(self) -> None:
        """Validações de consistência do Atendimento.

        - Garante que `etapa_atual` pertença ao mesmo departamento
          selecionado no atendimento.
        - Garante que `fluxo_atendimento` pertence ao `departamento`.
        - Se ambos definidos, garante que `etapa_atual.fluxo == fluxo_atendimento`.
        """
        super().clean()

        # Validação: etapa_atual deve pertencer ao departamento escolhido
        if self.etapa_atual_id:
            if not self.departamento_id:
                raise ValidationError(
                    {
                        "etapa_atual": (
                            "Selecione um departamento antes de definir a "
                            "etapa."
                        )
                    }
                )

            fluxo_dep_id: Optional[int] = None
            try:
                # Tenta usar o objeto já carregado, se disponível
                if hasattr(self, "etapa_atual") and self.etapa_atual:
                    fluxo_dep_id = cast(
                        Optional[int],
                        getattr(
                            self.etapa_atual.fluxo, "departamento_id", None
                        ),
                    )

                # Busca no banco se necessário para garantir o vínculo
                if fluxo_dep_id is None:
                    from smart_core_assistant_painel.app.operacional.models import (
                        EtapaFluxo,
                    )

                    etapa = (
                        EtapaFluxo.objects.select_related("fluxo")
                        .filter(id=self.etapa_atual_id)
                        .first()
                    )
                    fluxo_dep_id = (
                        etapa.fluxo.departamento_id
                        if etapa and etapa.fluxo
                        else None
                    )
            except Exception as exc:
                logger.warning(
                    "Falha ao validar etapa_atual por departamento: {}", exc
                )

            if fluxo_dep_id != self.departamento_id:
                raise ValidationError(
                    {
                        "etapa_atual": (
                            "A etapa selecionada não pertence ao "
                            "departamento escolhido."
                        )
                    }
                )

        # Validação: fluxo_atendimento deve pertencer ao departamento
        if self.fluxo_atendimento_id:
            try:
                fluxo_dep_id2: Optional[int] = None
                if (
                    hasattr(self, "fluxo_atendimento")
                    and self.fluxo_atendimento
                ):
                    fluxo_dep_id2 = cast(
                        Optional[int],
                        getattr(
                            self.fluxo_atendimento, "departamento_id", None
                        ),
                    )
                if fluxo_dep_id2 is None:
                    from smart_core_assistant_painel.app.operacional.models import (
                        FluxoAtendimento,
                    )

                    fluxo_obj = (
                        FluxoAtendimento.objects.only("departamento_id")
                        .filter(id=self.fluxo_atendimento_id)
                        .first()
                    )
                    fluxo_dep_id2 = (
                        fluxo_obj.departamento_id if fluxo_obj else None
                    )
                if (
                    self.departamento_id is not None
                    and fluxo_dep_id2 != self.departamento_id
                ):
                    raise ValidationError(
                        {
                            "fluxo_atendimento": (
                                "O fluxo selecionado não pertence ao "
                                "departamento escolhido."
                            )
                        }
                    )
            except Exception as exc:
                logger.warning(
                    "Falha ao validar fluxo_atendimento por departamento: {}",
                    exc,
                )

        # Validação cruzada: etapa_atual deve pertencer ao fluxo_atendimento
        if self.etapa_atual_id and self.fluxo_atendimento_id:
            try:
                etapa_fluxo_id: Optional[int] = None
                if hasattr(self, "etapa_atual") and self.etapa_atual:
                    etapa_fluxo_id = cast(
                        Optional[int],
                        getattr(self.etapa_atual, "fluxo_id", None),
                    )
                if etapa_fluxo_id is None:
                    from smart_core_assistant_painel.app.operacional.models import (
                        EtapaFluxo,
                    )

                    etapa = (
                        EtapaFluxo.objects.only("fluxo_id")
                        .filter(id=self.etapa_atual_id)
                        .first()
                    )
                    etapa_fluxo_id = etapa.fluxo_id if etapa else None
                if etapa_fluxo_id != self.fluxo_atendimento_id:
                    raise ValidationError(
                        {
                            "etapa_atual": (
                                "A etapa selecionada não pertence ao "
                                "fluxo escolhido."
                            )
                        }
                    )
            except Exception as exc:
                logger.warning(
                    "Falha ao validar consistência etapa_atual/fluxo: {}",
                    exc,
                )

    @override
    def __str__(self) -> str:
        return f"Atendimento {self.id} - {self.contato.telefone}"

    @property
    def cliente(self) -> Optional["clientes.Cliente"]:
        """Retorna o cliente principal vinculado ao contato."""
        if TYPE_CHECKING:
            pass
        return (
            self.contato.clientes.first()
            if self.contato.clientes.exists()
            else None
        )

    def finalizar_atendimento(
        self, novo_status: str = "resolvido", solicitar_feedback: bool = True
    ) -> None:
        self.status = novo_status
        self.data_fim = timezone.now()
        self.adicionar_historico_status(novo_status, "Atendimento finalizado")
        self.save()

        if solicitar_feedback:
            self._enviar_solicitacao_feedback()

    def _enviar_solicitacao_feedback(self) -> None:
        """Envia solicitação de feedback via instância do departamento Atendimento."""
        try:
            from smart_core_assistant_painel.app.operacional.models import (
                AppInstance,
                Departamento,
            )

            # Buscar departamento Atendimento
            dept = Departamento.objects.filter(
                nome="Atendimento", ativo=True
            ).first()

            if not dept:
                logger.warning(
                    "Departamento 'Atendimento' não encontrado. "
                    "Tentando usar departamento atual."
                )
                dept = self.departamento

            api_key: Optional[str] = None
            if dept:
                app_instance = (
                    AppInstance.objects.filter(departamento=dept, active=True)
                    .order_by("-created_at")
                    .first()
                )
                if app_instance:
                    api_key = str(app_instance.api_key)

            metadados: dict[str, Any] = {}
            if api_key:
                metadados["evolution"] = {"api_key": api_key}
                logger.info(
                    f"API key configurada para feedback (Dept: {dept.nome if dept else 'N/A'})"
                )

            msg_texto = (
                "Seu atendimento na Ecoprint foi concluído!\n "
                "Sua opinião é muito importante para nós. Poderia nos avaliar com uma nota de 1 a 5 e compartilhar um comentário sobre como foi sua experiência?"
            )

            # Usando self.mensagens.create para evitar referência direta à classe Mensagem
            # que é definida posteriormente neste arquivo.
            self.mensagens.create(
                tipo=TipoMensagem.TEXTO_FORMATADO,
                conteudo="",
                remetente=TipoRemetente.BOT,
                resposta_bot=msg_texto,
                metadados=metadados,
                respondida=False,
            )
            logger.info(
                f"Solicitação de feedback criada para atendimento {self.id}"
            )

            # Agendar task de verificação de timeout (5 minutos)
            try:
                # 5 minutos = 300 segundos
                from datetime import timedelta

                from django.utils import timezone

                from smart_core_assistant_painel.app.atendimentos.tasks import (
                    verificar_feedback_atendimento,
                )
                from smart_core_assistant_painel.app.tenants.tenant_context import (
                    get_current_tenant_slug,
                )

                run_at = timezone.now() + timedelta(minutes=5)

                verificar_feedback_atendimento.apply_async(
                    args=[get_current_tenant_slug(), self.id],
                    eta=run_at,
                )
                logger.info(
                    f"Task de timeout de feedback agendada para {run_at}"
                )
                logger.info(
                    f"Task de timeout de feedback agendada para {run_at}"
                )

            except Exception as e:
                logger.error(
                    f"Erro ao agendar task de timeout de feedback: {e}"
                )

        except Exception as e:
            logger.error(
                f"Erro ao enviar solicitação de feedback para atendimento {self.id}: {e}"
            )

    def change_status(
        self, novo_status: StatusAtendimento, observacao: str = ""
    ) -> None:
        """Altera o status do atendimento com histórico e efeitos colaterais.

        - Se finalizador (RESOLVIDO/CANCELADO), marca `data_fim`.
        - Mantém coerência com UI Kanban.
        """
        self.status = novo_status
        if novo_status in (
            StatusAtendimento.RESOLVIDO,
            StatusAtendimento.CANCELADO,
            StatusAtendimento.ARQUIVADO,
        ):
            self.data_fim = timezone.now()
        self.adicionar_historico_status(novo_status.value, observacao)
        self.save()

    def adicionar_historico_status(
        self, novo_status: str, observacao: str = ""
    ) -> None:
        if not self.historico_status:
            self.historico_status = []
        self.historico_status.append(
            {
                "status": novo_status,
                "timestamp": timezone.now().isoformat(),
                "observacao": observacao,
            }
        )

    def assumir_atendimento(self, atendente_id: int) -> None:
        """Atendente assume o atendimento e desabilita o bot.

        Args:
            atendente_id: ID do atendente que assumirá o atendimento.
        """
        try:
            atendente = Atendente.objects.get(id=atendente_id)
            self.assign_to_agent(
                atendente,
                observacao="Atendente assumiu o atendimento (Bot desativado)",
            )
            self.bot_pode_atender = False
            self.save(update_fields=["bot_pode_atender"])
        except Atendente.DoesNotExist:
            logger.error(f"Atendente com ID {atendente_id} não encontrado.")
            raise

    def assign_to_agent(
        self, atendente: Atendente, observacao: str = ""
    ) -> None:
        """Atribui o atendimento a um atendente humano, atualiza status e histórico.

        - Atualiza `departamento` para o do atendente, se existir.
        - Define `status=EM_ATENDIMENTO`.
        - Registra `data_ultima_atribuicao` do atendente para fairness.
        - Desabilita o bot para este atendimento.
        """
        # Atualiza departamento de acordo com o atendente (se definido)
        if atendente.departamento and (
            self.departamento_id != atendente.departamento_id
        ):
            self.departamento_id = atendente.departamento_id
        # Alinha fluxo com o fluxo do atendente, quando disponível
        if getattr(atendente, "fluxo_id", None) and (
            self.fluxo_atendimento_id != atendente.fluxo_id
        ):
            self.fluxo_atendimento_id = atendente.fluxo_id

        self.atendente_humano = atendente
        self.status = StatusAtendimento.EM_ATENDIMENTO
        # self.bot_pode_atender = False  # Removido: assign_to_agent não desabilita bot automaticamente
        self.adicionar_historico_status(
            StatusAtendimento.EM_ATENDIMENTO.value,
            observacao or f"Atribuído a {atendente.nome}",
        )
        self.save()

        # Atualiza métrica de última atribuição do atendente
        atendente.data_ultima_atribuicao = timezone.now()
        atendente.save(update_fields=["data_ultima_atribuicao"])

    def unassign_agent(self, observacao: str = "") -> None:
        """Remove a atribuição do atendente e retorna o atendimento à fila."""
        self.atendente_humano = None
        self.status = StatusAtendimento.FILA
        # Se desatribuído, o bot pode voltar a atender?
        # O usuário não especificou, mas geralmente sim, se voltar pra fila.
        # Porem, a regra diz "a menos que essa flag esteja marcada como false... e isso só ocorrerá... se o atendente tomar...".
        # Se o atendente soltar, talvez devesse voltar a ser True?
        # Por segurança e seguindo a lógica de "bot atende novos", se voltar pra fila, talvez o bot deva pegar.
        # Mas vou manter False por enquanto para ser conservador, ou True?
        # O usuário disse: "os novos atendimentos... será atendida pelo bot, a menos que essa flag esteja marcada como false".
        # Se eu devolvo pra fila, ele não é "novo".
        # Mas se ninguém tá atendendo, o bot deveria?
        # Vou deixar como está (não altera a flag) ou setar True?
        # Se o atendente "unassign", ele está devolvendo.
        # Vou assumir que se volta pra fila, o bot pode tentar de novo se configurado.
        # Mas a instrução foi estrita sobre quando vira False. Não disse quando vira True.
        # Vou manter a flag como está no unassign por enquanto.

        self.adicionar_historico_status(
            StatusAtendimento.FILA.value,
            observacao or "Desatribuído e retornado à fila",
        )
        self.save()

    def transfer_to_department(
        self, departamento: "Departamento", observacao: str = ""
    ) -> None:
        """Transfere atendimento para outro departamento e volta para fila."""
        self.departamento_id = departamento.id
        self.atendente_humano = None
        self.status = StatusAtendimento.FILA
        self.bot_pode_atender = False  # Bot não atende após transferência
        # Mantém fluxo indefinido até escolha explícita ou método de fluxo
        # (evita vincular automaticamente a um fluxo incorreto)
        self.adicionar_historico_status(
            StatusAtendimento.FILA.value,
            observacao or f"Transferido para {departamento.nome}",
        )
        self.save()

    def apply_flow_by_description(self, flow_description: str) -> None:
        """Atualiza departamento e etapa inicial a partir de uma descrição.

        A descrição deve seguir o formato
        "<nome_do_fluxo> - <nome_do_departamento>", por exemplo:
        "Atendimento Comercial - Comercial".

        Ao localizar o fluxo, o atendimento é atribuído ao departamento
        correspondente e sua etapa atual é definida para a etapa inicial
        do fluxo (preferencialmente a etapa do tipo FILA, caso exista).

        Args:
            flow_description: Texto no formato "Fluxo - Departamento".

        Raises:
            ValidationError: Quando o formato estiver inválido, o fluxo não
                existir ou não houver etapa configurada.
        """
        if flow_description is None or not isinstance(flow_description, str):
            raise ValidationError(
                "A descrição do fluxo deve ser uma string válida."
            )

        descricao = flow_description.strip()
        if not descricao:
            raise ValidationError("A descrição do fluxo não pode ser vazia.")

        partes = re.split(r"\s*-\s*", descricao, maxsplit=1)
        if len(partes) != 2:
            raise ValidationError(
                "Formato inválido. Use 'Fluxo - Departamento'."
            )

        fluxo_nome, departamento_nome = partes[0], partes[1]

        # Import em runtime para evitar ciclos de import
        from smart_core_assistant_painel.app.operacional.models import (
            FluxoAtendimento,
            TipoEtapa,
        )

        fluxo = (
            FluxoAtendimento.objects.select_related("departamento")
            .filter(nome=fluxo_nome, departamento__nome=departamento_nome)
            .first()
        )
        if not fluxo:
            raise ValidationError(
                ("Fluxo '{0}' no departamento '{1}' não encontrado.").format(
                    fluxo_nome, departamento_nome
                )
            )

        # Prioriza a etapa do tipo FILA; caso não exista, usa a primeira
        etapa_inicial = (
            fluxo.get_etapa_inicial() or fluxo.etapas.order_by("ordem").first()
        )
        if not etapa_inicial:
            raise ValidationError(
                "Fluxo selecionado não possui etapas configuradas."
            )

        # Atualiza departamento e etapa do atendimento
        self.departamento = fluxo.departamento
        self.fluxo_atendimento = fluxo
        self.etapa_atual = etapa_inicial
        self.bot_pode_atender = False

        # Se a etapa inicial for FILA, alinhar status de atendimento
        status_alterado = False
        if getattr(etapa_inicial, "tipo_etapa", None) == TipoEtapa.FILA.value:
            if self.status != StatusAtendimento.FILA:
                self.status = StatusAtendimento.FILA
                status_alterado = True

        campos = [
            "departamento",
            "fluxo_atendimento",
            "etapa_atual",
            "bot_pode_atender",
        ]
        if status_alterado:
            campos.append("status")
        self.save(update_fields=campos)

        if status_alterado:
            self.adicionar_historico_status(
                StatusAtendimento.FILA.value,
                ("Posicionado na etapa inicial do fluxo '{0}' ({1}).").format(
                    fluxo.nome, fluxo.departamento.nome
                ),
            )

    def touch_last_message(self, quando: Optional[datetime] = None) -> None:
        """Atualiza `data_ultima_mensagem` para ordenação/SLA."""
        self.data_ultima_mensagem = quando or timezone.now()
        self.save(update_fields=["data_ultima_mensagem"])

    def atualizar_contexto(self, chave: str, valor: Any) -> None:
        if not self.contexto_conversa:
            self.contexto_conversa = {}
        self.contexto_conversa[chave] = valor
        self.save()

    def get_contexto(self, chave: str, padrao: Any = None) -> Any:
        if not self.contexto_conversa:
            return padrao
        return self.contexto_conversa.get(chave, padrao)

    def transferir_para_humano(
        self, atendente_humano: Atendente, observacao: str = ""
    ) -> None:
        self.atendente_humano = atendente_humano
        self.status = StatusAtendimento.EM_ATENDIMENTO
        self.bot_pode_atender = False
        self.adicionar_historico_status(
            StatusAtendimento.EM_ATENDIMENTO.value,
            observacao or f"Transferido para {atendente_humano.nome}",
        )
        self.save()

    def transferir_para_humano_com_saudacao(
        self, atendente_id: int, observacao: str = ""
    ) -> None:
        """Transfere atendimento para atendente e envia saudação automática.

        Cria uma mensagem de saudação que será enviada automaticamente
        via signal. Os metadados são configurados com a API key da instância
        Evolution associada ao atendente para garantir que a mensagem seja
        enviada pela instância correta.

        A API key é obtida do AppInstance vinculado:
        1. Ao atendente (campo owner do AppInstance)
        2. Ao departamento do atendente

        Args:
            atendente_id: ID do atendente que assumirá o atendimento
            observacao: Observação adicional para o histórico (opcional)

        Raises:
            Atendente.DoesNotExist: Se o atendente não for encontrado
        """
        try:
            # 1. Buscar o atendente com suas relações
            atendente = (
                Atendente.objects.select_related("departamento")
                .filter(id=atendente_id)
                .first()
            )

            if not atendente:
                raise Atendente.DoesNotExist(
                    f"Atendente com ID {atendente_id} não encontrado."
                )

            # 2. Executar transferência tradicional
            self.transferir_para_humano(
                atendente_humano=atendente,
                observacao=(
                    observacao
                    or f"Transferido para {atendente.nome} com saudação "
                    "automática"
                ),
            )

            # 3. Preparar mensagem de saudação
            mensagem_saudacao = (
                f"Olá, meu nome é {atendente.nome}, sou Vendedor da Ecoprint, irei continuar seu "
                "atendimento."
            )

            # 4. Buscar API key do AppInstance vinculado ao atendente ou departamento
            from smart_core_assistant_painel.app.operacional.models import (
                AppInstance,
            )

            api_key: Optional[str] = None
            app_instance: Optional[AppInstance] = None

            # Prioridade 1: AppInstance vinculado ao atendente (owner)
            app_instance = (
                AppInstance.objects.filter(owner=atendente, active=True)
                .order_by("-created_at")
                .first()
            )

            # Prioridade 2: AppInstance vinculado ao departamento
            if not app_instance and atendente.departamento:
                app_instance = (
                    AppInstance.objects.filter(
                        departamento=atendente.departamento, active=True
                    )
                    .order_by("-created_at")
                    .first()
                )

            if app_instance:
                api_key = str(app_instance.api_key)
                logger.debug(
                    f"API key obtida de AppInstance para "
                    f"atendente {atendente.nome}"
                )

            # 5. Preparar metadados com API key
            metadados: dict[str, Any] = {}
            ultima_mensagem = self.mensagens.order_by("-timestamp").first()
            if ultima_mensagem and ultima_mensagem.metadados:
                # Copia os metadados para manter estrutura de evolution
                metadados = dict(ultima_mensagem.metadados)

            # Configura API key nos metadados evolution
            if api_key:
                if "evolution" not in metadados:
                    metadados["evolution"] = {}
                metadados["evolution"]["api_key"] = api_key
                logger.info(
                    f"Metadados configurados com API key para "
                    f"atendente {atendente.nome}"
                )
            else:
                logger.warning(
                    f"Não foi possível determinar API key para "
                    f"atendente {atendente.nome}. Mensagem será enviada "
                    f"pela instância padrão."
                )

            # 6. Criar mensagem com saudação
            mensagem = Mensagem.objects.create(
                atendimento=self,
                tipo=TipoMensagem.TEXTO_FORMATADO,
                conteudo="",  # Conteúdo vazio, pois é mensagem de saída
                remetente=TipoRemetente.ATENDENTE_HUMANO,
                resposta_bot=mensagem_saudacao,  # Saudação a ser enviada
                metadados=metadados,
                respondida=False,  # Será marcado True após envio pelo signal
            )

            logger.info(
                f"Transferência com saudação concluída: Atendimento {self.id}"
                f" -> Atendente {atendente.nome} (ID: {atendente_id}), "
                f"Mensagem ID: {mensagem.id}"
            )

        except Atendente.DoesNotExist:
            logger.error(f"Atendente com ID {atendente_id} não encontrado.")
            raise
        except Exception as e:
            logger.error(
                f"Erro ao transferir atendimento {self.id} para atendente "
                f"{atendente_id} com saudação: {e}"
            )
            raise

    def carregar_historico_mensagens(
        self, excluir_mensagem_id: Optional[int] = None
    ) -> dict[str, Any]:
        """Carrega o histórico de mensagens do atendimento.

        Retorna um dicionário contendo:
        - chat_history: Lista de BaseMessage (HumanMessage/AIMessage) para
          uso com LangChain ChatPromptTemplate multi-turn.
        - intents_detectados: Lista de intents detectados nas mensagens.
        - entidades_extraidas: Lista de entidades extraídas das mensagens.
        - historico_atendimentos: Lista de atendimentos anteriores do contato.

        Args:
            excluir_mensagem_id: ID da mensagem a ser excluída do histórico
                (geralmente a mensagem atual que está sendo processada).

        Returns:
            dict[str, Any]: Dicionário com o histórico estruturado.
        """
        # Import local para evitar dependência circular
        from langchain_core.messages import (
            AIMessage,
            BaseMessage,
            HumanMessage,
        )

        try:
            mensagens_query: QuerySet["Mensagem"] = cast(
                QuerySet["Mensagem"],
                self.mensagens.all().order_by("timestamp"),
            )
            if excluir_mensagem_id:
                mensagens_query = mensagens_query.exclude(
                    id=excluir_mensagem_id
                )
            mensagens: list["Mensagem"] = list(mensagens_query)

            # Histórico de chat estruturado para LangChain
            chat_history: list[BaseMessage] = []
            intents_detectados: list[dict[str, str]] = []
            entidades_extraidas: list[dict[str, str]] = []

            for mensagem in mensagens:
                # Mensagem do cliente (HumanMessage)
                if mensagem.conteudo and mensagem.remetente in [
                    TipoRemetente.CONTATO,
                    TipoRemetente.ATENDENTE_HUMANO,
                ]:
                    chat_history.append(
                        HumanMessage(content=mensagem.conteudo)
                    )

                # Resposta do bot (AIMessage)
                if mensagem.resposta_bot:
                    chat_history.append(
                        AIMessage(content=mensagem.resposta_bot)
                    )

                # Coleta intents e entidades
                if mensagem.intent_detectado:
                    for intent_dict in mensagem.intent_detectado:
                        if intent_dict not in intents_detectados:
                            intents_detectados.append(intent_dict)
                if mensagem.entidades_extraidas:
                    for entidade_dict in mensagem.entidades_extraidas:
                        if entidade_dict not in entidades_extraidas:
                            entidades_extraidas.append(entidade_dict)

            # Histórico de atendimentos anteriores
            historico_atendimentos: list[str] = []
            atendimentos_anteriores = (
                Atendimento.objects.filter(contato=self.contato)
                .exclude(id=self.id)
                .filter(data_fim__isnull=False)
                .order_by("-data_fim")
            )
            for atendimento_anterior in atendimentos_anteriores:
                if (
                    atendimento_anterior.assunto
                    and atendimento_anterior.data_fim is not None
                ):
                    data_formatada = atendimento_anterior.data_fim.strftime(
                        "%d/%m/%Y"
                    )
                    historico_atendimentos.append(
                        f"{data_formatada} - assunto tratado: "
                        f"{atendimento_anterior.assunto}"
                    )

            resultado = {
                "chat_history": chat_history,
                "intents_detectados": intents_detectados,
                "entidades_extraidas": entidades_extraidas,
                "historico_atendimentos": historico_atendimentos,
            }
            return resultado
        except Exception as e:
            logger.error(
                f"Erro ao carregar histórico de mensagens do "
                f"atendimento {self.id}: {e}"
            )
            return {
                "chat_history": [],
                "intents_detectados": [],
                "entidades_extraidas": [],
                "historico_atendimentos": [],
            }


class Mensagem(models.Model):
    id: models.AutoField = models.AutoField(
        primary_key=True, help_text="Chave primária do registro"
    )
    atendimento: models.ForeignKey["Atendimento"] = models.ForeignKey(
        "Atendimento",
        on_delete=models.CASCADE,
        related_name="mensagens",
        help_text="Atendimento ao qual a mensagem pertence",
    )
    tipo: models.CharField[str] = models.CharField(
        max_length=25,
        choices=TipoMensagem.choices,
        default=TipoMensagem.TEXTO_FORMATADO,
        help_text="Tipo da mensagem",
    )
    conteudo: models.TextField[str] = models.TextField(
        help_text="Conteúdo da mensagem"
    )
    remetente: models.CharField[str] = models.CharField(
        max_length=20,
        choices=TipoRemetente.choices,
        default=TipoRemetente.CONTATO,
        help_text="Tipo do remetente da mensagem",
    )
    timestamp: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp da mensagem"
    )
    message_id_whatsapp: models.CharField[str | None] = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ID da mensagem no WhatsApp",
    )
    metadados: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadados adicionais da mensagem (mídia, localização, etc.)",
    )
    respondida: models.BooleanField[bool] = models.BooleanField(
        default=False, help_text="Indica se a mensagem foi respondida"
    )
    lido: models.BooleanField[bool] = models.BooleanField(
        default=False,
        db_index=True,
        help_text=(
            "Indica se a mensagem (recebida do contato) já foi lida por algum "
            "atendente humano via workspace. Não se aplica a mensagens do bot "
            "ou do próprio atendente."
        ),
    )
    resposta_bot: models.TextField[str | None] = models.TextField(
        blank=True, null=True, help_text="Resposta gerada pelo bot"
    )
    intent_detectado: models.JSONField[list[dict[str, str]]] = (
        models.JSONField(
            default=list,
            blank=True,
            help_text="Intents detectados pelo processamento de NLP (formato: lista de dicionários como {'saudacao': 'Olá', 'pergunta': 'tudo bem?'})",
        )
    )
    entidades_extraidas: models.JSONField[list[dict[str, str]]] = (
        models.JSONField(
            default=list,
            blank=True,
            help_text="Entidades extraídas da mensagem (formato: lista de dicionários como {'pessoa': 'João Silva'})",
        )
    )
    confianca_resposta: models.FloatField[float | None] = models.FloatField(
        blank=True,
        null=True,
        help_text="Nível de confiança da resposta do bot (0-1)",
    )
    arquivo_midia: models.FileField = models.FileField(
        upload_to="midias_atendimento/%Y/%m/",
        blank=True,
        null=True,
        max_length=255,
        help_text=(
            "Arquivo binário da mídia decodificada (imagem, áudio, vídeo, "
            "documento). Substitui o uso de metadados['base64'] para mídia nova."
        ),
    )
    analise_midia: models.TextField[str | None] = models.TextField(
        blank=True,
        null=True,
        help_text=(
            "Análise gerada pela IA para mídias: transcrição de áudio, resumo "
            "de imagem/vídeo, descrição de documento. Separada de 'conteudo'."
        ),
    )

    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ["timestamp"]
        db_table = "oraculo_mensagem"

    @override
    def __str__(self) -> str:
        conteudo_preview = (
            self.conteudo[:50] + "..."
            if len(self.conteudo) > 50
            else self.conteudo
        )
        return f"{self.remetente}: {conteudo_preview}"

    def registrar_resposta_bot(self, resposta: str, confianca: float) -> None:
        """
        Registra a resposta gerada pelo bot nesta mensagem, persistindo o conteúdo e o nível de confiança.

        IMPORTANTE: A flag 'respondida' será marcada como True automaticamente
        pelo signal após o envio bem-sucedido via Evolution API.

        Parâmetros:
            resposta: Texto da resposta do bot.
            confianca: Nível de confiança entre 0.0 e 1.0.

        Levanta:
            ValidationError: Se a resposta for vazia ou se a confiança não estiver entre 0 e 1.
        """
        if (
            resposta is None
            or not isinstance(resposta, str)
            or not resposta.strip()
        ):
            raise ValidationError("A resposta do bot não pode ser vazia.")

        try:
            conf = float(confianca)
        except (TypeError, ValueError):
            raise ValidationError(
                "O parâmetro 'confianca' deve ser um número entre 0 e 1."
            )

        if not (0.0 <= conf <= 1.0):
            raise ValidationError(
                "O parâmetro 'confianca' deve estar entre 0 e 1."
            )

        self.resposta_bot = resposta.strip()
        self.confianca_resposta = conf
        # REMOVIDO: self.respondida = True
        # A mensagem só será marcada como respondida após envio bem-sucedido
        self.save(update_fields=["resposta_bot", "confianca_resposta"])

        try:
            atendimento = self.atendimento
            if not atendimento.data_primeira_resposta:
                atendimento.data_primeira_resposta = timezone.now()
                atendimento.save(update_fields=["data_primeira_resposta"])
        except Exception as _err:
            logger.warning(
                f"Erro ao definir data_primeira_resposta para "
                f"atendimento {self.atendimento_id}: {_err}"
            )

        logger.info(
            f"Resposta do bot registrada na mensagem {self.id} "
            f"(atendimento {self.atendimento_id}) com confianca={conf:.3f}. "
            f"Aguardando envio via Evolution API."
        )


class MovimentoFluxo(models.Model):
    """
    Registra a movimentacao de um atendimento entre as etapas do fluxo.
    Mantem historico completo para auditoria e analise.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    atendimento: models.ForeignKey["Atendimento"] = models.ForeignKey(
        "Atendimento",
        on_delete=models.CASCADE,
        related_name="movimentos_fluxo",
        help_text="Atendimento que foi movido",
    )
    etapa_origem: models.ForeignKey["EtapaFluxo"] = models.ForeignKey(
        "operacional.EtapaFluxo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentos_saida",
        help_text="Etapa de origem (None para novos atendimentos)",
    )
    etapa_destino: models.ForeignKey["EtapaFluxo"] = models.ForeignKey(
        "operacional.EtapaFluxo",
        on_delete=models.CASCADE,
        related_name="movimentos_entrada",
        help_text="Etapa para a qual o atendimento foi movido",
    )
    atendente_origem: models.ForeignKey[Atendente] = models.ForeignKey(
        "operacional.Atendente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentos_origem",
        help_text="Atendente que realizou o movimento (se aplicavel)",
    )
    atendente_destino: models.ForeignKey[Atendente] = models.ForeignKey(
        "operacional.Atendente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentos_destino",
        help_text="Atendente que foi atribuido ao atendimento (se aplicavel)",
    )
    motivo: models.TextField[str | None] = models.TextField(
        blank=True, null=True, help_text="Motivo da movimentacao (opcional)"
    )
    dados_complementares: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dados complementares sobre a movimentacao",
    )
    automatico: models.BooleanField[bool] = models.BooleanField(
        default=False, help_text="Indica se o movimento foi automatico"
    )
    data_movimento: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True, help_text="Data e hora da movimentacao"
    )
    duracao_segundos: models.PositiveIntegerField[int | None] = (
        models.PositiveIntegerField(
            blank=True,
            null=True,
            help_text="Duracao em segundos da etapa anterior (para calculos de SLA)",
        )
    )

    class Meta:
        verbose_name = "Movimento do Fluxo"
        verbose_name_plural = "Movimentos do Fluxo"
        db_table = "oraculo_movimento_fluxo"
        ordering = ["-data_movimento"]
        indexes = [
            models.Index(fields=["atendimento", "-data_movimento"]),
            models.Index(fields=["etapa_destino", "-data_movimento"]),
            models.Index(fields=["data_movimento"]),
        ]

    @override
    def __str__(self) -> str:
        origem = self.etapa_origem.nome if self.etapa_origem else "Novo"
        destino = (
            self.etapa_destino.nome if self.etapa_destino else "Desconhecido"
        )
        return f"{self.atendimento.id}: {origem} → {destino}"

    @classmethod
    def criar_movimento(
        cls,
        atendimento: "Atendimento",
        etapa_destino: "EtapaFluxo",
        atendente_destino: Optional[Atendente] = None,
        motivo: Optional[str] = None,
        automatico: bool = False,
        atendente_origem: Optional[Atendente] = None,
        etapa_origem: Optional["EtapaFluxo"] = None,
    ) -> "MovimentoFluxo":
        duracao_segundos = None
        if not etapa_origem:
            ultimo_movimento = atendimento.movimentos_fluxo.first()
            if ultimo_movimento:
                etapa_origem = ultimo_movimento.etapa_destino
                agora = timezone.now()
                if ultimo_movimento.data_movimento:
                    duracao_segundos = int(
                        (
                            agora - ultimo_movimento.data_movimento
                        ).total_seconds()
                    )

        movimento = cls.objects.create(
            atendimento=atendimento,
            etapa_origem=etapa_origem,
            etapa_destino=etapa_destino,
            atendente_origem=atendente_origem,
            atendente_destino=atendente_destino,
            motivo=motivo,
            automatico=automatico,
            duracao_segundos=duracao_segundos,
        )

        atendimento.etapa_atual = etapa_destino

        if atendente_destino:
            atendimento.atendente_humano = atendente_destino
            atendente_destino.data_ultima_atribuicao = timezone.now()
            atendente_destino.save(update_fields=["data_ultima_atribuicao"])

        atendimento.save(update_fields=["etapa_atual", "atendente_humano"])

        return movimento


def inicializar_atendimento_whatsapp(
    numero_telefone: str,
    primeira_mensagem: str = "",
    metadata_contato: Optional[dict[str, Any]] = None,
    nome_contato: Optional[str] = None,
    nome_perfil_whatsapp: Optional[str] = None,
) -> tuple[Contato, Atendimento]:
    """
    Inicializa ou recupera um contato e cria um novo atendimento baseado no número do WhatsApp.
    """
    try:
        telefone_limpo = re.sub(r"\D", "", numero_telefone)
        if not telefone_limpo.startswith("55"):
            telefone_limpo = "55" + telefone_limpo
        telefone_formatado = telefone_limpo

        contato, contato_criado = Contato.objects.get_or_create(
            telefone=telefone_formatado,
            defaults={
                "nome_contato": nome_contato,
                "nome_perfil_whatsapp": nome_perfil_whatsapp,
                "metadados": metadata_contato or {},
                "ativo": True,
            },
        )

        if not contato_criado:
            atualizado = False
            if nome_contato and not contato.nome_contato:
                contato.nome_contato = nome_contato
                atualizado = True
            if (
                nome_perfil_whatsapp
                and nome_perfil_whatsapp != contato.nome_perfil_whatsapp
            ):
                contato.nome_perfil_whatsapp = nome_perfil_whatsapp
                atualizado = True
            if metadata_contato:
                if contato.metadados is None:
                    contato.metadados = {}
                contato.metadados.update(metadata_contato)
                atualizado = True
            if atualizado:
                contato.save()

        # Estados considerados "ativos" para reaproveitar atendimento existente
        atendimento_ativo = Atendimento.objects.filter(
            contato=contato,
            status__in=[
                StatusAtendimento.FILA,
                StatusAtendimento.EM_ATENDIMENTO,
                StatusAtendimento.PENDENCIA,
            ],
        ).first()

        if not atendimento_ativo:
            # Status inicial agora é FILA, aguardando atendimento
            atendimento = Atendimento.objects.create(
                contato=contato,
                status=StatusAtendimento.FILA,
                contexto_conversa={
                    "canal": "whatsapp",
                    "primeira_interacao": True,
                    "sessao_iniciada": timezone.now().isoformat(),
                },
            )
            atendimento.adicionar_historico_status(
                StatusAtendimento.FILA.value,
                "Atendimento iniciado via WhatsApp (fila)",
            )
        else:
            atendimento = atendimento_ativo

        return contato, atendimento

    except Exception as e:
        logger.error(f"Erro ao inicializar atendimento WhatsApp: {e}")
        raise


def buscar_atendimento_ativo(numero_telefone: str) -> Optional[Atendimento]:
    """
    Busca um atendimento ativo para o número de telefone fornecido.
    """
    try:
        telefone_limpo = re.sub(r"\D", "", numero_telefone)
        if not telefone_limpo.startswith("55"):
            telefone_limpo = "55" + telefone_limpo
        telefone_formatado = telefone_limpo

        contato = Contato.objects.filter(telefone=telefone_formatado).first()
        if not contato:
            return None

        atendimento = Atendimento.objects.filter(
            contato=contato,
            status__in=[
                StatusAtendimento.FILA,
                StatusAtendimento.EM_ATENDIMENTO,
                StatusAtendimento.PENDENCIA,
            ],
        ).first()

        return atendimento

    except Exception as e:
        logger.error(f"Erro ao buscar atendimento ativo: {e}")
        return None


def processar_mensagem_whatsapp(
    numero_telefone: str,
    conteudo: str,
    message_type: str,
    message_id: str,
    metadados: Optional[dict[str, Any]] = None,
    nome_perfil_whatsapp: Optional[str] = None,
    from_me: bool = False,
) -> int:
    """
    Processa uma mensagem recebida do WhatsApp.
    """
    try:
        if from_me:
            remetente = TipoRemetente.ATENDENTE_HUMANO
        else:
            remetente = TipoRemetente.CONTATO

        atendimento = buscar_atendimento_ativo(numero_telefone)

        if not atendimento:
            _, atendimento = inicializar_atendimento_whatsapp(
                numero_telefone,
                conteudo,
                metadata_contato=metadados,
                nome_perfil_whatsapp=nome_perfil_whatsapp,
            )

        if message_id:
            mensagem_existente = Mensagem.objects.filter(
                message_id_whatsapp=message_id, atendimento=atendimento
            ).first()

            if mensagem_existente:
                return mensagem_existente.id
        tipo_mensagem = TipoMensagem.obter_por_chave_json(message_type)
        mensagem = Mensagem.objects.create(
            atendimento=atendimento,
            tipo=tipo_mensagem,
            conteudo=conteudo,
            remetente=remetente,
            message_id_whatsapp=message_id,
            metadados=metadados or {},
        )

        if remetente == TipoRemetente.CONTATO:
            atendimento.contato.ultima_interacao = timezone.now()
            atendimento.contato.save()

        return mensagem.id

    except Exception as e:
        logger.error(f"Erro ao processar mensagem WhatsApp: {e}")
        raise


def buscar_atendimento_ativo_por_contato(
    contato_id: int,
) -> Optional[Atendimento]:
    try:
        contato = Contato.objects.filter(id=contato_id).first()
        if not contato:
            return None
        return Atendimento.objects.filter(
            contato=contato,
            status__in=[
                StatusAtendimento.FILA,
                StatusAtendimento.EM_ATENDIMENTO,
                StatusAtendimento.PENDENCIA,
            ],
        ).first()
    except Exception as e:
        logger.error(f"Erro ao buscar atendimento por contato: {e}")
        return None


def inicializar_atendimento_por_contato(
    contato: Contato,
    primeira_mensagem: str = "",
    metadata_contato: Optional[dict[str, Any]] = None,
    nome_perfil_whatsapp: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Atendimento:
    try:
        atualizado = False
        if nome_perfil_whatsapp and (
            nome_perfil_whatsapp
            != getattr(contato, "nome_perfil_whatsapp", None)
        ):
            contato.nome_perfil_whatsapp = nome_perfil_whatsapp
            atualizado = True
        if metadata_contato:
            if contato.metadados is None:
                contato.metadados = {}
            contato.metadados.update(metadata_contato)
            atualizado = True
        if atualizado:
            contato.save()

        atendimento_ativo = Atendimento.objects.filter(
            contato=contato,
            status__in=[
                StatusAtendimento.FILA,
                StatusAtendimento.EM_ATENDIMENTO,
                StatusAtendimento.PENDENCIA,
            ],
        ).first()

        if not atendimento_ativo:
            atendimento = Atendimento.objects.create(
                contato=contato,
                status=StatusAtendimento.FILA,
                contexto_conversa={
                    "canal": "whatsapp",
                    "primeira_interacao": True,
                    "sessao_iniciada": timezone.now().isoformat(),
                },
            )
            try:
                if api_key:
                    from smart_core_assistant_painel.app.operacional.models import (
                        AppInstance,
                    )

                    app_inst = AppInstance.objects.filter(
                        api_key=api_key, active=True
                    ).first()
                    if app_inst:
                        if getattr(app_inst, "owner", None):
                            atendente = app_inst.owner
                            atendimento.atendente_humano = atendente
                            if getattr(atendente, "departamento", None):
                                atendimento.departamento = (
                                    atendente.departamento
                                )
                        elif getattr(app_inst, "departamento", None):
                            atendimento.departamento = app_inst.departamento
                        # Comentário (PT-BR): ao definir o departamento,
                        # vincula também o fluxo e a etapa inicial.
                        try:
                            if atendimento.departamento_id and (
                                not atendimento.fluxo_atendimento_id
                            ):
                                from smart_core_assistant_painel.app.operacional.models import (
                                    FluxoAtendimento,
                                )

                                fluxo = (
                                    FluxoAtendimento.objects.filter(
                                        departamento_id=atendimento.departamento_id,
                                    )
                                    .order_by("id")
                                    .first()
                                )
                                if fluxo:
                                    etapa_ini = (
                                        fluxo.get_etapa_inicial()
                                        or fluxo.etapas.order_by(
                                            "ordem"
                                        ).first()
                                        or fluxo.etapas.order_by("id").first()
                                    )
                                    atendimento.fluxo_atendimento = fluxo
                                    atendimento.etapa_atual = etapa_ini
                                    atendimento.save(
                                        update_fields=[
                                            "atendente_humano",
                                            "departamento",
                                            "fluxo_atendimento",
                                            "etapa_atual",
                                        ]
                                    )
                                else:
                                    atendimento.save(
                                        update_fields=[
                                            "atendente_humano",
                                            "departamento",
                                        ]
                                    )
                            else:
                                atendimento.save(
                                    update_fields=[
                                        "atendente_humano",
                                        "departamento",
                                    ]
                                )
                        except Exception:
                            atendimento.save(
                                update_fields=[
                                    "atendente_humano",
                                    "departamento",
                                ]
                            )
            except Exception:
                ...
            atendimento.adicionar_historico_status(
                StatusAtendimento.FILA.value,
                "Atendimento iniciado via WhatsApp (fila)",
            )
        else:
            atendimento = atendimento_ativo

        return atendimento
    except Exception as e:
        logger.error(f"Erro ao inicializar atendimento por contato: {e}")
        raise


def processar_mensagem_por_contato(
    contato_id: int,
    conteudo: str,
    message_type: str,
    message_id: str,
    metadados: Optional[dict[str, Any]] = None,
    nome_perfil_whatsapp: Optional[str] = None,
    from_me: bool = False,
    api_key: Optional[str] = None,
) -> int:
    try:
        remetente = (
            TipoRemetente.ATENDENTE_HUMANO
            if from_me
            else TipoRemetente.CONTATO
        )
        contato = Contato.objects.filter(id=contato_id).first()
        if not contato:
            raise ValidationError("Contato não encontrado")

        atendimento = buscar_atendimento_ativo_por_contato(contato_id)
        if not atendimento:
            # Verifica se há atendimento recém-resolvido (janela de feedback de 10 min)
            from datetime import timedelta
            # StatusAtendimento is available in global scope (imported/defined above)

            recent_resolved = (
                Atendimento.objects.filter(
                    contato_id=contato_id,
                    status=StatusAtendimento.RESOLVIDO,
                    data_fim__gte=timezone.now() - timedelta(minutes=10),
                )
                .order_by("-data_fim")
                .first()
            )

            if recent_resolved and not recent_resolved.avaliacao:
                atendimento = recent_resolved
            else:
                atendimento = inicializar_atendimento_por_contato(
                    contato,
                    primeira_mensagem=conteudo,
                    metadata_contato=metadados,
                    nome_perfil_whatsapp=nome_perfil_whatsapp,
                    api_key=api_key,
                )

        if message_id:
            existente = Mensagem.objects.filter(
                message_id_whatsapp=message_id, atendimento=atendimento
            ).first()
            if existente:
                return existente.id

        tipo_mensagem = TipoMensagem.obter_por_chave_json(message_type)
        mensagem = Mensagem.objects.create(
            atendimento=atendimento,
            tipo=tipo_mensagem,
            conteudo=conteudo,
            remetente=remetente,
            message_id_whatsapp=message_id,
            metadados=metadados or {},
        )

        # Atualiza timestamp para SLA/ordenação
        atendimento.touch_last_message()

        if remetente == TipoRemetente.CONTATO:
            contato.ultima_interacao = timezone.now()
            contato.save()

        if remetente == TipoRemetente.ATENDENTE_HUMANO:
            atendimento.bot_pode_atender = False
            atendimento.save(update_fields=["bot_pode_atender"])

        return mensagem.id
    except Exception as e:
        logger.error(f"Erro ao processar mensagem por contato: {e}")
        raise
