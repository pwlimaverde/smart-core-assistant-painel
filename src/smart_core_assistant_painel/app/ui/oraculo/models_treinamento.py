import re
from typing import Any, List, Optional

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.conf import settings
from loguru import logger
from smart_core_assistant_painel.modules.services import SERVICEHUB

from .models_departamento import Departamento
from langchain.docstore.document import Document


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
        raise ValidationError("Tag deve ter no máximo 40 caracteres.")

    if " " in value:
        raise ValidationError("Tag não deve conter espaços.")

    if not value.islower():
        raise ValidationError("Tag deve conter apenas letras minúsculas.")

    # Opcional: validar se contém apenas letras, números e underscore
    if not re.match(r"^[a-z0-9_]+$", value):
        raise ValidationError(
            "Tag deve conter apenas letras minúsculas, números e underscore."
        )


class Treinamento(models.Model):
    """
    Modelo para armazenar informações de treinamento de IA.

    Este modelo gerencia treinamentos organizados por tags e grupos.
    O conteúdo completo é armazenado aqui e depois dividido em chunks
    que são salvos como registros Documento com embeddings individuais.

    Attributes:
        id: Chave primária do registro
        tag: Identificador único do treinamento
        grupo: Grupo ao qual o treinamento pertence
        conteudo: Conteúdo completo do treinamento (antes da divisão em chunks)
        treinamento_finalizado: Status de finalização do treinamento
        treinamento_vetorizado: Status de vetorização do treinamento
        data_criacao: Data de criação automática do treinamento
        data_atualizacao: Data da última atualização
    """

    id: models.AutoField = models.AutoField(
        primary_key=True, help_text="Chave primária do registro"
    )
    tag: models.CharField = models.CharField(
        max_length=40,
        validators=[validate_tag],
        blank=False,
        null=False,
        help_text="Campo obrigatório para identificar o treinamento",
    )
    grupo: models.CharField = models.CharField(
        max_length=40,
        validators=[validate_tag],
        blank=False,
        null=False,
        help_text="Campo obrigatório para identificar o grupo do treinamento",
    )
    conteudo: models.TextField = models.TextField(
        blank=True,
        null=True,
        help_text="Conteúdo completo do treinamento (antes da divisão em chunks)",
    )
    treinamento_finalizado: models.BooleanField = models.BooleanField(
        default=False,
        help_text="Indica se o treinamento foi finalizado",
    )
    treinamento_vetorizado: models.BooleanField = models.BooleanField(
        default=False,
        help_text="Indica se o treinamento foi vetorizado com sucesso",
    )
    data_criacao: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criação do treinamento",
    )
    data_atualizacao: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        help_text="Data da última atualização do treinamento",
    )

    class Meta:
        verbose_name = "Treinamento"
        verbose_name_plural = "Treinamentos"
        ordering = ["-data_criacao"]
        indexes = [
            models.Index(fields=["tag", "grupo"]),
            models.Index(fields=["data_criacao"]),
            models.Index(fields=["treinamento_finalizado", "treinamento_vetorizado"]),
        ]

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
            raise ValidationError({"grupo": "O grupo não pode ser igual à tag."})

    def __str__(self):
        """
        Retorna representação string do objeto.

        Returns:
            str: Tag do treinamento ou identificador padrão
        """
        return str(self.tag) if self.tag else f"Treinamento {self.id}"

    def processar_conteudo_para_chunks(self, conteudo_novo: str) -> None:
        """
        Processa o conteúdo, armazena no treinamento e cria chunks como Documento.
        Gera embeddings automaticamente e finaliza o treinamento.
        
        Args:
            conteudo_novo (str): Conteúdo completo a ser processado
        """
        # Armazena o conteúdo completo
        self.conteudo = conteudo_novo
        self.save(update_fields=['conteudo'])
        
        # Limpa documentos existentes
        self.limpar_documentos()
        
        if not conteudo_novo or not conteudo_novo.strip():
            logger.info(f"Conteúdo vazio para treinamento {self.pk}")
            return
            
        # Cria chunks usando RecursiveCharacterTextSplitter do LangChain
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            from smart_core_assistant_painel.modules.services import SERVICEHUB
            
            # Cria um documento temporário para chunking
            temp_document = Document(
                page_content=conteudo_novo,
                metadata={
                    "source": "treinamento_manual", 
                    "treinamento_id": str(self.pk),
                    "tag": self.tag,
                    "grupo": self.grupo
                }
            )
            
            # Divide documentos em chunks
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=SERVICEHUB.CHUNK_SIZE, 
                chunk_overlap=SERVICEHUB.CHUNK_OVERLAP
            )
            chunks = splitter.split_documents([temp_document])
            
            # Cria registros Documento para cada chunk (com embeddings automáticos)
            self.criar_documentos(chunks)
            
            # Finaliza o treinamento automaticamente se todos os embeddings foram criados
            if self.treinamento_vetorizado:
                self.finalizar()
            
            logger.info(f"Processados {len(chunks)} chunks para treinamento {self.pk}")
            
        except Exception as e:
            logger.error(f"Erro ao processar conteúdo em chunks: {e}")
            raise

    def criar_documentos(self, documentos_langchain: List[Document]) -> None:
        """
        Cria registros Documento a partir de uma lista de objetos Document do LangChain.
        Os embeddings são gerados automaticamente no método save() de cada documento.

        Args:
            documentos_langchain: Lista de objetos Document do LangChain

        Raises:
            TypeError: Se algum item da lista não for um objeto Document válido
            ValueError: Se houver erro no processamento dos dados
        """
        # Verificação segura da lista para evitar erro de ambiguidade
        if len(documentos_langchain) == 0:
            logger.info(f"Lista de documentos vazia para treinamento {self.pk}")
            return

        try:
            # Limpa documentos existentes
            self.limpar_documentos()

            # Cria novos registros Documento (embeddings gerados automaticamente no save)
            documentos_criados = []
            sucesso = 0
            erros = 0
            
            for i, documento in enumerate(documentos_langchain):
                if not isinstance(documento, Document):
                    error_msg = f"Item na posição {i} não é um Document válido: {type(documento)}"
                    logger.error(error_msg)
                    erros += 1
                    continue

                try:
                    # Importação local para evitar circular import
                    from .models_documento import Documento
                    doc_obj = Documento(
                        treinamento=self,
                        conteudo=documento.page_content or "",
                        metadata=documento.metadata or {},
                        ordem=i + 1,
                    )
                    # O embedding é gerado automaticamente no save()
                    doc_obj.save()
                    documentos_criados.append(doc_obj)
                    sucesso += 1
                except Exception as e:
                    logger.error(f"Erro ao criar documento {i}: {e}")
                    erros += 1

            # Atualiza status de vetorização do treinamento
            if erros == 0:
                self.treinamento_vetorizado = True
                self.save(update_fields=['treinamento_vetorizado'])
                logger.info(f"Criados {len(documentos_criados)} documentos com embeddings para treinamento {self.pk}")
            else:
                logger.warning(f"Documentos criados: {len(documentos_criados)}, Sucessos: {sucesso}, Erros: {erros}")

        except Exception as e:
            error_msg = f"Erro inesperado ao criar documentos: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def limpar_documentos(self) -> None:
        """
        Remove todos os documentos relacionados a este treinamento.
        """
        if self.pk:
            # Importação local para evitar circular import
            from django.apps import apps
            Documento = apps.get_model('oraculo', 'Documento')
            count = self.documentos.count()
            self.documentos.all().delete()
            logger.info(f"Removidos {count} documentos do treinamento {self.pk}")

    def vetorizar_documentos(self) -> None:
        """
        Gera embeddings para documentos que ainda não possuem embedding.
        
        Este método é usado principalmente para casos onde documentos foram criados
        sem embeddings ou para reprocessar documentos existentes.
        """
        if not self.pk:
            logger.warning("Treinamento deve ser salvo antes de vetorizar documentos")
            return

        # Importação local para evitar circular import
        from django.apps import apps
        Documento = apps.get_model('oraculo', 'Documento')
        documentos_sem_embedding = self.documentos.filter(embedding__isnull=True)

        if not documentos_sem_embedding.exists():
            logger.info(f"Todos os documentos do treinamento {self.pk} já estão vetorizados")
            self.treinamento_vetorizado = True
            self.save(update_fields=['treinamento_vetorizado'])
            return

        # Gera embeddings individualmente para ter melhor controle
        sucesso = 0
        erros = 0
        
        for documento in documentos_sem_embedding:
            try:
                documento.gerar_embedding()
                sucesso += 1
            except Exception as e:
                logger.error(f"Erro ao gerar embedding para documento {documento.id}: {e}")
                erros += 1
        
        # Atualiza status de vetorização
        if erros == 0:
            self.treinamento_vetorizado = True
            self.finalizar()  # Finaliza automaticamente se todos os embeddings foram criados
            self.save(update_fields=['treinamento_vetorizado'])
            logger.info(f"Vetorização concluída: {sucesso} documentos vetorizados")
        else:
            logger.warning(f"Vetorização parcial: {sucesso} sucessos, {erros} erros")

    def finalizar(self) -> None:
        """
        Marca o treinamento como finalizado e persiste no banco.
        """
        self.treinamento_finalizado = True
        self.save(update_fields=["treinamento_finalizado"])
        logger.info(f"Treinamento {self.pk} finalizado")
        
    @classmethod
    def search_by_similarity(
        cls,
        query: str,
        top_k: int = 5,
        grupo: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[tuple["Treinamento", float]]:
        """
        Busca treinamentos mais similares a um texto de consulta usando os métodos nativos do pgvector.

        Utiliza a nova arquitetura com Documento para
        busca semântica mais precisa por documento individual.

        Args:
            query (str): Texto de consulta para gerar o embedding.
            top_k (int): Número máximo de resultados a retornar.
            grupo (Optional[str]): Filtro opcional por grupo.
            tag (Optional[str]): Filtro opcional por tag.

        Returns:
            List[tuple[Treinamento, float]]: Lista de tuplas
            (objeto, distancia), ordenada por menor distância.
        """
        if not query or not query.strip():
            return []
        if top_k <= 0:
            return []

        # Importação local para evitar circular import
        from .models_documento import Documento
        # Busca documentos similares usando Documento
        documentos_similares = Documento.search_by_similarity(
            query=query.strip(),
            top_k=top_k * 3,  # Busca mais para garantir diversidade
            grupo=grupo,
            tag=tag,
        )

        if not documentos_similares:
            return []

        # Agrupa por treinamento e pega a melhor distância
        treinamentos_scores = {}
        for documento, distancia in documentos_similares:
            treinamento = documento.treinamento
            if treinamento.id not in treinamentos_scores:
                treinamentos_scores[treinamento.id] = (treinamento, distancia)
            else:
                # Mantém a menor distância (mais similar)
                if distancia < treinamentos_scores[treinamento.id][1]:
                    treinamentos_scores[treinamento.id] = (treinamento, distancia)

        # Ordena por distância e retorna top_k
        resultados = list(treinamentos_scores.values())
        resultados.sort(key=lambda x: x[1])  # Ordena por distância
        
        return resultados[:top_k]

    def clear_all_data(self) -> None:
        """
        Limpa completamente todos os dados do treinamento para reutilização.
        
        Este método é especialmente útil durante edição de treinamentos,
        garantindo que não haja conflitos ou problemas de ambiguidade.
        """
        self.conteudo = ""
        self.treinamento_finalizado = False
        self.treinamento_vetorizado = False
        
        # Limpa documentos se o treinamento já foi salvo
        self.limpar_documentos()
            
        logger.info(f"Dados do treinamento {self.pk or 'novo'} limpos completamente")

    def finalize(self) -> None:
        """
        Marca o treinamento como finalizado e persiste no banco.
        """
        self.treinamento_finalizado = True
        self.save(update_fields=["treinamento_finalizado"])

    @classmethod
    def build_similarity_context_v2(
        cls,
        query: str,
        top_k_docs: int = 5,
        grupo: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> str:
        """
        Versão otimizada da busca semântica usando Documento.

        Esta versão é mais eficiente pois utiliza embeddings pré-calculados
        armazenados na tabela Documento, evitando geração em tempo real.

        Args:
            query (str): Texto de consulta
            top_k_docs (int): Quantidade de documentos no contexto
            grupo (Optional[str]): Filtro por grupo
            tag (Optional[str]): Filtro por tag

        Returns:
            str: Contexto concatenado com '---' entre os chunks
        """
        if not query or not query.strip():
            return ""
        if top_k_docs <= 0:
            return ""

        # Importação local para evitar circular import
        from .models_documento import Documento
        # Busca documentos mais similares diretamente
        documentos_similares = Documento.search_by_similarity(
            query=query.strip(),
            top_k=top_k_docs,
            grupo=grupo,
            tag=tag,
        )

        if not documentos_similares:
            return ""

        # Monta a string de contexto
        lines: List[str] = []
        lines.append(
            "Contexto de suporte (documentos mais similares - v2):"
        )
        
        for rank, (documento, distancia) in enumerate(documentos_similares, start=1):
            treinamento = documento.treinamento
            source = documento.metadata.get("source", "-")

            header = (
                f"[{rank}] Treinamento={treinamento.tag} | Grupo={treinamento.grupo} | "
                f"Fonte={source} | Distância={distancia:.4f}"
            )
            lines.append(header)
            lines.append(documento.conteudo.strip())
            lines.append("---")

        return "\n".join(lines)