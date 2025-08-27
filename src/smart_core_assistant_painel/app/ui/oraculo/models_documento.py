import re
from typing import Any, List, Optional

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.conf import settings
from langchain.docstore.document import Document
from loguru import logger
from smart_core_assistant_painel.modules.services import SERVICEHUB

from .models_departamento import Departamento
# Importando nosso VectorField personalizado
from .fields import VectorField
# Removendo o import do VectorField do pgvector
# from pgvector.django import VectorField, CosineDistance, HnswIndex

# Importando CosineDistance e HnswIndex do pgvector
from pgvector.django import CosineDistance, HnswIndex


class Documento(models.Model):
    """
    Modelo que representa um documento vetorizado individual.
    
    Cada instância armazena um chunk de conteúdo de treinamento
    com seu respectivo embedding vetorial para busca semântica.
    """
    
    # Relacionamento com Treinamento (1:N) - usando string para evitar circular import
    treinamento: models.ForeignKey = models.ForeignKey(
        "Treinamento",  # Referência direta ao modelo Treinamento
        on_delete=models.CASCADE,
        related_name="documentos",
        help_text="Treinamento ao qual este documento pertence",
    )
    
    # Conteúdo do documento (chunk)
    conteudo: models.TextField = models.TextField(
        blank=True,
        null=True,
        help_text="Conteúdo do chunk de treinamento",
    )
    
    # Metadados do documento
    metadata: models.JSONField = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadados do documento (tag, grupo, source, etc.)",
    )
    
    # Embedding vetorial (1024 dimensões)
    embedding: VectorField = VectorField(
        dimensions=1024,
        null=True,
        blank=True,
        help_text="Vetor de embeddings do conteúdo do documento",
    )
    
    def formfield(self, **kwargs):
        """
        Sobrescreve o método formfield para evitar que o campo embedding
        seja exibido diretamente no formulário do admin, evitando o erro
        "The truth value of an array with more than one element is ambiguous".
        """
        # Para o campo embedding, retornamos None para evitar exibição no admin
        from django import forms
        kwargs['widget'] = forms.HiddenInput()
        # Retornando None para evitar a exibição do campo no formulário
        return None

    # Ordem do documento no treinamento
    ordem: models.PositiveIntegerField = models.PositiveIntegerField(
        default=1,
        help_text="Ordem do documento no treinamento",
    )
    
    # Timestamps
    data_criacao: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criação do documento",
    )
    
    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["treinamento", "ordem"]
        indexes = [
            models.Index(fields=["treinamento", "ordem"]),
            models.Index(fields=["data_criacao"]),
            # Adicionando índice HNSW para buscas de similaridade com distância cosseno
            HnswIndex(
                name='documento_embedding_hnsw_idx',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops']
            ),
        ]

    def __str__(self):
        """
        Retorna representação string do objeto.

        Returns:
            str: Conteúdo truncado do documento
        """
        if self.conteudo:
            return f"Documento {self.pk}: {self.conteudo[:50]}..."
        return f"Documento {self.pk} (vazio)"

    def save(self, *args, **kwargs):
        """
        Salva o documento, gerando o embedding antes se necessário.
        """
        # Gera embedding antes de salvar se não existir e o treinamento estiver finalizado
        # Verificação segura para evitar erro "truth value of array is ambiguous"
        embedding_exists = self.embedding is not None
        if hasattr(self.embedding, '__len__'):
            try:
                embedding_exists = len(self.embedding) > 0
            except Exception:
                # Se não conseguirmos verificar o tamanho, assumimos que existe
                embedding_exists = True
        
        if (not embedding_exists and self.conteudo and self.conteudo.strip() and 
            self.treinamento and self.treinamento.treinamento_finalizado):
            try:
                self.gerar_embedding_sem_salvar()
            except Exception as e:
                logger.error(f"Erro ao gerar embedding antes de salvar documento: {e}")
                # Continua salvando mesmo se o embedding falhar
        
        super().save(*args, **kwargs)
    
    def gerar_embedding(self) -> None:
        """
        Gera o embedding do documento e salva no banco.
        
        Raises:
            EmbeddingError: Se houver erro na geração do embedding
        """
        self.gerar_embedding_sem_salvar()
        if self.pk:
            self.save(update_fields=['embedding'])
        else:
            logger.warning("Documento ainda não foi salvo, embedding será salvo junto")

    def gerar_embedding_sem_salvar(self) -> None:
        """
        Gera o embedding do documento sem salvar no banco.
        
        Raises:
            EmbeddingError: Se houver erro na geração do embedding
        """
        if not self.conteudo or not self.conteudo.strip():
            logger.warning(f"Conteúdo vazio para documento {self.pk or 'novo'}")
            return

        try:
            # Importações e configurações
            from smart_core_assistant_painel.modules.services import SERVICEHUB
            
            # Criar instância de embeddings usando configurações do ServiceHub
            embeddings_class = SERVICEHUB.EMBEDDINGS_CLASS
            embeddings_model = SERVICEHUB.EMBEDDINGS_MODEL
            
            # Criar instância de embeddings baseada na configuração do ServiceHub
            embeddings_instance = None
            if embeddings_class == "OpenAIEmbeddings":
                from langchain_openai import OpenAIEmbeddings
                embeddings_instance = OpenAIEmbeddings(model=embeddings_model)
            
            elif embeddings_class == "OllamaEmbeddings":
                from langchain_ollama import OllamaEmbeddings
                embeddings_instance = OllamaEmbeddings(model=embeddings_model)
            
            elif embeddings_class == "HuggingFaceEmbeddings":
                try:
                    # Tentar importar da versão mais recente primeiro
                    from langchain_huggingface import HuggingFaceEmbeddings
                    embeddings_instance = HuggingFaceEmbeddings(model_name=embeddings_model)
                except ImportError:
                    # Fallback para a versão community se a versão huggingface não estiver disponível
                    from langchain_community.embeddings import HuggingFaceEmbeddings
                    embeddings_instance = HuggingFaceEmbeddings(model_name=embeddings_model)
            
            elif embeddings_class == "HuggingFaceInferenceAPIEmbeddings":
                from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
                from pydantic import SecretStr
                import os
                api_key = os.environ.get("HUGGINGFACE_API_KEY", "")
                embeddings_instance = HuggingFaceInferenceAPIEmbeddings(
                    api_key=SecretStr(api_key),
                    model_name=embeddings_model
                )
            
            else:
                # Fallback para OpenAI como padrão
                from langchain_openai import OpenAIEmbeddings
                embeddings_instance = OpenAIEmbeddings(model=embeddings_model or "text-embedding-ada-002")
            
            # Verificar se embeddings_instance foi criado
            if embeddings_instance is None:
                raise ValueError(f"Não foi possível criar instância de embeddings para a classe: {embeddings_class}")
            
            # Gerar embeddings usando LangChain
            embedding_vector = embeddings_instance.embed_query(self.conteudo)
            
            # Converter para lista se necessário
            try:
                # Tentar converter para lista diretamente
                self.embedding = list(embedding_vector)
            except Exception:
                # Se falhar, atribuir diretamente
                self.embedding = embedding_vector

            logger.info(f"Embedding gerado para documento {self.pk or 'novo'}")

        except Exception as e:
            error_msg = f"Erro ao gerar embedding para documento {self.pk or 'novo'}: {e}"
            logger.error(error_msg)
            raise

    @classmethod
    def search_by_similarity(
        cls,
        query: str,
        top_k: int = 5,
        grupo: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[tuple["Documento", float]]:
        """
        Busca documentos mais similares a um texto de consulta usando os métodos nativos do pgvector.

        Args:
            query (str): Texto de consulta para gerar o embedding
            top_k (int): Número máximo de resultados
            grupo (Optional[str]): Filtro opcional por grupo do treinamento
            tag (Optional[str]): Filtro opcional por tag do treinamento

        Returns:
            List[tuple[Documento, float]]: Lista de tuplas (documento, distância)
        """
        if not query or not query.strip():
            return []
        if top_k <= 0:
            return []

        # Gera vetor do texto de consulta usando método estático
        query_vec: List[float] = cls._embed_text_static(query.strip())

        # Base queryset: documentos de treinamentos finalizados com embedding
        qs = cls.objects.filter(
            treinamento__treinamento_finalizado=True,
            embedding__isnull=False
        )

        # Aplicar filtros opcionais
        if grupo:
            qs = qs.filter(treinamento__grupo=grupo)
        if tag:
            qs = qs.filter(treinamento__tag=tag)

        # Anota com a distância cosseno, ordena e limita resultados
        # Esta é a forma correta conforme documentação do pgvector
        qs = qs.annotate(
            distance=CosineDistance('embedding', query_vec)
        ).order_by('distance')[:top_k]

        # Coleta os resultados já anotados
        resultados: List[tuple["Documento", float]] = []
        for obj in qs:
            distancia = getattr(obj, 'distance', 0.0)
            resultados.append((obj, float(distancia)))

        return resultados

    @staticmethod
    def _embed_text_static(text: str) -> List[float]:
        """
        Gera o vetor de embedding para um texto (método estático).

        Args:
            text (str): Texto de entrada.

        Returns:
            List[float]: Vetor de floats (dimensão 1024).
        """
        from smart_core_assistant_painel.modules.services import SERVICEHUB
        from django.conf import settings
        
        embeddings_class: str = SERVICEHUB.EMBEDDINGS_CLASS
        embeddings_model: str = SERVICEHUB.EMBEDDINGS_MODEL

        try:
            if embeddings_class == "OllamaEmbeddings":
                from langchain_ollama import OllamaEmbeddings
                base_url: str = getattr(settings, "OLLAMA_BASE_URL", "")
                kwargs: dict[str, Any] = {}
                if embeddings_model:
                    kwargs["model"] = embeddings_model
                if base_url:
                    kwargs["base_url"] = base_url
                embeddings = OllamaEmbeddings(**kwargs)
            elif embeddings_class == "OpenAIEmbeddings":
                from langchain_openai import OpenAIEmbeddings
                if embeddings_model:
                    embeddings = OpenAIEmbeddings(model=embeddings_model)
                else:
                    embeddings = OpenAIEmbeddings()
            elif embeddings_class == "HuggingFaceEmbeddings":
                try:
                    # Tentar importar da versão mais recente primeiro
                    from langchain_huggingface import HuggingFaceEmbeddings
                    if embeddings_model:
                        embeddings = HuggingFaceEmbeddings(model_name=embeddings_model)
                    else:
                        embeddings = HuggingFaceEmbeddings()
                except ImportError:
                    # Fallback para a versão community se a versão huggingface não estiver disponível
                    from langchain_community.embeddings import HuggingFaceEmbeddings
                    if embeddings_model:
                        embeddings = HuggingFaceEmbeddings(model_name=embeddings_model)
                    else:
                        embeddings = HuggingFaceEmbeddings()
            else:
                raise ValueError(f"Classe de embeddings não suportada: {embeddings_class}")

            # Gera embedding
            if hasattr(embeddings, "embed_query"):
                vec: List[float] = list(map(float, embeddings.embed_query(text)))
            else:
                docs_vec: List[List[float]] = embeddings.embed_documents([text])
                vec = list(map(float, docs_vec[0]))
            
            # Garantir que o vetor seja uma lista de floats
            return list(vec)
            
        except Exception as exc:
            logger.error(f"Erro ao gerar embedding do texto: {exc}", exc_info=True)
            raise

    @classmethod
    def limpar_documentos_por_treinamento(cls, treinamento_id: int) -> None:
        """Remove todos os documentos relacionados a um treinamento específico.
        
        Args:
            treinamento_id (int): ID do treinamento cujos documentos devem ser removidos
        """
        count = cls.objects.filter(treinamento_id=treinamento_id).count()
        cls.objects.filter(treinamento_id=treinamento_id).delete()
        logger.info(f"Removidos {count} documentos do treinamento {treinamento_id}")

    @classmethod
    def processar_conteudo_para_chunks(cls, treinamento, conteudo_novo: str) -> None:
        """Processa o conteúdo e cria chunks como registros Documento.
        
        Args:
            treinamento: Instância do modelo Treinamento
            conteudo_novo (str): Conteúdo completo a ser processado em chunks
        """
        # Armazena o conteúdo completo no treinamento
        treinamento.conteudo = conteudo_novo
        treinamento.save(update_fields=['conteudo'])
        
        # Limpa documentos existentes
        cls.limpar_documentos_por_treinamento(treinamento.pk)
        
        if not conteudo_novo or not conteudo_novo.strip():
            logger.info(f"Conteúdo vazio para treinamento {treinamento.pk}")
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
                    "treinamento_id": str(treinamento.pk),
                    "tag": treinamento.tag,
                    "grupo": treinamento.grupo
                }
            )
            
            # Divide documentos em chunks
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=SERVICEHUB.CHUNK_SIZE, 
                chunk_overlap=SERVICEHUB.CHUNK_OVERLAP
            )
            chunks = splitter.split_documents([temp_document])
            
            # Cria registros Documento para cada chunk
            cls.criar_documentos_from_chunks(treinamento, chunks)
            
            logger.info(f"Processados {len(chunks)} chunks para treinamento {treinamento.pk}")
            
        except Exception as e:
            logger.error(f"Erro ao processar conteúdo em chunks: {e}")
            raise

    @classmethod
    def criar_documentos_from_chunks(cls, treinamento, documentos_langchain: List[Document]) -> None:
        """Cria registros Documento a partir de uma lista de objetos Document do LangChain.
        
        Args:
            treinamento: Instância do modelo Treinamento
            documentos_langchain: Lista de objetos Document do LangChain
        """
        if len(documentos_langchain) == 0:
            logger.info(f"Lista de documentos vazia para treinamento {treinamento.pk}")
            return

        try:
            # Limpa documentos existentes
            cls.limpar_documentos_por_treinamento(treinamento.pk)

            # Cria novos registros Documento
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
                    doc_obj = cls(
                        treinamento=treinamento,
                        conteudo=documento.page_content or "",
                        metadata=documento.metadata or {},
                        ordem=i + 1,
                    )
                    # O embedding é gerado automaticamente no save() se o treinamento estiver finalizado
                    doc_obj.save()
                    documentos_criados.append(doc_obj)
                    sucesso += 1
                except Exception as e:
                    logger.error(f"Erro ao criar documento {i}: {e}")
                    erros += 1

            # Atualiza status de vetorização do treinamento apenas se estiver finalizado
            if treinamento.treinamento_finalizado:
                if erros == 0:
                    treinamento.treinamento_vetorizado = True
                    treinamento.save(update_fields=['treinamento_vetorizado'])
                    logger.info(f"Criados {len(documentos_criados)} documentos com embeddings para treinamento {treinamento.pk}")
                else:
                    logger.warning(f"Documentos criados: {len(documentos_criados)}, Sucessos: {sucesso}, Erros: {erros}")
            else:
                logger.info(f"Criados {len(documentos_criados)} documentos para treinamento {treinamento.pk} (embeddings gerados após finalização)")

        except Exception as e:
            error_msg = f"Erro inesperado ao criar documentos: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    @classmethod
    def vetorizar_documentos_por_treinamento(cls, treinamento) -> None:
        """Gera embeddings para documentos que ainda não possuem embedding.
        
        Args:
            treinamento: Instância do modelo Treinamento
        """
        if not treinamento.pk:
            logger.warning("Treinamento deve ser salvo antes de vetorizar documentos")
            return

        documentos_sem_embedding = cls.objects.filter(
            treinamento=treinamento, 
            embedding__isnull=True
        )

        if not documentos_sem_embedding.exists():
            logger.info(f"Todos os documentos do treinamento {treinamento.pk} já estão vetorizados")
            treinamento.treinamento_vetorizado = True
            treinamento.save(update_fields=['treinamento_vetorizado'])
            return

        # Gera embeddings individualmente para ter melhor controle
        sucesso = 0
        erros = 0
        
        for documento in documentos_sem_embedding:
            try:
                documento.gerar_embedding()
                sucesso += 1
            except Exception as e:
                logger.error(f"Erro ao gerar embedding para documento {documento.pk}: {e}")
                erros += 1
        
        # Atualiza status de vetorização
        if erros == 0:
            treinamento.treinamento_vetorizado = True
            # NÃO chama treinamento.finalizar() aqui para evitar loop infinito!
            # O treinamento já está finalizado quando chegamos neste ponto
            treinamento.save(update_fields=['treinamento_vetorizado'])
            logger.info(f"Vetorização concluída: {sucesso} documentos vetorizados")
        else:
            logger.warning(f"Vetorização parcial: {sucesso} sucessos, {erros} erros")

    @classmethod
    def build_similarity_context_v2(
        cls,
        query: str,
        top_k_docs: int = 5,
        grupo: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> str:
        """Versão otimizada da busca semântica usando Documento.

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

        # Busca documentos mais similares diretamente
        documentos_similares = cls.search_by_similarity(
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

    @classmethod
    def search_treinamentos_by_similarity(
        cls,
        query: str,
        top_k: int = 5,
        grupo: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[tuple[Any, float]]:
        """Busca treinamentos mais similares a um texto de consulta.

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

        # Busca documentos similares
        documentos_similares = cls.search_by_similarity(
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
