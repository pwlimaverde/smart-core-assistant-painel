import re
from datetime import datetime
from typing import Any, Optional, cast, override

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone
from loguru import logger

from smart_core_assistant_painel.app.ui.clientes.models import Contato
from smart_core_assistant_painel.app.ui.operacional.models import AtendenteHumano

class StatusAtendimento(models.TextChoices):
    AGUARDANDO_INICIAL = "aguardando_inicial", "Aguardando Interação Inicial"
    EM_ANDAMENTO = "em_andamento", "Em Andamento"
    AGUARDANDO_CONTATO = "aguardando_contato", "Aguardando Contato"
    AGUARDANDO_ATENDENTE = "aguardando_atendente", "Aguardando Atendente"
    RESOLVIDO = "resolvido", "Resolvido"
    CANCELADO = "cancelado", "Cancelado"
    TRANSFERIDO = "transferido", "Transferido para Humano"

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
    id: models.AutoField = models.AutoField(
        primary_key=True, help_text="Chave primária do registro"
    )
    contato: models.ForeignKey[Contato] = models.ForeignKey(
        "clientes.Contato",
        on_delete=models.CASCADE,
        related_name="atendimentos",
        help_text="Contato vinculado ao atendimento",
    )
    status: models.CharField[str] = models.CharField(
        max_length=20,
        choices=StatusAtendimento.choices,
        default=StatusAtendimento.AGUARDANDO_INICIAL,
        help_text="Status atual do atendimento",
    )
    data_inicio: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True, help_text="Data de início do atendimento"
    )
    data_fim: models.DateTimeField[datetime | None] = models.DateTimeField(
        blank=True, null=True, help_text="Data de finalização do atendimento"
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
    atendente_humano: models.ForeignKey[Optional["operacional.AtendenteHumano"]] = models.ForeignKey(
        "operacional.AtendenteHumano",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="atendimentos",
        help_text="Atendente humano responsável pelo atendimento (se transferido)",
    )
    contexto_conversa: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Contexto atual da conversa (variáveis, estado, etc.)",
    )
    historico_status: models.JSONField[list[dict[str, Any]]] = models.JSONField(
        default=list, blank=True, help_text="Histórico de mudanças de status"
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

    class Meta:
        verbose_name = "Atendimento"
        verbose_name_plural = "Atendimentos"
        ordering = ["-data_inicio"]
        db_table = "oraculo_atendimento"

    @override
    def __str__(self) -> str:
        return f"Atendimento {self.id} - {self.contato.telefone}"

    def finalizar_atendimento(self, novo_status: str = "resolvido") -> None:
        self.status = novo_status
        self.data_fim = timezone.now()
        self.adicionar_historico_status(novo_status, "Atendimento finalizado")
        self.save()

    def adicionar_historico_status(self, novo_status: str, observacao: str = "") -> None:
        if not self.historico_status:
            self.historico_status = []
        self.historico_status.append(
            {
                "status": novo_status,
                "timestamp": timezone.now().isoformat(),
                "observacao": observacao,
            }
        )

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
        self, atendente_humano: AtendenteHumano, observacao: str = ""
    ) -> None:
        self.atendente_humano = atendente_humano
        self.status = StatusAtendimento.TRANSFERIDO
        self.adicionar_historico_status(
            "transferido",
            observacao or f"Transferido para {atendente_humano.nome}",
        )
        self.save()

    def carregar_historico_mensagens(
        self, excluir_mensagem_id: Optional[int] = None
    ) -> dict[str, Any]:
        try:
            mensagens_query: QuerySet["Mensagem"] = cast(
                QuerySet["Mensagem"], self.mensagens.all().order_by("timestamp")
            )
            if excluir_mensagem_id:
                mensagens_query = mensagens_query.exclude(id=excluir_mensagem_id)
            mensagens: list["Mensagem"] = list(mensagens_query)
            conteudo_mensagens: list[str] = []
            intents_detectados: list[dict[str, str]] = []
            entidades_extraidas: list[dict[str, str]] = []
            for mensagem in mensagens:
                if mensagem.conteudo:
                    conteudo_mensagens.append(mensagem.conteudo)
                if mensagem.intent_detectado:
                    for intent_dict in mensagem.intent_detectado:
                        if intent_dict not in intents_detectados:
                            intents_detectados.append(intent_dict)
                if mensagem.entidades_extraidas:
                    for entidade_dict in mensagem.entidades_extraidas:
                        if entidade_dict not in entidades_extraidas:
                            entidades_extraidas.append(entidade_dict)
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
                    data_formatada = atendimento_anterior.data_fim.strftime("%d/%m/%Y")
                    historico_atendimentos.append(
                        f"{data_formatada} - assunto tratado: {atendimento_anterior.assunto}"
                    )
            resultado = {
                "conteudo_mensagens": conteudo_mensagens,
                "intents_detectados": intents_detectados,
                "entidades_extraidas": entidades_extraidas,
                "historico_atendimentos": historico_atendimentos,
            }
            return resultado
        except Exception as e:
            logger.error(
                f"Erro ao carregar histórico de mensagens do atendimento {self.id}: {e}"
            )
            return {
                "conteudo_mensagens": [],
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
    conteudo: models.TextField[str] = models.TextField(help_text="Conteúdo da mensagem")
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
    resposta_bot: models.TextField[str | None] = models.TextField(
        blank=True, null=True, help_text="Resposta gerada pelo bot"
    )
    intent_detectado: models.JSONField[list[dict[str, str]]] = models.JSONField(
        default=list,
        blank=True,
        help_text="Intents detectados pelo processamento de NLP (formato: lista de dicionários como {'saudacao': 'Olá', 'pergunta': 'tudo bem?'})",
    )
    entidades_extraidas: models.JSONField[list[dict[str, str]]] = models.JSONField(
        default=list,
        blank=True,
        help_text="Entidades extraídas da mensagem (formato: lista de dicionários como {'pessoa': 'João Silva'})",
    )
    confianca_resposta: models.FloatField[float | None] = models.FloatField(
        blank=True,
        null=True,
        help_text="Nível de confiança da resposta do bot (0-1)",
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

        atendimento_ativo = Atendimento.objects.filter(
            contato=contato,
            status__in=[
                StatusAtendimento.AGUARDANDO_INICIAL,
                StatusAtendimento.EM_ANDAMENTO,
                StatusAtendimento.AGUARDANDO_CONTATO,
                StatusAtendimento.AGUARDANDO_ATENDENTE,
            ],
        ).first()

        if not atendimento_ativo:
            atendimento = Atendimento.objects.create(
                contato=contato,
                status=StatusAtendimento.EM_ANDAMENTO,
                contexto_conversa={
                    "canal": "whatsapp",
                    "primeira_interacao": True,
                    "sessao_iniciada": timezone.now().isoformat(),
                },
            )
            atendimento.adicionar_historico_status(
                StatusAtendimento.EM_ANDAMENTO,
                "Atendimento iniciado via WhatsApp",
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
                StatusAtendimento.AGUARDANDO_INICIAL,
                StatusAtendimento.EM_ANDAMENTO,
                StatusAtendimento.AGUARDANDO_CONTATO,
                StatusAtendimento.AGUARDANDO_ATENDENTE,
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

            if atendimento.status in StatusAtendimento.AGUARDANDO_INICIAL:
                atendimento.status = StatusAtendimento.EM_ANDAMENTO
                atendimento.adicionar_historico_status(
                    "em_andamento",
                    "Primeira mensagem recebida",
                )
                atendimento.save()

        return mensagem.id

    except Exception as e:
        logger.error(f"Erro ao processar mensagem WhatsApp: {e}")
        raise