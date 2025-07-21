import json
import re
from typing import TYPE_CHECKING, Any, List, Optional

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from langchain.docstore.document import Document
from loguru import logger

# Para resolving Django related managers com MyPy
# mypy: disable-error-code="attr-defined"

if TYPE_CHECKING:
    pass


def validate_tag(value: str) -> None:
    """
    Valida se a tag está em formato válido.

    A tag deve estar em minúsculo, sem espaços, com no máximo 40 caracteres
    e conter apenas letras minúsculas, números e underscore.

    Args:
        value (str): Valor da tag a ser validada

    Raises:
        ValidationError: Se a tag não atender aos critérios de validação

    Examples:
        >>> validate_tag("minha_tag_123")  # válida
        >>> validate_tag("MinhaTag")       # inválida - maiúsculas
        >>> validate_tag("minha tag")      # inválida - espaço
    """
    if len(value) > 40:
        raise ValidationError('Tag deve ter no máximo 40 caracteres.')

    if ' ' in value:
        raise ValidationError('Tag não deve conter espaços.')

    if not value.islower():
        raise ValidationError('Tag deve conter apenas letras minúsculas.')

    # Opcional: validar se contém apenas letras, números e underscore
    if not re.match(r'^[a-z0-9_]+$', value):
        raise ValidationError(
            'Tag deve conter apenas letras minúsculas, números e underscore.')


class Treinamentos(models.Model):
    """
    Modelo para armazenar informações de treinamento de IA.

    Este modelo gerencia documentos de treinamento organizados por tags e grupos,
    permitindo armazenar e recuperar documentos LangChain serializados.

    Attributes:
        id: Chave primária do registro
        tag: Identificador único do treinamento
        grupo: Grupo ao qual o treinamento pertence
        _documentos: Lista de documentos LangChain serializados
        treinamento_finalizado: Status de finalização do treinamento
        data_criacao: Data de criação automática do treinamento
    """
    id: models.AutoField = models.AutoField(
        primary_key=True,
        help_text="Chave primária do registro"
    )
    tag: models.CharField = models.CharField(
        max_length=40,
        validators=[validate_tag],
        blank=False,
        null=False,
        help_text="Campo obrigatório para identificar o treinamento")
    grupo: models.CharField = models.CharField(
        max_length=40,
        validators=[validate_tag],
        blank=False,
        null=False,
        help_text="Campo obrigatório para identificar o grupo do treinamento")
    _documentos: models.JSONField = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="Lista de documentos LangChain serializados (campo privado)",
        db_column='documentos'
    )
    treinamento_finalizado: models.BooleanField = models.BooleanField(
        default=False,)
    data_criacao: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
        help_text="Data de criação do treinamento"
    )

    def save(self, *args, **kwargs):
        """
        Salva o modelo executando validação completa antes do salvamento.

        Args:
            *args: Argumentos posicionais do método save
            **kwargs: Argumentos nomeados do método save
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        """
        Validação personalizada do modelo.

        Valida que a tag não seja igual ao grupo e executa outras
        validações customizadas do modelo.

        Raises:
            ValidationError: Se houver violação das regras de validação
        """
        super().clean()

        # Validação customizada: tag não pode ser igual ao grupo
        if self.tag and self.grupo and self.tag == self.grupo:
            raise ValidationError({
                'grupo': 'O grupo não pode ser igual à tag.'
            })

    def __str__(self):
        """
        Retorna representação string do objeto.

        Returns:
            str: Tag do treinamento ou identificador padrão
        """
        return str(self.tag) if self.tag else f"Treinamento {self.id}"

    def get_conteudo_unificado(self) -> str:
        """
        Retorna todos os page_content da lista de documentos concatenados.

        Processa a lista de documentos LangChain serializados e extrai
        o conteúdo de texto (page_content) de cada documento, concatenando
        tudo em uma única string.

        Returns:
            str: Conteúdo unificado de todos os documentos, separados por quebras de linha duplas

        Note:
            Se não houver documentos ou se houver erro no processamento,
            retorna uma string vazia.
        """
        todos_page_contents = []

        if self._documentos:
            # documentos é sempre uma lista (JSONField)
            documentos_lista = self._documentos

            for i, doc in enumerate(documentos_lista):

                # Se o documento é uma string JSON, faz o parse
                if isinstance(doc, str):
                    doc_parsed = json.loads(doc)
                else:
                    doc_parsed = doc

                # Extrai o page_content do documento parseado
                if isinstance(doc_parsed,
                              dict) and 'page_content' in doc_parsed:
                    page_content = doc_parsed['page_content']
                    todos_page_contents.append(page_content)

        # Concatena todos os conteúdos em uma única string
        resultado = '\n\n'.join(str(content)
                                for content in todos_page_contents if content)
        return resultado

    def set_documentos(self, documentos: List[Document]) -> None:
        """
        Define uma lista de documentos LangChain, serializando-os para JSON.

        Este método processa uma lista de objetos Document do LangChain e os
        serializa adequadamente para armazenamento no campo JSONField do modelo.

        Args:
            documentos: Lista de objetos Document do LangChain a serem armazenados

        Raises:
            TypeError: Se algum item da lista não for um objeto Document válido
            ValueError: Se houver erro na serialização dos dados

        Example:
            >>> from langchain.docstore.document import Document
            >>> docs = [
            ...     Document(page_content="Texto 1", metadata={"source": "doc1.txt"}),
            ...     Document(page_content="Texto 2", metadata={"source": "doc2.txt"})
            ... ]
            >>> treinamento.set_documentos(docs)
        """
        if not documentos:
            self._documentos = []
            return

        try:
            serialized_docs = []

            for i, documento in enumerate(documentos):
                if not isinstance(documento, Document):
                    error_msg = f"Item na posição {i} não é um Document válido: {
                        type(documento)}"
                    logger.error(error_msg)
                    raise TypeError(error_msg)

                try:
                    # Serializa o Document para dicionário
                    doc_dict = documento.model_dump_json(
                        indent=2)
                    serialized_docs.append(doc_dict)

                except Exception as e:
                    error_msg = f"Erro ao serializar documento na posição {i}: {e}"
                    logger.error(error_msg)
                    raise ValueError(error_msg) from e

            self._documentos = serialized_docs
            logger.info(
                f"Documentos serializados com sucesso: {
                    len(serialized_docs)} documentos")

        except (TypeError, ValueError):
            # Re-raise erros já tratados
            raise
        except Exception as e:
            error_msg = f"Erro inesperado ao processar documentos: {e}"
            logger.error(error_msg)
            self._documentos = []
            raise ValueError(error_msg) from e

    def get_documentos(self) -> List[Document]:
        """
        Processa e converte documentos JSON para objetos Document.

        Desserializa a lista de documentos armazenados no campo JSONField
        e converte cada item para um objeto Document do LangChain.

        Returns:
            List[Document]: Lista de documentos processados. Retorna lista vazia
                          se não houver documentos ou se houver erro no processamento.

        Note:
            Em caso de erro na desserialização, o erro é logado e uma lista
            vazia é retornada para manter a estabilidade da aplicação.
        """
        documentos: list[Document] = []

        if not self._documentos:
            return documentos

        try:
            # documentos é sempre uma lista (JSONField)
            documentos_lista = self._documentos or []

            # Converte cada documento para objeto Document
            for doc_json in documentos_lista:
                if isinstance(doc_json, str):
                    # Se é string JSON, faz parse primeiro
                    documento = Document.model_validate_json(doc_json)
                else:
                    # Se já é dicionário, converte para Document
                    documento = Document(**doc_json)
                documentos.append(documento)

        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.error(
                f"Erro ao processar documentos do treinamento {
                    self.pk or 'novo'}: {e}")

        return documentos

    class Meta:
        verbose_name = "Treinamento"
        verbose_name_plural = "Treinamentos"


def validate_telefone(value: str) -> None:
    """
    Valida se o número de telefone está no formato correto.

    Verifica se o número tem entre 10 e 15 dígitos (formato brasileiro)
    e contém apenas números após remover caracteres não numéricos.

    Args:
        value (str): Número de telefone a ser validado

    Raises:
        ValidationError: Se o número não atender aos critérios de validação

    Examples:
        >>> validate_telefone("11999999999")   # válido
        >>> validate_telefone("+5511999999999") # válido
        >>> validate_telefone("123")           # inválido - muito curto
    """
    # Remove caracteres não numéricos
    telefone_limpo = re.sub(r'\D', '', value)

    # Verifica se tem pelo menos 10 dígitos (formato brasileiro)
    if len(telefone_limpo) < 10 or len(telefone_limpo) > 15:
        raise ValidationError(
            'Número de telefone deve ter entre 10 e 15 dígitos.')

    # Verifica se contém apenas números
    if not telefone_limpo.isdigit():
        raise ValidationError('Número de telefone deve conter apenas números.')


class AtendenteHumano(models.Model):
    """
    Modelo para armazenar informações dos atendentes humanos.

    Representa um atendente humano do sistema com informações completas
    incluindo dados de contato, credenciais e metadados profissionais.

    Attributes:
        id: Chave primária do registro
        telefone: Número de telefone único do atendente (usado como sessão)
        nome: Nome completo do atendente
        cargo: Cargo/função do atendente
        departamento: Departamento ao qual pertence
        email: E-mail corporativo do atendente
        usuario_sistema: Usuário do sistema (se aplicável)
        ativo: Status de atividade do atendente
        disponivel: Disponibilidade atual para atendimento
        max_atendimentos_simultaneos: Máximo de atendimentos simultâneos
        especialidades: Lista de especialidades/áreas de conhecimento
        horario_trabalho: Horário de trabalho em formato JSON
        data_cadastro: Data de cadastro no sistema
        ultima_atividade: Data da última atividade no sistema
        metadados: Informações adicionais do atendente
    """
    id: models.AutoField = models.AutoField(
        primary_key=True,
        help_text="Chave primária do registro"
    )
    telefone: models.CharField = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_telefone],
        null=True,
        blank=True,
        help_text="Número de telefone do atendente (usado como sessão única)"
    )
    nome: models.CharField = models.CharField(
        max_length=100,
        help_text="Nome completo do atendente"
    )
    cargo: models.CharField = models.CharField(
        max_length=100,
        help_text="Cargo/função do atendente"
    )
    departamento: models.CharField = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Departamento ao qual o atendente pertence"
    )
    email: models.EmailField = models.EmailField(
        blank=True,
        null=True,
        help_text="E-mail corporativo do atendente"
    )
    usuario_sistema: models.CharField = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Usuário do sistema para login (se aplicável)"
    )
    ativo: models.BooleanField = models.BooleanField(
        default=True,
        help_text="Status de atividade do atendente"
    )
    disponivel: models.BooleanField = models.BooleanField(
        default=True,
        help_text="Disponibilidade atual para receber novos atendimentos"
    )
    max_atendimentos_simultaneos: models.PositiveIntegerField = models.PositiveIntegerField(
        default=5, help_text="Máximo de atendimentos simultâneos permitidos")
    especialidades: models.JSONField = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de especialidades/áreas de conhecimento do atendente"
    )
    horario_trabalho: models.JSONField = models.JSONField(
        default=dict,
        blank=True,
        help_text="Horário de trabalho (ex: {'segunda': '08:00-18:00', 'terca': '08:00-18:00'})"
    )
    data_cadastro: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de cadastro no sistema"
    )
    ultima_atividade: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        help_text="Data da última atividade no sistema"
    )
    metadados: models.JSONField = models.JSONField(
        default=dict,
        blank=True,
        help_text="Informações adicionais do atendente (configurações, preferências, etc.)"
    )

    class Meta:
        verbose_name = "Atendente Humano"
        verbose_name_plural = "Atendentes Humanos"
        ordering = ['nome']

    def __str__(self):
        """
        Retorna representação string do atendente.

        Returns:
            str: Nome e cargo do atendente
        """
        return f"{self.nome} - {self.cargo}"

    def save(self, *args, **kwargs):
        """
        Salva o atendente normalizando o número de telefone.

        Normaliza o telefone para formato internacional (+55...) antes
        de salvar no banco de dados.

        Args:
            *args: Argumentos posicionais do método save
            **kwargs: Argumentos nomeados do método save
        """
        # Normaliza o número de telefone
        if self.telefone:
            # Remove caracteres não numéricos
            telefone_limpo = re.sub(r'\D', '', self.telefone)
            # Adiciona código do país se não tiver
            if not telefone_limpo.startswith('55'):
                telefone_limpo = '55' + telefone_limpo
            self.telefone = '+' + telefone_limpo

        super().save(*args, **kwargs)

    def clean(self) -> None:
        """
        Validação personalizada do modelo.

        Executa validações customizadas do modelo.

        Raises:
            ValidationError: Se houver violação das regras de validação
        """
        super().clean()

    def get_atendimentos_ativos(self) -> int:
        """
        Retorna a quantidade de atendimentos ativos do atendente.

        Returns:
            int: Número de atendimentos ativos
        """
        return self.atendimentos.filter(
            status__in=[
                StatusAtendimento.EM_ANDAMENTO,
                StatusAtendimento.AGUARDANDO_CLIENTE,
                StatusAtendimento.AGUARDANDO_ATENDENTE
            ]
        ).count()

    def pode_receber_atendimento(self) -> bool:
        """
        Verifica se o atendente pode receber um novo atendimento.

        Considera se está ativo, disponível e se não excedeu o limite
        de atendimentos simultâneos.

        Returns:
            bool: True se pode receber atendimento, False caso contrário
        """
        if not self.ativo or not self.disponivel:
            return False

        atendimentos_ativos = self.get_atendimentos_ativos()
        return atendimentos_ativos < self.max_atendimentos_simultaneos

    def adicionar_especialidade(self, especialidade: str) -> None:
        """
        Adiciona uma especialidade à lista de especialidades do atendente.

        Args:
            especialidade (str): Especialidade a ser adicionada
        """
        if not self.especialidades:
            self.especialidades = []

        if especialidade not in self.especialidades:
            self.especialidades.append(especialidade)
            self.save()

    def remover_especialidade(self, especialidade: str) -> None:
        """
        Remove uma especialidade da lista de especialidades do atendente.

        Args:
            especialidade (str): Especialidade a ser removida
        """
        if self.especialidades and especialidade in self.especialidades:
            self.especialidades.remove(especialidade)
            self.save()


class Cliente(models.Model):
    """
    Modelo para armazenar informações dos clientes.

    Representa um cliente do sistema com informações básicas como
    telefone, nome e metadados. O telefone é usado como identificador único.

    Attributes:
        id: Chave primária do registro
        telefone: Número de telefone único do cliente (formato internacional)
        nome: Nome do cliente (opcional)
        data_cadastro: Data de cadastro automática
        ultima_interacao: Data da última interação (atualizada automaticamente)
        ativo: Status de atividade do cliente
        metadados: Informações adicionais em formato JSON
    """
    id: models.AutoField = models.AutoField(
        primary_key=True,
        help_text="Chave primária do registro"
    )
    telefone: models.CharField = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_telefone],
        help_text="Número de telefone do cliente (formato: +5511999999999)"
    )
    nome: models.CharField = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Nome do cliente"
    )
    data_cadastro: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de cadastro do cliente"
    )
    ultima_interacao: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        help_text="Data da última interação"
    )
    ativo: models.BooleanField = models.BooleanField(
        default=True,
        help_text="Status de atividade do cliente"
    )
    metadados = models.JSONField(
        default=dict,
        blank=True,
        help_text="Informações adicionais do cliente"
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['-ultima_interacao']

    def __str__(self):
        """
        Retorna representação string do cliente.

        Returns:
            str: Nome do cliente (ou 'Cliente') seguido do telefone
        """
        return f"{self.nome or 'Cliente'} ({self.telefone})"

    def save(self, *args, **kwargs):
        """
        Salva o cliente normalizando o número de telefone.

        Normaliza o telefone para formato internacional (+55...) antes
        de salvar no banco de dados.

        Args:
            *args: Argumentos posicionais do método save
            **kwargs: Argumentos nomeados do método save
        """
        # Normaliza o número de telefone
        if self.telefone:
            # Remove caracteres não numéricos
            telefone_limpo = re.sub(r'\D', '', self.telefone)
            # Adiciona código do país se não tiver
            if not telefone_limpo.startswith('55'):
                telefone_limpo = '55' + telefone_limpo
            self.telefone = '+' + telefone_limpo

        super().save(*args, **kwargs)


class StatusAtendimento(models.TextChoices):
    """
    Enum para definir os estados possíveis do atendimento.

    Define todos os status que um atendimento pode ter durante seu ciclo de vida,
    desde o início até a finalização.
    """
    AGUARDANDO_INICIAL = 'aguardando_inicial', 'Aguardando Interação Inicial'
    EM_ANDAMENTO = 'em_andamento', 'Em Andamento'
    AGUARDANDO_CLIENTE = 'aguardando_cliente', 'Aguardando Cliente'
    AGUARDANDO_ATENDENTE = 'aguardando_atendente', 'Aguardando Atendente'
    RESOLVIDO = 'resolvido', 'Resolvido'
    CANCELADO = 'cancelado', 'Cancelado'
    TRANSFERIDO = 'transferido', 'Transferido para Humano'


class TipoMensagem(models.TextChoices):
    """
    Enum para definir os tipos de mensagem disponíveis no sistema.

    Define todos os tipos de conteúdo que podem ser enviados e recebidos
    através dos canais de comunicação, baseado nos tipos suportados pela API.
    """
    TEXTO_FORMATADO = 'extendedTextMessage', 'Texto com formatação, citações, fontes, etc.'
    IMAGEM = 'imageMessage', 'Imagem recebida, JPG/PNG, com caption possível'
    VIDEO = 'videoMessage', 'Vídeo recebido, com legenda possível'
    AUDIO = 'audioMessage', 'Áudio recebido (.mp4, .mp3), com duração/ptt'
    DOCUMENTO = 'documentMessage', 'Arquivo genérico (PDF, DOCX etc.)'
    STICKER = 'stickerMessage', 'Sticker no formato WebP'
    LOCALIZACAO = 'locationMessage', 'Coordinates de localização (lat/long)'
    CONTATO = 'contactMessage', 'vCard com dados de contato'
    LISTA = 'listMessage', 'Mensagem interativa com opções em lista'
    BOTOES = 'buttonsMessage', 'Botões clicáveis dentro da mensagem'
    ENQUETE = 'pollMessage', 'Opções de enquete dentro da mensagem'
    REACAO = 'reactMessage', 'Reação (emoji) a uma mensagem existente'

    @classmethod
    def obter_por_chave_json(cls, chave_json: Optional[str]):
        """
        Retorna o tipo de mensagem baseado na chave JSON recebida.

        Args:
            chave_json (Optional[str]): Chave JSON do tipo de mensagem (ex: 'extendedTextMessage') ou None

        Returns:
            Optional[TipoMensagem]: Tipo de mensagem correspondente ou None se não encontrado ou se chave_json for None

        Examples:
            >>> TipoMensagem.obter_por_chave_json('extendedTextMessage')
            TipoMensagem.TEXTO_FORMATADO
            >>> TipoMensagem.obter_por_chave_json('imageMessage')
            TipoMensagem.IMAGEM
            >>> TipoMensagem.obter_por_chave_json(None)
            None
        """
        # Verifica se chave_json é None
        if chave_json is None:
            return None

        # Mapeamento direto das chaves JSON para os tipos
        mapeamento = {
            'extendedTextMessage': cls.TEXTO_FORMATADO,
            'imageMessage': cls.IMAGEM,
            'videoMessage': cls.VIDEO,
            'audioMessage': cls.AUDIO,
            'documentMessage': cls.DOCUMENTO,
            'stickerMessage': cls.STICKER,
            'locationMessage': cls.LOCALIZACAO,
            'contactMessage': cls.CONTATO,
            'listMessage': cls.LISTA,
            'buttonsMessage': cls.BOTOES,
            'pollMessage': cls.ENQUETE,
            'reactMessage': cls.REACAO,
        }
        return mapeamento.get(chave_json)

    @classmethod
    def obter_chave_json(cls, tipo_mensagem):
        """
        Retorna a chave JSON correspondente ao tipo de mensagem.

        Args:
            tipo_mensagem: Tipo de mensagem do enum

        Returns:
            str: Chave JSON correspondente ou None se não encontrado

        Examples:
            >>> TipoMensagem.obter_chave_json(TipoMensagem.TEXTO_FORMATADO)
            'extendedTextMessage'
            >>> TipoMensagem.obter_chave_json(TipoMensagem.IMAGEM)
            'imageMessage'
        """
        # Como o valor já é a chave JSON (primeiro elemento da tupla), retorna
        # diretamente
        if hasattr(tipo_mensagem, 'value'):
            return tipo_mensagem.value
        return None


class TipoRemetente(models.TextChoices):
    """
    Enum para definir os tipos de remetente das mensagens.

    Define quem enviou a mensagem para controle do fluxo de interação
    entre cliente, bot e atendente humano.
    """
    CLIENTE = 'cliente', 'Cliente'
    BOT = 'bot', 'Bot/Sistema'
    ATENDENTE_HUMANO = 'atendente_humano', 'Atendente Humano'


class Atendimento(models.Model):
    """
    Modelo para controlar o fluxo de atendimento.

    Representa um atendimento completo com controle de status, histórico,
    contexto da conversa e metadados associados.

    Attributes:
        id: Chave primária do registro
        cliente: Cliente vinculado ao atendimento
        status: Status atual do atendimento
        data_inicio: Data de início do atendimento
        data_fim: Data de finalização do atendimento
        assunto: Assunto/resumo do atendimento
        prioridade: Prioridade do atendimento
        atendente_humano: Nome do atendente humano (se transferido)
        contexto_conversa: Contexto atual da conversa
        historico_status: Histórico de mudanças de status
        tags: Tags para categorização do atendimento
        avaliacao: Avaliação do atendimento (1-5)
        feedback: Feedback do cliente
    """
    id: models.AutoField = models.AutoField(
        primary_key=True,
        help_text="Chave primária do registro"
    )
    cliente: models.ForeignKey = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='atendimentos',
        help_text="Cliente vinculado ao atendimento"
    )
    status: models.CharField = models.CharField(
        max_length=20,
        choices=StatusAtendimento.choices,
        default=StatusAtendimento.AGUARDANDO_INICIAL,
        help_text="Status atual do atendimento"
    )
    data_inicio: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de início do atendimento"
    )
    data_fim: models.DateTimeField = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data de finalização do atendimento"
    )
    assunto: models.CharField = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Assunto/resumo do atendimento"
    )
    prioridade: models.CharField = models.CharField(
        max_length=10,
        choices=[
            ('baixa', 'Baixa'),
            ('normal', 'Normal'),
            ('alta', 'Alta'),
            ('urgente', 'Urgente')
        ],
        default='normal',
        help_text="Prioridade do atendimento"
    )
    atendente_humano: models.ForeignKey = models.ForeignKey(
        AtendenteHumano,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='atendimentos',
        help_text="Atendente humano responsável pelo atendimento (se transferido)")
    contexto_conversa: models.JSONField = models.JSONField(
        default=dict,
        blank=True,
        help_text="Contexto atual da conversa (variáveis, estado, etc.)"
    )
    historico_status: models.JSONField = models.JSONField(
        default=list,
        blank=True,
        help_text="Histórico de mudanças de status"
    )
    tags: models.JSONField = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags para categorização do atendimento"
    )
    avaliacao: models.IntegerField = models.IntegerField(
        blank=True,
        null=True,
        choices=[(i, i) for i in range(1, 6)],
        help_text="Avaliação do atendimento (1-5)"
    )
    feedback: models.TextField = models.TextField(
        blank=True,
        null=True,
        help_text="Feedback do cliente"
    )

    class Meta:
        verbose_name = "Atendimento"
        verbose_name_plural = "Atendimentos"
        ordering = ['-data_inicio']

    def __str__(self):
        """
        Retorna representação string do atendimento.

        Returns:
            str: ID do atendimento, telefone do cliente e status atual
        """
        return f"Atendimento {
            self.id} - {
            self.cliente.telefone} ({
            self.get_status_display()})"

    def finalizar_atendimento(
            self,
            novo_status: str = StatusAtendimento.RESOLVIDO) -> None:
        """
        Finaliza o atendimento alterando o status e registrando a data de fim.

        Args:
            novo_status: Status final do atendimento (padrão: RESOLVIDO)
        """
        self.status = novo_status
        self.data_fim = timezone.now()
        self.adicionar_historico_status(novo_status, "Atendimento finalizado")
        self.save()

    def adicionar_historico_status(
            self,
            novo_status: str,
            observacao: str = "") -> None:
        """
        Adiciona entrada no histórico de status.

        Args:
            novo_status: Novo status do atendimento
            observacao (str): Observação sobre a mudança de status (opcional)
        """
        if not self.historico_status:
            self.historico_status = []

        self.historico_status.append({
            'status': novo_status,
            'timestamp': timezone.now().isoformat(),
            'observacao': observacao
        })

    def atualizar_contexto(self, chave: str, valor: Any) -> None:
        """
        Atualiza uma chave no contexto da conversa.

        Args:
            chave: Chave a ser atualizada no contexto
            valor: Valor a ser armazenado
        """
        if not self.contexto_conversa:
            self.contexto_conversa = {}

        self.contexto_conversa[chave] = valor
        self.save()

    def get_contexto(self, chave: str, padrao: Any = None) -> Any:
        """
        Recupera um valor do contexto da conversa.

        Args:
            chave: Chave a ser recuperada do contexto
            padrao: Valor padrão se a chave não existir (opcional)

        Returns:
            Valor armazenado na chave ou valor padrão
        """
        if not self.contexto_conversa:
            return padrao

        return self.contexto_conversa.get(chave, padrao)

    def transferir_para_humano(self,
                               atendente_humano: 'AtendenteHumano',
                               observacao: str = "") -> None:
        """
        Transfere o atendimento para um atendente humano específico.

        Args:
            atendente_humano (AtendenteHumano): Atendente que receberá o atendimento
            observacao (str): Observação sobre a transferência (opcional)

        Raises:
            ValidationError: Se o atendente não pode receber o atendimento
        """
        if not atendente_humano.pode_receber_atendimento():
            raise ValidationError(
                f"O atendente {atendente_humano.nome} não pode receber novos atendimentos. "
                f"Motivos possíveis: inativo, indisponível ou limite de atendimentos atingido."
            )

        self.atendente_humano = atendente_humano
        self.status = StatusAtendimento.TRANSFERIDO
        self.adicionar_historico_status(
            StatusAtendimento.TRANSFERIDO,
            observacao or f"Transferido para {atendente_humano.nome}"
        )
        self.save()

    def liberar_atendente_humano(self, observacao: str = "") -> None:
        """
        Remove a atribuição do atendente humano do atendimento.

        Args:
            observacao (str): Observação sobre a liberação (opcional)
        """
        if self.atendente_humano:
            nome_anterior = self.atendente_humano.nome
            self.atendente_humano = None
            self.adicionar_historico_status(
                self.status,
                observacao or f"Liberado do atendente {nome_anterior}"
            )
            self.save()

    def carregar_historico_mensagens(
            self, excluir_mensagem_id: Optional[int] = None) -> dict[str, Any]:
        """
        Carrega o histórico completo de todas as mensagens do atendimento.

        Args:
            excluir_mensagem_id (Optional[int]): ID da mensagem a ser excluída do histórico
                (útil para excluir a mensagem atual ao analisar contexto)

        Returns:
            dict: Dicionário contendo:
                - 'conteudo_mensagens': Lista de strings com o conteúdo das mensagens
                - 'intents_detectados': Set com todos os intents únicos detectados
                - 'entidades_extraidas': Set com todas as entidades únicas extraídas

        Example:
            >>> # Para carregar histórico completo
            >>> historico = atendimento.carregar_historico_mensagens()
            >>>
            >>> # Para carregar histórico excluindo mensagem atual
            >>> historico = atendimento.carregar_historico_mensagens(excluir_mensagem_id=123)
            >>> print(f"Total de mensagens: {len(historico['conteudo_mensagens'])}")
            >>> print(f"Intents únicos: {historico['intents_detectados']}")
            >>> print(f"Entidades únicas: {historico['entidades_extraidas']}")
        """
        try:
            # Busca todas as mensagens do atendimento ordenadas por timestamp
            # (mais antigas primeiro)
            mensagens_query = self.mensagens.all().order_by('timestamp')

            # Exclui mensagem específica se solicitado
            if excluir_mensagem_id:
                mensagens_query = mensagens_query.exclude(
                    id=excluir_mensagem_id)

            mensagens = mensagens_query

            # Inicializa as estruturas de dados
            conteudo_mensagens = []
            intents_detectados = set()
            entidades_extraidas = set()

            # Processa cada mensagem
            for mensagem in mensagens:
                # Adiciona conteúdo da mensagem
                if mensagem.conteudo:
                    conteudo_mensagens.append(mensagem.conteudo)

                # Processa intents detectados
                if mensagem.intent_detectado:
                    # Espera uma lista de dicionários no formato
                    # {"saudacao": "Olá", "pergunta": "tudo bem?"}
                    if isinstance(mensagem.intent_detectado, list):
                        for intent_dict in mensagem.intent_detectado:
                            if isinstance(intent_dict, dict):
                                # Formato padrão: {"saudacao": "Olá"} -
                                # pega todos os valores dos intents
                                for tipo_intent, valor_intent in intent_dict.items():
                                    if valor_intent and str(
                                            valor_intent).strip():
                                        intents_detectados.add(
                                            f"{tipo_intent}: {valor_intent}")
                    else:
                        # Se não é uma lista, loga um aviso
                        logger.warning(
                            f"Intent detectado da mensagem {
                                mensagem.id} não está no formato esperado (lista de dicionários): {
                                type(
                                    mensagem.intent_detectado)}")

                # Processa entidades extraídas
                if mensagem.entidades_extraidas:
                    # Espera sempre uma lista de dicionários no formato
                    # {"tipo": "valor"}
                    if isinstance(mensagem.entidades_extraidas, list):
                        for entidade_dict in mensagem.entidades_extraidas:
                            if isinstance(entidade_dict, dict):
                                # Formato padrão: {"pessoa": "João Silva"} -
                                # pega todos os valores
                                for chave, valor in entidade_dict.items():
                                    if valor and str(valor).strip():
                                        entidades_extraidas.add(str(valor))
                    else:
                        # Se não é uma lista, loga um aviso
                        logger.warning(
                            f"Entidades extraídas da mensagem {
                                mensagem.id} não está no formato esperado (lista de dicionários): {
                                type(
                                    mensagem.entidades_extraidas)}")

            # Remove strings vazias das entidades
            entidades_extraidas.discard('')
            entidades_extraidas.discard('None')
            entidades_extraidas.discard('null')

            resultado = {
                'conteudo_mensagens': conteudo_mensagens,
                'intents_detectados': intents_detectados,
                'entidades_extraidas': entidades_extraidas
            }

            logger.info(
                f"Histórico carregado para atendimento {self.id}: "
                f"{len(conteudo_mensagens)} mensagens, "
                f"{len(intents_detectados)} intents únicos, "
                f"{len(entidades_extraidas)} entidades únicas"
                f"{f' (excluindo mensagem {excluir_mensagem_id})' if excluir_mensagem_id else ''}"
            )

            return resultado

        except Exception as e:
            logger.error(
                f"Erro ao carregar histórico de mensagens do atendimento {
                    self.id}: {e}")
            return {
                'conteudo_mensagens': [],
                'intents_detectados': set(),
                'entidades_extraidas': set()
            }


class Mensagem(models.Model):
    """
    Modelo para armazenar todas as mensagens da conversa.

    Representa uma mensagem individual dentro de um atendimento, incluindo
    metadados, tipo de conteúdo e informações de processamento.

    Attributes:
        id: Chave primária do registro
        atendimento: Atendimento ao qual a mensagem pertence
        tipo: Tipo da mensagem (texto, imagem, áudio, etc.)
        conteudo: Conteúdo textual da mensagem
        remetente: Tipo do remetente (cliente, bot, atendente_humano)
        timestamp: Data e hora da mensagem
        message_id_whatsapp: ID da mensagem no WhatsApp (se aplicável)
        metadados: Metadados adicionais da mensagem
        respondida: Indica se a mensagem foi respondida
        resposta_bot: Resposta gerada pelo bot
        intent_detectado: Intent detectado pelo processamento de NLP
        entidades_extraidas: Entidades extraídas da mensagem
        confianca_resposta: Nível de confiança da resposta do bot
    """
    id: models.AutoField = models.AutoField(
        primary_key=True,
        help_text="Chave primária do registro"
    )
    atendimento: models.ForeignKey = models.ForeignKey(
        Atendimento,
        on_delete=models.CASCADE,
        related_name='mensagens',
        help_text="Atendimento ao qual a mensagem pertence"
    )
    tipo: models.CharField = models.CharField(
        max_length=25,
        choices=TipoMensagem.choices,
        default=TipoMensagem.TEXTO_FORMATADO,
        help_text="Tipo da mensagem"
    )
    conteudo: models.TextField = models.TextField(
        help_text="Conteúdo da mensagem"
    )
    remetente: models.CharField = models.CharField(
        max_length=20,
        choices=TipoRemetente.choices,
        default=TipoRemetente.CLIENTE,
        help_text="Tipo do remetente da mensagem"
    )
    timestamp: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp da mensagem"
    )
    message_id_whatsapp: models.CharField = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ID da mensagem no WhatsApp"
    )
    metadados = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadados adicionais da mensagem (mídia, localização, etc.)"
    )
    respondida: models.BooleanField = models.BooleanField(
        default=False,
        help_text="Indica se a mensagem foi respondida"
    )
    resposta_bot: models.TextField = models.TextField(
        blank=True,
        null=True,
        help_text="Resposta gerada pelo bot"
    )
    intent_detectado = models.JSONField(
        default=list,
        blank=True,
        help_text="Intents detectados pelo processamento de NLP (formato: lista de dicionários como {'saudacao': 'Olá', 'pergunta': 'tudo bem?'})"
    )
    entidades_extraidas = models.JSONField(
        default=list,
        blank=True,
        help_text="Entidades extraídas da mensagem (formato: lista de dicionários como {'pessoa': 'João Silva'})"
    )
    confianca_resposta: models.FloatField = models.FloatField(
        blank=True,
        null=True,
        help_text="Nível de confiança da resposta do bot (0-1)"
    )

    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ['timestamp']

    def __str__(self):
        """
        Retorna representação string da mensagem.

        Returns:
            str: Remetente e preview do conteúdo
        """
        remetente_display = self.get_remetente_display()
        conteudo_preview = self.conteudo[:50] + \
            "..." if len(self.conteudo) > 50 else self.conteudo
        return f"{remetente_display}: {conteudo_preview}"

    def marcar_como_respondida(
            self,
            resposta: str,
            confianca: Optional[float] = None) -> None:
        """
        Marca a mensagem como respondida com a resposta fornecida.

        Args:
            resposta (str): Resposta gerada para a mensagem
            confianca (float, optional): Nível de confiança da resposta (0-1)
        """
        self.respondida = True
        self.resposta_bot = resposta
        if confianca is not None:
            self.confianca_resposta = confianca
        self.save()

    @property
    def is_from_client(self) -> bool:
        """
        Propriedade para compatibilidade com código existente.

        Returns:
            bool: True se a mensagem é do cliente
        """
        return self.remetente == TipoRemetente.CLIENTE

    @property
    def is_from_bot(self) -> bool:
        """
        Verifica se a mensagem é do bot.

        Returns:
            bool: True se a mensagem é do bot
        """
        return self.remetente == TipoRemetente.BOT

    def adicionar_intent(self, tipo_intent: str, valor_intent: str) -> None:
        """
        Adiciona um intent à lista de intents detectados.

        Args:
            tipo_intent (str): Tipo do intent (ex: 'saudacao', 'pergunta', 'solicitacao')
            valor_intent (str): Valor/conteúdo do intent

        Example:
            >>> mensagem.adicionar_intent('saudacao', 'Olá')
            >>> mensagem.adicionar_intent('pergunta', 'tudo bem?')
        """
        if not self.intent_detectado:
            self.intent_detectado = []

        # Adiciona o intent como dicionário
        intent_dict = {tipo_intent: valor_intent}
        self.intent_detectado.append(intent_dict)

    def get_intents_por_tipo(self, tipo_intent: str) -> list[str]:
        """
        Retorna todos os valores de um tipo específico de intent.

        Args:
            tipo_intent (str): Tipo do intent a buscar

        Returns:
            list[str]: Lista com todos os valores encontrados para o tipo

        Example:
            >>> mensagem.get_intents_por_tipo('pergunta')
            ['tudo bem?', 'vocês produzem cones para crepe?']
        """
        valores = []
        if self.intent_detectado:
            for intent_dict in self.intent_detectado:
                if isinstance(intent_dict,
                              dict) and tipo_intent in intent_dict:
                    valores.append(intent_dict[tipo_intent])
        return valores

    def get_todos_intents(self) -> dict[str, list[str]]:
        """
        Retorna todos os intents organizados por tipo.

        Returns:
            dict: Dicionário com tipos como chaves e listas de valores

        Example:
            >>> mensagem.get_todos_intents()
            {
                'saudacao': ['Olá'],
                'pergunta': ['tudo bem?', 'vocês produzem cones para crepe?'],
                'solicitacao': ['gostaria de uma cotação de uma embalagem']
            }
        """
        intents_organizados = {}
        if self.intent_detectado:
            for intent_dict in self.intent_detectado:
                if isinstance(intent_dict, dict):
                    for tipo, valor in intent_dict.items():
                        if tipo not in intents_organizados:
                            intents_organizados[tipo] = []
                        intents_organizados[tipo].append(valor)
        return intents_organizados

    @property
    def is_from_atendente_humano(self) -> bool:
        """
        Verifica se a mensagem é de um atendente humano.

        Returns:
            bool: True se a mensagem é de um atendente humano
        """
        return self.remetente == TipoRemetente.ATENDENTE_HUMANO


class FluxoConversa(models.Model):
    """
    Modelo para definir fluxos de conversa e estados.

    Gerencia os fluxos de conversação automatizados do sistema,
    incluindo condições de entrada, estados e transições.

    Attributes:
        id: Chave primária do registro
        nome: Nome único do fluxo de conversa
        descricao: Descrição detalhada do fluxo
        condicoes_entrada: Condições JSON para ativação do fluxo
        estados: Estados e transições do fluxo em formato JSON
        ativo: Indica se o fluxo está ativo
        data_criacao: Data de criação automática
        data_modificacao: Data de última modificação automática
    """
    id: models.AutoField = models.AutoField(
        primary_key=True,
        help_text="Chave primária do registro"
    )
    nome: models.CharField = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nome do fluxo de conversa"
    )
    descricao: models.TextField = models.TextField(
        blank=True,
        null=True,
        help_text="Descrição do fluxo"
    )
    condicoes_entrada: models.JSONField = models.JSONField(
        default=dict,
        help_text="Condições para entrar neste fluxo"
    )
    estados: models.JSONField = models.JSONField(
        default=dict,
        help_text="Estados e transições do fluxo"
    )
    ativo: models.BooleanField = models.BooleanField(
        default=True,
        help_text="Fluxo ativo"
    )
    data_criacao: models.DateTimeField = models.DateTimeField(
        auto_now_add=True
    )
    data_modificacao: models.DateTimeField = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Fluxo de Conversa"
        verbose_name_plural = "Fluxos de Conversa"

    def __str__(self):
        """
        Retorna representação string do fluxo de conversa.

        Returns:
            str: Nome do fluxo de conversa
        """
        return self.nome


# Função utilitária para inicializar cliente e atendimento
def inicializar_atendimento_whatsapp(numero_telefone: str,
                                     primeira_mensagem: str = "",
                                     metadata_cliente: Optional[dict[str, Any]] = None,
                                     nome_cliente: Optional[str] = None) -> tuple['Cliente',
                                                                                  'Atendimento']:
    """
    Inicializa ou recupera um cliente e cria um novo atendimento baseado no número do WhatsApp.

    Args:
        numero_telefone (str): Número de telefone do cliente
        primeira_mensagem (str, optional): Primeira mensagem recebida do cliente
        metadata_cliente (dict, optional): Metadados adicionais do cliente
        nome_cliente (str, optional): Nome do cliente (se conhecido)

    Returns:
        tuple: Tupla com (cliente, atendimento) criados/recuperados

    Raises:
        Exception: Se houver erro durante a inicialização
    """
    try:
        # Normaliza o número de telefone
        telefone_limpo = re.sub(r'\D', '', numero_telefone)
        if not telefone_limpo.startswith('55'):
            telefone_limpo = '55' + telefone_limpo
        telefone_formatado = '+' + telefone_limpo

        # Busca ou cria o cliente
        cliente, cliente_criado = Cliente.objects.get_or_create(
            telefone=telefone_formatado,
            defaults={
                'nome': nome_cliente,
                'metadados': metadata_cliente or {},
                'ativo': True
            }
        )

        # Se o cliente já existe, atualiza informações se fornecidas
        if not cliente_criado:
            if nome_cliente and not cliente.nome:
                cliente.nome = nome_cliente
            if metadata_cliente:
                cliente.metadados.update(metadata_cliente)
            cliente.save()

        # Verifica se existe atendimento em andamento
        atendimento_ativo = Atendimento.objects.filter(
            cliente=cliente,
            status__in=[
                StatusAtendimento.AGUARDANDO_INICIAL,
                StatusAtendimento.EM_ANDAMENTO,
                StatusAtendimento.AGUARDANDO_CLIENTE,
                StatusAtendimento.AGUARDANDO_ATENDENTE
            ]
        ).first()

        # Se não existe atendimento ativo, cria um novo
        if not atendimento_ativo:
            atendimento = Atendimento.objects.create(
                cliente=cliente,
                status=StatusAtendimento.AGUARDANDO_INICIAL,
                contexto_conversa={
                    'canal': 'whatsapp',
                    'primeira_interacao': True,
                    'sessao_iniciada': timezone.now().isoformat()
                }
            )

            # Adiciona entrada no histórico
            atendimento.adicionar_historico_status(
                StatusAtendimento.AGUARDANDO_INICIAL,
                "Atendimento iniciado via WhatsApp"
            )
        else:
            atendimento = atendimento_ativo

        # REMOVIDO: Não cria mensagem aqui para evitar duplicação
        # A mensagem será criada na função processar_mensagem_whatsapp

        logger.info(
            f"{'Novo' if cliente_criado else 'Existente'} cliente inicializado: {cliente.telefone}")

        return cliente, atendimento

    except Exception as e:
        logger.error(f"Erro ao inicializar atendimento WhatsApp: {e}")
        raise


def buscar_atendimento_ativo(numero_telefone: str) -> Optional['Atendimento']:
    """
    Busca um atendimento ativo para o número de telefone fornecido.

    Args:
        numero_telefone (str): Número de telefone do cliente

    Returns:
        Atendimento: Atendimento ativo ou None se não encontrado

    Raises:
        Exception: Se houver erro durante a busca
    """
    try:
        # Normaliza o número de telefone
        telefone_limpo = re.sub(r'\D', '', numero_telefone)
        if not telefone_limpo.startswith('55'):
            telefone_limpo = '55' + telefone_limpo
        telefone_formatado = '+' + telefone_limpo

        cliente = Cliente.objects.filter(telefone=telefone_formatado).first()
        if not cliente:
            return None

        atendimento = Atendimento.objects.filter(
            cliente=cliente,
            status__in=[
                StatusAtendimento.AGUARDANDO_INICIAL,
                StatusAtendimento.EM_ANDAMENTO,
                StatusAtendimento.AGUARDANDO_CLIENTE,
                StatusAtendimento.AGUARDANDO_ATENDENTE
            ]
        ).first()

        return atendimento

    except Exception as e:
        logger.error(f"Erro ao buscar atendimento ativo: {e}")
        return None


def nova_mensagem(data: dict[str, Any]) -> int:
    """
    Processa os dados brutos recebidos do webhook do WhatsApp e cria uma nova mensagem.

    Args:
        data (dict): Dados brutos do webhook do WhatsApp contendo:
            - data.key.remoteJid: Identificador do remetente
            - data.key.id: ID da mensagem
            - data.message: Objeto da mensagem com tipo específico

    Returns:
        int: ID da mensagem criada

    Raises:
        ValueError: Se campos obrigatórios estiverem ausentes
        Exception: Se houver erro durante o processamento
    """
    try:
        # Extrair informações básicas com verificações de segurança
        data_section = data.get('data')
        if not data_section:
            raise ValueError(
                "Campo 'data' não encontrado no payload do webhook")

        key_section = data_section.get('key')
        if not key_section:
            raise ValueError("Campo 'key' não encontrado nos dados do webhook")

        remote_jid = key_section.get('remoteJid')
        if not remote_jid:
            raise ValueError(
                "Campo 'remoteJid' não encontrado na chave do webhook")

        phone = remote_jid.split('@')[0]
        message_id = key_section.get('id')

        # Obter a primeira chave do message (tipo de mensagem)
        message_section = data_section.get('message')
        if not message_section:
            raise ValueError(
                "Campo 'message' não encontrado nos dados do webhook")

        message_keys = message_section.keys()
        tipo_chave = list(message_keys)[0] if message_keys else None

        # Converter chave JSON para tipo de mensagem interno
        tipo_mensagem = TipoMensagem.obter_por_chave_json(tipo_chave)

        # Extrair conteúdo da mensagem com base no tipo
        conteudo = ""
        metadados = {}

        if tipo_chave:
            message_data = message_section.get(tipo_chave, {})

            if tipo_mensagem == TipoMensagem.TEXTO_FORMATADO:
                conteudo = message_data.get('text', '')
            elif tipo_mensagem == TipoMensagem.IMAGEM:
                # Para imagens, podemos extrair a caption e URL/dados da imagem
                conteudo = message_data.get('caption', 'Imagem recebida')
                metadados['mimetype'] = message_data.get('mimetype')
                metadados['url'] = message_data.get('url')
                # Outros metadados relevantes para processamento posterior
                metadados['fileLength'] = message_data.get('fileLength')
            elif tipo_mensagem == TipoMensagem.VIDEO:
                # Para vídeos, similar às imagens
                conteudo = message_data.get('caption', 'Vídeo recebido')
                metadados['mimetype'] = message_data.get('mimetype')
                metadados['url'] = message_data.get('url')
                metadados['seconds'] = message_data.get('seconds')
                metadados['fileLength'] = message_data.get('fileLength')
            elif tipo_mensagem == TipoMensagem.AUDIO:
                # Para áudios
                conteudo = "Áudio recebido"
                metadados['mimetype'] = message_data.get('mimetype')
                metadados['url'] = message_data.get('url')
                metadados['seconds'] = message_data.get('seconds')
                metadados['ptt'] = message_data.get(
                    'ptt', False)  # Se é mensagem de voz
            elif tipo_mensagem == TipoMensagem.DOCUMENTO:
                # Para documentos
                conteudo = message_data.get('fileName', 'Documento recebido')
                metadados['mimetype'] = message_data.get('mimetype')
                metadados['url'] = message_data.get('url')
                metadados['fileLength'] = message_data.get('fileLength')
            elif tipo_mensagem == TipoMensagem.STICKER:
                # Para stickers
                conteudo = "Sticker recebido"
                metadados['mimetype'] = message_data.get('mimetype')
                metadados['url'] = message_data.get('url')
            elif tipo_mensagem == TipoMensagem.LOCALIZACAO:
                # Para localização
                conteudo = "Localização recebida"
                metadados['latitude'] = message_data.get('degreesLatitude')
                metadados['longitude'] = message_data.get('degreesLongitude')
                metadados['name'] = message_data.get('name')
                metadados['address'] = message_data.get('address')
            elif tipo_mensagem == TipoMensagem.CONTATO:
                # Para contatos
                conteudo = "Contato recebido"
                metadados['displayName'] = message_data.get('displayName')
                metadados['vcard'] = message_data.get('vcard')
            elif tipo_mensagem == TipoMensagem.LISTA:
                # Para mensagens de lista
                conteudo = message_data.get('title', 'Lista recebida')
                metadados['buttonText'] = message_data.get('buttonText')
                metadados['description'] = message_data.get('description')
                metadados['listType'] = message_data.get('listType')
            elif tipo_mensagem == TipoMensagem.BOTOES:
                # Para mensagens com botões
                conteudo = message_data.get('contentText', 'Botões recebidos')
                metadados['headerType'] = message_data.get('headerType')
                metadados['footerText'] = message_data.get('footerText')
            elif tipo_mensagem == TipoMensagem.ENQUETE:
                # Para enquetes
                conteudo = message_data.get('name', 'Enquete recebida')
                metadados['options'] = message_data.get('options')
                metadados['selectableCount'] = message_data.get(
                    'selectableCount')
            elif tipo_mensagem == TipoMensagem.REACAO:
                # Para reações
                conteudo = "Reação recebida"
                metadados['emoji'] = message_data.get('text')
                metadados['key'] = message_data.get('key')
            else:
                # Para outros tipos não tratados especificamente
                conteudo = f"Mensagem do tipo {tipo_chave} recebida"

        logger.info(
            f"Processando mensagem - Telefone: {phone}, Tipo: {tipo_chave}, Conteúdo: {conteudo[:50]}...")

        # Processar a mensagem usando a função existente
        mensagem = processar_mensagem_whatsapp(
            numero_telefone=phone,
            conteudo=conteudo,
            tipo_mensagem=tipo_mensagem,
            message_id=message_id,
            metadados=metadados,
            remetente=TipoRemetente.CLIENTE
        )

        return mensagem

    except Exception as e:
        logger.error(f"Erro ao processar nova mensagem WhatsApp: {e}")
        raise


def processar_mensagem_whatsapp(
        numero_telefone: str,
        conteudo: str,
        tipo_mensagem: 'TipoMensagem' = TipoMensagem.TEXTO_FORMATADO,
        message_id: Optional[str] = None,
        metadados: Optional[dict[str, Any]] = None,
        remetente: Optional['TipoRemetente'] = None) -> int:
    """
    Processa uma mensagem recebida do WhatsApp.

    Args:
        numero_telefone (str): Número de telefone do remetente
        conteudo (str): Conteúdo da mensagem
        tipo_mensagem (TipoMensagem): Tipo da mensagem (texto, imagem, etc.)
        message_id (str, optional): ID da mensagem no WhatsApp
        metadados (dict, optional): Metadados adicionais da mensagem
        remetente (TipoRemetente, optional): Tipo do remetente da mensagem (se já determinado)

    Returns:
        Mensagem: Objeto mensagem criado

    Raises:
        Exception: Se houver erro durante o processamento
    """
    try:
        # Determinar o tipo de remetente se não foi especificado
        if remetente is None:
            # Verificar se o número pertence a um atendente humano
            try:
                atendente = AtendenteHumano.objects.filter(
                    telefone=numero_telefone).first()
                if atendente:
                    remetente = TipoRemetente.ATENDENTE_HUMANO
                    logger.info(
                        f"Número {numero_telefone} identificado como atendente: {
                            atendente.nome}")
                else:
                    remetente = TipoRemetente.CLIENTE
            except Exception as e:
                logger.warning(
                    f"Erro ao verificar se número é de atendente: {e}. Assumindo CLIENTE.")
                remetente = TipoRemetente.CLIENTE

        # Busca atendimento ativo ou inicializa novo
        atendimento = buscar_atendimento_ativo(numero_telefone)

        if not atendimento:
            # Se não existe atendimento ativo, inicializa um novo
            cliente, atendimento = inicializar_atendimento_whatsapp(
                numero_telefone,
                conteudo
            )

        # Verifica se a mensagem já foi processada (evita duplicação)
        if message_id:
            mensagem_existente = Mensagem.objects.filter(
                message_id_whatsapp=message_id,
                atendimento=atendimento
            ).first()

            if mensagem_existente:
                logger.warning(
                    f"Mensagem duplicada detectada - ID: {message_id}, "
                    f"Telefone: {numero_telefone}. Retornando mensagem existente."
                )
                return mensagem_existente.id

        # Cria a mensagem
        mensagem = Mensagem.objects.create(
            atendimento=atendimento,
            tipo=tipo_mensagem,
            conteudo=conteudo,
            remetente=remetente,
            message_id_whatsapp=message_id,
            metadados=metadados or {}
        )

        # Atualiza timestamp da última interação do cliente
        if remetente == TipoRemetente.CLIENTE:
            atendimento.cliente.ultima_interacao = timezone.now()
            atendimento.cliente.save()

            # Atualiza status do atendimento se for a primeira mensagem
            if atendimento.status == StatusAtendimento.AGUARDANDO_INICIAL:
                atendimento.status = StatusAtendimento.EM_ANDAMENTO
                atendimento.adicionar_historico_status(
                    StatusAtendimento.EM_ANDAMENTO,
                    "Primeira mensagem recebida"
                )
                atendimento.save()

        logger.info(
            f"Mensagem processada para {numero_telefone} de {remetente}: {conteudo[:50]}...")

        return mensagem.id

    except Exception as e:
        logger.error(f"Erro ao processar mensagem WhatsApp: {e}")
        raise


def buscar_atendente_disponivel(
        especialidades: Optional[list[str]] = None,
        departamento: Optional[str] = None) -> Optional['AtendenteHumano']:
    """
    Busca um atendente humano disponível para receber um novo atendimento.

    Args:
        especialidades (list, optional): Lista de especialidades requeridas
        departamento (str, optional): Departamento específico

    Returns:
        AtendenteHumano: Atendente disponível ou None se nenhum encontrado
    """
    try:
        # Query base: atendentes ativos e disponíveis
        query = AtendenteHumano.objects.filter(
            ativo=True,
            disponivel=True
        )

        # Filtra por departamento se especificado
        if departamento:
            query = query.filter(departamento=departamento)

        # Filtra atendentes que podem receber novos atendimentos
        atendentes_disponiveis = []
        for atendente in query:
            if atendente.pode_receber_atendimento():
                # Verifica especialidades se especificadas
                if especialidades:
                    if any(
                            esp in atendente.especialidades for esp in especialidades):
                        atendentes_disponiveis.append(atendente)
                else:
                    atendentes_disponiveis.append(atendente)

        if not atendentes_disponiveis:
            return None

        # Retorna o atendente com menos atendimentos ativos (balanceamento)
        return min(
            atendentes_disponiveis,
            key=lambda a: a.get_atendimentos_ativos())

    except Exception as e:
        logger.error(f"Erro ao buscar atendente disponível: {e}")
        return None


def transferir_atendimento_automatico(
        atendimento: 'Atendimento',
        especialidades: Optional[list[str]] = None,
        departamento: Optional[str] = None) -> Optional['AtendenteHumano']:
    """
    Transfere automaticamente um atendimento para um atendente humano disponível.

    Args:
        atendimento (Atendimento): Atendimento a ser transferido
        especialidades (list, optional): Lista de especialidades requeridas
        departamento (str, optional): Departamento específico

    Returns:
        AtendenteHumano: Atendente que recebeu o atendimento ou None se nenhum disponível

    Raises:
        Exception: Se houver erro durante a transferência
    """
    try:
        atendente = buscar_atendente_disponivel(especialidades, departamento)

        if not atendente:
            logger.warning(
                f"Nenhum atendente disponível para o atendimento {
                    atendimento.id}")
            return None

        # Realiza a transferência
        observacao = "Transferência automática do sistema"
        if especialidades:
            observacao += f" - Especialidades: {', '.join(especialidades)}"
        if departamento:
            observacao += f" - Departamento: {departamento}"

        atendimento.transferir_para_humano(atendente, observacao)

        logger.info(
            f"Atendimento {
                atendimento.id} transferido automaticamente para {
                atendente.nome}")

        return atendente

    except Exception as e:
        logger.error(f"Erro ao transferir atendimento automaticamente: {e}")
        raise


def listar_atendentes_por_disponibilidade(
) -> dict[str, list['AtendenteHumano']]:
    """
    Lista todos os atendentes agrupados por disponibilidade.

    Returns:
        dict: Dicionário com atendentes agrupados por status de disponibilidade
    """
    try:
        atendentes = AtendenteHumano.objects.filter(ativo=True)

        resultado: dict[str, list[dict[str, Any]]] = {
            'disponiveis': [],
            'ocupados': [],
            'indisponiveis': []
        }

        for atendente in atendentes:
            info_atendente = {
                'id': atendente.id,
                'nome': atendente.nome,
                'cargo': atendente.cargo,
                'departamento': atendente.departamento,
                'telefone': atendente.telefone,
                'atendimentos_ativos': atendente.get_atendimentos_ativos(),
                'max_atendimentos': atendente.max_atendimentos_simultaneos,
                'especialidades': atendente.especialidades
            }

            if not atendente.disponivel:
                resultado['indisponiveis'].append(info_atendente)
            elif atendente.pode_receber_atendimento():
                resultado['disponiveis'].append(info_atendente)
            else:
                resultado['ocupados'].append(info_atendente)

        return resultado

    except Exception as e:
        logger.error(f"Erro ao listar atendentes por disponibilidade: {e}")
        return {'disponiveis': [], 'ocupados': [], 'indisponiveis': []}


def enviar_mensagem_atendente(
        atendimento: 'Atendimento',
        atendente_humano: 'AtendenteHumano',
        conteudo: str,
        tipo_mensagem: 'TipoMensagem' = TipoMensagem.TEXTO_FORMATADO,
        metadados: Optional[dict[str, Any]] = None) -> 'Mensagem':
    """
    Envia uma mensagem de um atendente humano para um atendimento.

    Args:
        atendimento (Atendimento): Atendimento onde a mensagem será enviada
        atendente_humano (AtendenteHumano): Atendente que está enviando a mensagem
        conteudo (str): Conteúdo da mensagem
        tipo_mensagem (TipoMensagem): Tipo da mensagem (padrão: TEXTO)
        metadados (dict, optional): Metadados adicionais da mensagem

    Returns:
        Mensagem: Objeto mensagem criado

    Raises:
        ValidationError: Se o atendente não estiver associado ao atendimento
    """
    try:
        # Verifica se o atendente está associado ao atendimento
        if atendimento.atendente_humano != atendente_humano:
            raise ValidationError(
                f"O atendente {
                    atendente_humano.nome} não está associado a este atendimento.")

        # Cria a mensagem
        mensagem = Mensagem.objects.create(
            atendimento=atendimento,
            tipo=tipo_mensagem,
            conteudo=conteudo,
            remetente=TipoRemetente.ATENDENTE_HUMANO,
            metadados=metadados or {
                'atendente_id': atendente_humano.id,
                'atendente_nome': atendente_humano.nome
            }
        )

        # Atualiza a última atividade do atendente
        atendente_humano.ultima_atividade = timezone.now()
        atendente_humano.save()

        logger.info(
            f"Mensagem enviada pelo atendente {atendente_humano.nome} no atendimento {atendimento.id}: {conteudo[:50]}..."
        )

        return mensagem

    except Exception as e:
        logger.error(f"Erro ao enviar mensagem do atendente: {e}")
        raise
