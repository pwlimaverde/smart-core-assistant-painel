# import json
# import re
# from typing import Any, list, Optional

# from django.core.exceptions import ValidationError
# from django.db import models
# from django.utils import timezone
# from django.conf import settings
# from pgvector.django import VectorField, CosineDistance
# from langchain.docstore.document import Document
# from loguru import logger
# from smart_core_assistant_painel.modules.services import SERVICEHUB

# from .models_departamento import Departamento


# def validate_tag(value: str) -> None:
#     """
#     Valida se a tag está em formato válido.

#     A tag deve estar em minúsculo, sem espaços, com no máximo 40 caracteres
#     e conter apenas letras minúsculas, números e underscore.

#     Args:
#         value (str): Valor da tag a ser validada

#     Raises:
#         ValidationError: Se a tag não atender aos critérios de validação

#     Examples:
#         >>> validate_tag("minha_tag_123")  # válida
#         >>> validate_tag("MinhaTag")       # inválida - maiúsculas
#         >>> validate_tag("minha tag")      # inválida - espaço
#     """
#     if len(value) > 40:
#         raise ValidationError("Tag deve ter no máximo 40 caracteres.")

#     if " " in value:
#         raise ValidationError("Tag não deve conter espaços.")

#     if not value.islower():
#         raise ValidationError("Tag deve conter apenas letras minúsculas.")

#     # Opcional: validar se contém apenas letras, números e underscore
#     if not re.match(r"^[a-z0-9_]+$", value):
#         raise ValidationError(
#             "Tag deve conter apenas letras minúsculas, números e underscore."
#         )


# class Documento(models.Model):
#     """
#     Modelo que representa um documento vetorizado individual.
    
#     Cada instância armazena um chunk de conteúdo de treinamento
#     com seu respectivo embedding vetorial para busca semântica.
#     """
    
#     # Relacionamento com Treinamento (1:N)
#     treinamento: models.ForeignKey = models.ForeignKey(
#         "Treinamentos",
#         on_delete=models.CASCADE,
#         related_name="documentos",
#         help_text="Treinamento ao qual este documento pertence",
#     )
    
#     # Conteúdo do documento (chunk)
#     conteudo: models.TextField = models.TextField(
#         blank=True,
#         null=True,
#         help_text="Conteúdo do chunk de treinamento",
#     )
    
#     # Metadados do documento
#     metadata: models.JSONField = models.JSONField(
#         default=dict,
#         blank=True,
#         help_text="Metadados do documento (tag, grupo, source, etc.)",
#     )
    
#     # Embedding vetorial (1024 dimensões)
#     embedding: VectorField = VectorField(
#         dimensions=1024,
#         null=True,
#         blank=True,
#         help_text="Vetor de embeddings do conteúdo do documento",
#     )
    
#     # Ordem do documento no treinamento
#     ordem: models.PositiveIntegerField = models.PositiveIntegerField(
#         default=1,
#         help_text="Ordem do documento no treinamento",
#     )
    
#     # Timestamps
#     data_criacao: models.DateTimeField = models.DateTimeField(
#         auto_now_add=True,
#         help_text="Data de criação do documento",
#     )
    
#     class Meta:
#         verbose_name = "Documento"
#         verbose_name_plural = "Documentos"
#         ordering = ["treinamento", "ordem"]
#         indexes = [
#             models.Index(fields=["treinamento", "ordem"]),
#             models.Index(fields=["data_criacao"]),
#         ]

#     def __str__(self):
#         """
#         Retorna representação string do objeto.

#         Returns:
#             str: Conteúdo truncado do documento
#         """
#         if self.conteudo:
#             return f"Documento {self.pk}: {self.conteudo[:50]}..."
#         return f"Documento {self.pk} (vazio)"

#     def save(self, *args, **kwargs):
#         """
#         Salva o documento, gerando o embedding antes se necessário.
#         """
#         # Gera embedding antes de salvar se não existir
#         if not self.embedding and self.conteudo and self.conteudo.strip():
#             try:
#                 self.gerar_embedding_sem_salvar()
#             except Exception as e:
#                 logger.error(f"Erro ao gerar embedding antes de salvar documento: {e}")
#                 # Continua salvando mesmo se o embedding falhar
        
#         super().save(*args, **kwargs)
    
#     def gerar_embedding(self) -> None:
#         """
#         Gera o embedding do documento e salva no banco.
        
#         Raises:
#             EmbeddingError: Se houver erro na geração do embedding
#         """
#         self.gerar_embedding_sem_salvar()
#         if self.pk:
#             self.save(update_fields=['embedding'])
#         else:
#             logger.warning("Documento ainda não foi salvo, embedding será salvo junto")

#     def gerar_embedding_sem_salvar(self) -> None:
#         """
#         Gera o embedding do documento sem salvar no banco.
        
#         Raises:
#             EmbeddingError: Se houver erro na geração do embedding
#         """
#         if not self.conteudo or not self.conteudo.strip():
#             logger.warning(f"Conteúdo vazio para documento {self.pk or 'novo'}")
#             return

#         try:
#             # Importações e configurações
#             from smart_core_assistant_painel.modules.services import SERVICEHUB
            
#             # Criar instância de embeddings usando configurações do ServiceHub
#             embeddings_class = SERVICEHUB.EMBEDDINGS_CLASS
#             embeddings_model = SERVICEHUB.EMBEDDINGS_MODEL
            
#             # Criar instância de embeddings baseada na configuração do ServiceHub
#             if embeddings_class == "OpenAIEmbeddings":
#                 from langchain_openai import OpenAIEmbeddings
#                 embeddings_instance = OpenAIEmbeddings(model=embeddings_model)
            
#             elif embeddings_class == "OllamaEmbeddings":
#                 from langchain_ollama import OllamaEmbeddings
#                 embeddings_instance = OllamaEmbeddings(model=embeddings_model)
            
#             elif embeddings_class == "HuggingFaceEmbeddings":
#                 from langchain_community.embeddings import HuggingFaceEmbeddings
#                 embeddings_instance = HuggingFaceEmbeddings(model_name=embeddings_model)
            
#             elif embeddings_class == "HuggingFaceInferenceAPIEmbeddings":
#                 from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
#                 from pydantic import SecretStr
#                 import os
#                 api_key = os.environ.get("HUGGINGFACE_API_KEY", "")
#                 embeddings_instance = HuggingFaceInferenceAPIEmbeddings(
#                     api_key=SecretStr(api_key),
#                     model_name=embeddings_model
#                 )
            
#             else:
#                 # Fallback para OpenAI como padrão
#                 from langchain_openai import OpenAIEmbeddings
#                 embeddings_instance = OpenAIEmbeddings(model=embeddings_model or "text-embedding-ada-002")
            
#             # Gerar embeddings usando LangChain
#             embedding_vector = embeddings_instance.embed_query(self.conteudo)
#             self.embedding = embedding_vector
            
#             logger.info(f"Embedding gerado para documento {self.pk or 'novo'}")

#         except Exception as e:
#             error_msg = f"Erro ao gerar embedding para documento {self.pk or 'novo'}: {e}"
#             logger.error(error_msg)
#             raise

#     @classmethod
#     def search_by_similarity(
#         cls,
#         query: str,
#         top_k: int = 5,
#         grupo: Optional[str] = None,
#         tag: Optional[str] = None,
#     ) -> list[tuple["Documento", float]]:
#         """
#         Busca documentos mais similares a um texto de consulta.

#         Args:
#             query (str): Texto de consulta para gerar o embedding
#             top_k (int): Número máximo de resultados
#             grupo (Optional[str]): Filtro opcional por grupo do treinamento
#             tag (Optional[str]): Filtro opcional por tag do treinamento

#         Returns:
#             list[tuple[Documento, float]]: lista de tuplas (documento, distância)
#         """
#         if not query or not query.strip():
#             return []
#         if top_k <= 0:
#             return []

#         # Gera vetor do texto de consulta usando método estático
#         query_vec: list[float] = cls._embed_text_static(query.strip())

#         # Base queryset: documentos de treinamentos finalizados com embedding
#         qs = cls.objects.filter(
#             treinamento__treinamento_finalizado=True,
#             embedding__isnull=False
#         )

#         # Aplicar filtros opcionais
#         if grupo:
#             qs = qs.filter(treinamento__grupo=grupo)
#         if tag:
#             qs = qs.filter(treinamento__tag=tag)

#         # Anota e ordena por distância cosseno
#         qs = qs.annotate(
#             distance=CosineDistance("embedding", query_vec)
#         ).order_by("distance")[:top_k]

#         resultados: list[tuple["Documento", float]] = []
#         for obj in qs:
#             distancia_val: float = float(getattr(obj, "distance", 0.0))
#             resultados.append((obj, distancia_val))

#         return resultados

#     @staticmethod
#     def _embed_text_static(text: str) -> list[float]:
#         """
#         Gera o vetor de embedding para um texto (método estático).

#         Args:
#             text (str): Texto de entrada.

#         Returns:
#             list[float]: Vetor de floats (dimensão 1024).
#         """
#         from smart_core_assistant_painel.modules.services import SERVICEHUB
#         from django.conf import settings
        
#         embeddings_class: str = SERVICEHUB.EMBEDDINGS_CLASS
#         embeddings_model: str = SERVICEHUB.EMBEDDINGS_MODEL

#         try:
#             if embeddings_class == "OllamaEmbeddings":
#                 from langchain_ollama import OllamaEmbeddings
#                 base_url: str = getattr(settings, "OLLAMA_BASE_URL", "")
#                 kwargs: dict[str, Any] = {}
#                 if embeddings_model:
#                     kwargs["model"] = embeddings_model
#                 if base_url:
#                     kwargs["base_url"] = base_url
#                 embeddings = OllamaEmbeddings(**kwargs)
#             elif embeddings_class == "OpenAIEmbeddings":
#                 from langchain_openai import OpenAIEmbeddings
#                 if embeddings_model:
#                     embeddings = OpenAIEmbeddings(model=embeddings_model)
#                 else:
#                     embeddings = OpenAIEmbeddings()
#             elif embeddings_class == "HuggingFaceEmbeddings":
#                 from langchain_huggingface import HuggingFaceEmbeddings
#                 if embeddings_model:
#                     embeddings = HuggingFaceEmbeddings(model_name=embeddings_model)
#                 else:
#                     embeddings = HuggingFaceEmbeddings()
#             else:
#                 raise ValueError(f"Classe de embeddings não suportada: {embeddings_class}")

#             # Gera embedding
#             if hasattr(embeddings, "embed_query"):
#                 vec: list[float] = list(map(float, embeddings.embed_query(text)))
#             else:
#                 docs_vec: list[list[float]] = embeddings.embed_documents([text])
#                 vec = list(map(float, docs_vec[0]))
#             return vec
            
#         except Exception as exc:
#             logger.error(f"Erro ao gerar embedding do texto: {exc}", exc_info=True)
#             raise


# class Treinamentos(models.Model):
#     """
#     Modelo para armazenar informações de treinamento de IA.

#     Este modelo gerencia treinamentos organizados por tags e grupos.
#     O conteúdo completo é armazenado aqui e depois dividido em chunks
#     que são salvos como registros Documento com embeddings individuais.

#     Attributes:
#         id: Chave primária do registro
#         tag: Identificador único do treinamento
#         grupo: Grupo ao qual o treinamento pertence
#         conteudo: Conteúdo completo do treinamento (antes da divisão em chunks)
#         treinamento_finalizado: Status de finalização do treinamento
#         treinamento_vetorizado: Status de vetorização do treinamento
#         data_criacao: Data de criação automática do treinamento
#         data_atualizacao: Data da última atualização
#     """

#     id: models.AutoField = models.AutoField(
#         primary_key=True, help_text="Chave primária do registro"
#     )
#     tag: models.CharField = models.CharField(
#         max_length=40,
#         validators=[validate_tag],
#         blank=False,
#         null=False,
#         help_text="Campo obrigatório para identificar o treinamento",
#     )
#     grupo: models.CharField = models.CharField(
#         max_length=40,
#         validators=[validate_tag],
#         blank=False,
#         null=False,
#         help_text="Campo obrigatório para identificar o grupo do treinamento",
#     )
#     conteudo: models.TextField = models.TextField(
#         blank=True,
#         null=True,
#         help_text="Conteúdo completo do treinamento (antes da divisão em chunks)",
#     )
#     treinamento_finalizado: models.BooleanField = models.BooleanField(
#         default=False,
#         help_text="Indica se o treinamento foi finalizado",
#     )
#     treinamento_vetorizado: models.BooleanField = models.BooleanField(
#         default=False,
#         help_text="Indica se o treinamento foi vetorizado com sucesso",
#     )
#     data_criacao: models.DateTimeField = models.DateTimeField(
#         auto_now_add=True,
#         help_text="Data de criação do treinamento",
#     )
#     data_atualizacao: models.DateTimeField = models.DateTimeField(
#         auto_now=True,
#         help_text="Data da última atualização do treinamento",
#     )

#     class Meta:
#         verbose_name = "Treinamento"
#         verbose_name_plural = "Treinamentos"
#         ordering = ["-data_criacao"]
#         indexes = [
#             models.Index(fields=["tag", "grupo"]),
#             models.Index(fields=["data_criacao"]),
#             models.Index(fields=["treinamento_finalizado", "treinamento_vetorizado"]),
#         ]

#     def clean(self):
#         """
#         Validação personalizada do modelo.

#         Valida que a tag não seja igual ao grupo e executa outras
#         validações customizadas do modelo.

#         Raises:
#             ValidationError: Se houver violação das regras de validação
#         """
#         super().clean()

#         # Validação customizada: tag não pode ser igual ao grupo
#         if self.tag and self.grupo and self.tag == self.grupo:
#             raise ValidationError({"grupo": "O grupo não pode ser igual à tag."})

#     def __str__(self):
#         """
#         Retorna representação string do objeto.

#         Returns:
#             str: Tag do treinamento ou identificador padrão
#         """
#         return str(self.tag) if self.tag else f"Treinamento {self.id}"

#     def processar_conteudo_para_chunks(self, conteudo_novo: str) -> None:
#         """
#         Processa o conteúdo, armazena no treinamento e cria chunks como Documento.
#         Gera embeddings automaticamente e finaliza o treinamento.
        
#         Args:
#             conteudo_novo (str): Conteúdo completo a ser processado
#         """
#         # Armazena o conteúdo completo
#         self.conteudo = conteudo_novo
#         self.save(update_fields=['conteudo'])
        
#         # Limpa documentos existentes
#         self.limpar_documentos()
        
#         if not conteudo_novo or not conteudo_novo.strip():
#             logger.info(f"Conteúdo vazio para treinamento {self.pk}")
#             return
            
#         # Cria chunks usando RecursiveCharacterTextSplitter do LangChain
#         try:
#             from langchain.text_splitter import RecursiveCharacterTextSplitter
#             from smart_core_assistant_painel.modules.services import SERVICEHUB
            
#             # Cria um documento temporário para chunking
#             temp_document = Document(
#                 page_content=conteudo_novo,
#                 metadata={
#                     "source": "treinamento_manual", 
#                     "treinamento_id": str(self.pk),
#                     "tag": self.tag,
#                     "grupo": self.grupo
#                 }
#             )
            
#             # Divide documentos em chunks
#             splitter = RecursiveCharacterTextSplitter(
#                 chunk_size=SERVICEHUB.CHUNK_SIZE, 
#                 chunk_overlap=SERVICEHUB.CHUNK_OVERLAP
#             )
#             chunks = splitter.split_documents([temp_document])
            
#             # Cria registros Documento para cada chunk (com embeddings automáticos)
#             self.criar_documentos(chunks)
            
#             # Finaliza o treinamento automaticamente se todos os embeddings foram criados
#             if self.treinamento_vetorizado:
#                 self.finalizar()
            
#             logger.info(f"Processados {len(chunks)} chunks para treinamento {self.pk}")
            
#         except Exception as e:
#             logger.error(f"Erro ao processar conteúdo em chunks: {e}")
#             raise

#     def criar_documentos(self, documentos_langchain: list[Document]) -> None:
#         """
#         Cria registros Documento a partir de uma lista de objetos Document do LangChain.
#         Os embeddings são gerados automaticamente no método save() de cada documento.

#         Args:
#             documentos_langchain: lista de objetos Document do LangChain

#         Raises:
#             TypeError: Se algum item da lista não for um objeto Document válido
#             ValueError: Se houver erro no processamento dos dados
#         """
#         # Verificação segura da lista para evitar erro de ambiguidade
#         if len(documentos_langchain) == 0:
#             logger.info(f"lista de documentos vazia para treinamento {self.pk}")
#             return

#         try:
#             # Limpa documentos existentes
#             self.limpar_documentos()

#             # Cria novos registros Documento (embeddings gerados automaticamente no save)
#             documentos_criados = []
#             sucesso = 0
#             erros = 0
            
#             for i, documento in enumerate(documentos_langchain):
#                 if not isinstance(documento, Document):
#                     error_msg = f"Item na posição {i} não é um Document válido: {type(documento)}"
#                     logger.error(error_msg)
#                     erros += 1
#                     continue

#                 try:
#                     doc_obj = Documento(
#                         treinamento=self,
#                         conteudo=documento.page_content or "",
#                         metadata=documento.metadata or {},
#                         ordem=i + 1,
#                     )
#                     # O embedding é gerado automaticamente no save()
#                     doc_obj.save()
#                     documentos_criados.append(doc_obj)
#                     sucesso += 1
#                 except Exception as e:
#                     logger.error(f"Erro ao criar documento {i}: {e}")
#                     erros += 1

#             # Atualiza status de vetorização do treinamento
#             if erros == 0:
#                 self.treinamento_vetorizado = True
#                 self.save(update_fields=['treinamento_vetorizado'])
#                 logger.info(f"Criados {len(documentos_criados)} documentos com embeddings para treinamento {self.pk}")
#             else:
#                 logger.warning(f"Documentos criados: {len(documentos_criados)}, Sucessos: {sucesso}, Erros: {erros}")

#         except Exception as e:
#             error_msg = f"Erro inesperado ao criar documentos: {e}"
#             logger.error(error_msg)
#             raise ValueError(error_msg) from e

#     def limpar_documentos(self) -> None:
#         """
#         Remove todos os documentos relacionados a este treinamento.
#         """
#         if self.pk:
#             count = self.documentos.count()
#             self.documentos.all().delete()
#             logger.info(f"Removidos {count} documentos do treinamento {self.pk}")

#     def vetorizar_documentos(self) -> None:
#         """
#         Gera embeddings para documentos que ainda não possuem embedding.
        
#         Este método é usado principalmente para casos onde documentos foram criados
#         sem embeddings ou para reprocessar documentos existentes.
#         """
#         if not self.pk:
#             logger.warning("Treinamento deve ser salvo antes de vetorizar documentos")
#             return

#         documentos_sem_embedding = self.documentos.filter(embedding__isnull=True)

#         if not documentos_sem_embedding.exists():
#             logger.info(f"Todos os documentos do treinamento {self.pk} já estão vetorizados")
#             self.treinamento_vetorizado = True
#             self.save(update_fields=['treinamento_vetorizado'])
#             return

#         # Gera embeddings individualmente para ter melhor controle
#         sucesso = 0
#         erros = 0
        
#         for documento in documentos_sem_embedding:
#             try:
#                 documento.gerar_embedding()
#                 sucesso += 1
#             except Exception as e:
#                 logger.error(f"Erro ao gerar embedding para documento {documento.id}: {e}")
#                 erros += 1
        
#         # Atualiza status de vetorização
#         if erros == 0:
#             self.treinamento_vetorizado = True
#             self.finalizar()  # Finaliza automaticamente se todos os embeddings foram criados
#             self.save(update_fields=['treinamento_vetorizado'])
#             logger.info(f"Vetorização concluída: {sucesso} documentos vetorizados")
#         else:
#             logger.warning(f"Vetorização parcial: {sucesso} sucessos, {erros} erros")

#     def finalizar(self) -> None:
#         """
#         Marca o treinamento como finalizado e persiste no banco.
#         """
#         self.treinamento_finalizado = True
#         self.save(update_fields=["treinamento_finalizado"])
#         logger.info(f"Treinamento {self.pk} finalizado")
#     @classmethod
#     def search_by_similarity(
#         cls,
#         query: str,
#         top_k: int = 5,
#         grupo: Optional[str] = None,
#         tag: Optional[str] = None,
#     ) -> list[tuple["Treinamentos", float]]:
#         """
#         Busca treinamentos mais similares a um texto de consulta.

#         Utiliza a nova arquitetura com Documento para
#         busca semântica mais precisa por documento individual.

#         Args:
#             query (str): Texto de consulta para gerar o embedding.
#             top_k (int): Número máximo de resultados a retornar.
#             grupo (Optional[str]): Filtro opcional por grupo.
#             tag (Optional[str]): Filtro opcional por tag.

#         Returns:
#             list[tuple[Treinamentos, float]]: lista de tuplas
#             (objeto, distancia), ordenada por menor distância.
#         """
#         if not query or not query.strip():
#             return []
#         if top_k <= 0:
#             return []

#         # Busca documentos similares usando Documento
#         documentos_similares = Documento.search_by_similarity(
#             query=query.strip(),
#             top_k=top_k * 3,  # Busca mais para garantir diversidade
#             grupo=grupo,
#             tag=tag,
#         )

#         if not documentos_similares:
#             return []

#         # Agrupa por treinamento e pega a melhor distância
#         treinamentos_scores = {}
#         for documento, distancia in documentos_similares:
#             treinamento = documento.treinamento
#             if treinamento.id not in treinamentos_scores:
#                 treinamentos_scores[treinamento.id] = (treinamento, distancia)
#             else:
#                 # Mantém a menor distância (mais similar)
#                 if distancia < treinamentos_scores[treinamento.id][1]:
#                     treinamentos_scores[treinamento.id] = (treinamento, distancia)

#         # Ordena por distância e retorna top_k
#         resultados = list(treinamentos_scores.values())
#         resultados.sort(key=lambda x: x[1])  # Ordena por distância
        
#         return resultados[:top_k]





#     def clear_all_data(self) -> None:
#         """
#         Limpa completamente todos os dados do treinamento para reutilização.
        
#         Este método é especialmente útil durante edição de treinamentos,
#         garantindo que não haja conflitos ou problemas de ambiguidade.
#         """
#         self.conteudo = ""
#         self.treinamento_finalizado = False
#         self.treinamento_vetorizado = False
        
#         # Limpa documentos se o treinamento já foi salvo
#         self.limpar_documentos()
            
#         logger.info(f"Dados do treinamento {self.pk or 'novo'} limpos completamente")

#     def finalize(self) -> None:
#         """
#         Marca o treinamento como finalizado e persiste no banco.
#         """
#         self.treinamento_finalizado = True
#         self.save(update_fields=["treinamento_finalizado"])

#     # -------------------------
#     # Busca por similaridade (pgvector)
#     # -------------------------

#     @staticmethod
#     def _get_embeddings_instance() -> Any:
#         """Cria a instância de embeddings conforme configuração do ServiceHub.

#         Returns:
#             Any: Instância compatível com LangChain.

#         Raises:
#             ValueError: Quando a classe configurada não é suportada.
#         """
#         embeddings_class: str = SERVICEHUB.EMBEDDINGS_CLASS
#         embeddings_model: str = SERVICEHUB.EMBEDDINGS_MODEL

#         try:
#             if embeddings_class == "OllamaEmbeddings":
#                 # Usa Ollama via URL configurada no settings/env
#                 from langchain_ollama import OllamaEmbeddings

#                 base_url: str = getattr(settings, "OLLAMA_BASE_URL", "")
#                 kwargs: dict[str, Any] = {}
#                 if embeddings_model:
#                     kwargs["model"] = embeddings_model
#                 if base_url:
#                     kwargs["base_url"] = base_url
#                 return OllamaEmbeddings(**kwargs)

#             if embeddings_class == "OpenAIEmbeddings":
#                 from langchain_openai import OpenAIEmbeddings

#                 if embeddings_model:
#                     return OpenAIEmbeddings(model=embeddings_model)
#                 return OpenAIEmbeddings()

#             if embeddings_class == "HuggingFaceEmbeddings":
#                 from langchain_huggingface import HuggingFaceEmbeddings

#                 if embeddings_model:
#                     return HuggingFaceEmbeddings(
#                         model_name=embeddings_model
#                     )
#                 return HuggingFaceEmbeddings()

#             raise ValueError(
#                 "Classe de embeddings não suportada: " f"{embeddings_class}"
#             )
#         except Exception as exc:  # pragma: no cover
#             # Loga erro e repassa para tratamento na chamada
#             logger.error(
#                 "Falha ao criar instancia de embeddings: " f"{exc}",
#                 exc_info=True,
#             )
#             raise

#     @staticmethod
#     def _embed_text(text: str) -> list[float]:
#         """Gera o vetor de embedding para um texto.

#         Usa embed_query (preferível para uma única string) quando disponível,
#         com fallback para embed_documents.

#         Args:
#             text (str): Texto de entrada.

#         Returns:
#             list[float]: Vetor de floats (dimensão 1024).
#         """
#         embeddings = Treinamentos._get_embeddings_instance()

#         try:
#             if hasattr(embeddings, "embed_query"):
#                 vec: list[float] = list(
#                     map(float, embeddings.embed_query(text))
#                 )
#             else:
#                 docs_vec: list[list[float]] = embeddings.embed_documents([text])
#                 vec = list(map(float, docs_vec[0]))
#             return vec
#         except Exception as exc:  # pragma: no cover
#             logger.error(
#                 "Erro ao gerar embedding do texto: " f"{exc}",
#                 exc_info=True,
#             )
#             raise

#     @classmethod
#     def search_by_similarity(
#         cls,
#         query: str,
#         top_k: int = 5,
#         grupo: Optional[str] = None,
#         tag: Optional[str] = None,
#     ) -> list[tuple["Treinamentos", float]]:
#         """Busca treinamentos mais similares a um texto de consulta.

#         Agora utiliza a nova arquitetura com DocumentoVetorizado para
#         busca semântica mais precisa por documento individual.

#         Args:
#             query (str): Texto de consulta para gerar o embedding.
#             top_k (int): Número máximo de resultados a retornar.
#             grupo (Optional[str]): Filtro opcional por grupo.
#             tag (Optional[str]): Filtro opcional por tag.

#         Returns:
#             list[tuple[Treinamentos, float]]: lista de tuplas
#             (objeto, distancia), ordenada por menor distância.
#         """
#         if not query or not query.strip():
#             return []
#         if top_k <= 0:
#             return []

#         # Busca documentos similares usando Documento
#         documentos_similares = Documento.search_by_similarity(
#             query=query.strip(),
#             top_k=top_k * 3,  # Busca mais para garantir diversidade
#             grupo=grupo,
#             tag=tag,
#         )

#         if not documentos_similares:
#             return []

#         # Agrupa por treinamento e pega a melhor distância
#         treinamentos_scores = {}
#         for documento, distancia in documentos_similares:
#             treinamento = documento.treinamento
#             if treinamento.id not in treinamentos_scores:
#                 treinamentos_scores[treinamento.id] = (treinamento, distancia)
#             else:
#                 # Mantém a menor distância (mais similar)
#                 if distancia < treinamentos_scores[treinamento.id][1]:
#                     treinamentos_scores[treinamento.id] = (treinamento, distancia)

#         # Ordena por distância e retorna top_k
#         resultados = list(treinamentos_scores.values())
#         resultados.sort(key=lambda x: x[1])  # Ordena por distância
        
#         return resultados[:top_k]

#     @staticmethod
#     def _cosine_distance(vec_a: list[float], vec_b: list[float]) -> float:
#         """Calcula a distância cosseno entre dois vetores.

#         Retorna valor em [0, 2]; quanto menor, mais similares.

#         Args:
#             vec_a (list[float]): Vetor A.
#             vec_b (list[float]): Vetor B.

#         Returns:
#             float: Distância cosseno (1 - similaridade).
#         """
#         # Tratamento defensivo para vetores vazios
#         if not vec_a or not vec_b:
#             return 1.0

#         # Garante o mesmo tamanho por segurança
#         n = min(len(vec_a), len(vec_b))
#         dot = 0.0
#         norm_a = 0.0
#         norm_b = 0.0
#         for i in range(n):
#             a = float(vec_a[i])
#             b = float(vec_b[i])
#             dot += a * b
#             norm_a += a * a
#             norm_b += b * b

#         if norm_a == 0.0 or norm_b == 0.0:
#             return 1.0

#         cosine = dot / ((norm_a ** 0.5) * (norm_b ** 0.5))
#         return 1.0 - cosine

#     @classmethod
#     def build_similarity_context(
#         cls,
#         query: str,
#         top_k_docs: int = 5,
#         top_k_trainings: int = 5,
#         grupo: Optional[str] = None,
#         tag: Optional[str] = None,
#     ) -> str:
#         """Retorna string com os N documentos mais similares como contexto.

#         Passos:
#         1) Busca treinamentos mais similares via pgvector;
#         2) Coleta os documentos desses treinamentos;
#         3) Gera embeddings em lote destes documentos;
#         4) Calcula distância cosseno para cada documento;
#         5) Retorna uma string estruturada com separadores.

#         Args:
#             query (str): Texto de consulta.
#             top_k_docs (int): Quantidade de documentos no contexto.
#             top_k_trainings (int): Quantidade de treinamentos a considerar.
#             grupo (Optional[str]): Filtro por grupo.
#             tag (Optional[str]): Filtro por tag.

#         Returns:
#             str: Contexto concatenado com '---' entre os chunks.
#         """
#         if not query or not query.strip():
#             return ""
#         if top_k_docs <= 0 or top_k_trainings <= 0:
#             return ""

#         # Embedding da consulta
#         query_vec: list[float] = cls._embed_text(query.strip())

#         # Seleciona treinamentos mais similares (com filtros opcionais)
#         top_trainings = cls.search_by_similarity(
#             query=query,
#             top_k=top_k_trainings,
#             grupo=grupo,
#             tag=tag,
#         )

#         if not top_trainings:
#             return ""

#         # Coleta documentos e metadados (tag/grupo) de cada treinamento
#         docs: list[Document] = []
#         doc_meta: list[tuple[str, str]] = []  # (tag, grupo)
#         for tr_obj, _dist in top_trainings:
#             for doc in tr_obj.get_documentos():
#                 docs.append(doc)
#                 doc_meta.append((tr_obj.tag, tr_obj.grupo))

#         if not docs:
#             return ""

#         # Gera embeddings em lote para os documentos
#         embeddings = cls._get_embeddings_instance()
#         try:
#             docs_vecs_raw = embeddings.embed_documents(
#                 [d.page_content for d in docs]
#             )
#         except Exception as exc:  # pragma: no cover
#             logger.error(
#                 f"Falha ao gerar embeddings dos documentos: {exc}",
#                 exc_info=True,
#             )
#             return ""

#         # Normaliza para list[list[float]]
#         docs_vecs: list[list[float]] = []
#         for vec in docs_vecs_raw:
#             docs_vecs.append([float(x) for x in vec])

#         # Calcula as distâncias cosseno
#         scored: list[tuple[float, int]] = []
#         for idx, vec in enumerate(docs_vecs):
#             dist = cls._cosine_distance(query_vec, vec)
#             scored.append((dist, idx))

#         # Ordena por menor distância (mais similar primeiro)
#         scored.sort(key=lambda t: t[0])

#         # Seleciona os top_k_docs
#         top_scored = scored[:top_k_docs]

#         # Monta a string de contexto
#         lines: list[str] = []
#         lines.append(
#             "Contexto de suporte (documentos mais similares):"
#         )
#         for rank, (dist, i) in enumerate(top_scored, start=1):
#             doc = docs[i]
#             tag_i, grupo_i = doc_meta[i]
#             source = "-"
#             try:
#                 source = str(doc.metadata.get("source", "-"))
#             except Exception:
#                 pass

#             header = (
#                 f"[{rank}] Treinamento={tag_i} | Grupo={grupo_i} | "
#                 f"Fonte={source} | Distância={dist:.4f}"
#             )
#             lines.append(header)
#             lines.append(str(doc.page_content).strip())
#             lines.append("---")

#         return "\n".join(lines)

#     @classmethod
#     def build_similarity_context_v2(
#         cls,
#         query: str,
#         top_k_docs: int = 5,
#         grupo: Optional[str] = None,
#         tag: Optional[str] = None,
#     ) -> str:
#         """
#         Versão otimizada da busca semântica usando Documento.

#         Esta versão é mais eficiente pois utiliza embeddings pré-calculados
#         armazenados na tabela Documento, evitando geração em tempo real.

#         Args:
#             query (str): Texto de consulta
#             top_k_docs (int): Quantidade de documentos no contexto
#             grupo (Optional[str]): Filtro por grupo
#             tag (Optional[str]): Filtro por tag

#         Returns:
#             str: Contexto concatenado com '---' entre os chunks
#         """
#         if not query or not query.strip():
#             return ""
#         if top_k_docs <= 0:
#             return ""

#         # Busca documentos mais similares diretamente
#         documentos_similares = Documento.search_by_similarity(
#             query=query.strip(),
#             top_k=top_k_docs,
#             grupo=grupo,
#             tag=tag,
#         )

#         if not documentos_similares:
#             return ""

#         # Monta a string de contexto
#         lines: list[str] = []
#         lines.append(
#             "Contexto de suporte (documentos mais similares - v2):"
#         )
        
#         for rank, (documento, distancia) in enumerate(documentos_similares, start=1):
#             treinamento = documento.treinamento
#             source = documento.metadata.get("source", "-")

#             header = (
#                 f"[{rank}] Treinamento={treinamento.tag} | Grupo={treinamento.grupo} | "
#                 f"Fonte={source} | Distância={distancia:.4f}"
#             )
#             lines.append(header)
#             lines.append(documento.conteudo.strip())
#             lines.append("---")

#         return "\n".join(lines)

#     class Meta:
#         verbose_name = "Treinamento"
#         verbose_name_plural = "Treinamentos"


# def validate_telefone(value: str) -> None:
#     """
#     Valida se o número de telefone está no formato correto.

#     Verifica se o número tem entre 10 e 15 dígitos (formato brasileiro)
#     e contém apenas números após remover caracteres não numéricos.

#     Args:
#         value (str): Número de telefone a ser validado

#     Raises:
#         ValidationError: Se o número não atender aos critérios de validação

#     Examples:
#         >>> validate_telefone("11999999999")   # válido
#         >>> validate_telefone("+5511999999999") # válido
#         >>> validate_telefone("123")           # inválido - muito curto
#     """
#     # Remove caracteres não numéricos
#     telefone_limpo = re.sub(r"\D", "", value)

#     # Verifica se tem pelo menos 10 dígitos (formato brasileiro)
#     if len(telefone_limpo) < 10 or len(telefone_limpo) > 15:
#         raise ValidationError("Número de telefone deve ter entre 10 e 15 dígitos.")

#     # Verifica se contém apenas números
#     if not telefone_limpo.isdigit():
#         raise ValidationError("Número de telefone deve conter apenas números.")


# def validate_cnpj(value: str) -> None:
#     """
#     Valida se o CNPJ está no formato correto.

#     Verifica se o CNPJ tem 14 dígitos e se o formato está válido.
#     Aceita tanto formato com máscara (XX.XXX.XXX/XXXX-XX) quanto sem.

#     Args:
#         value (str): CNPJ a ser validado

#     Raises:
#         ValidationError: Se o CNPJ não atender aos critérios de validação

#     Examples:
#         >>> validate_cnpj("12.345.678/0001-99")  # válido - com máscara
#         >>> validate_cnpj("12345678000199")       # válido - sem máscara
#         >>> validate_cnpj("123")                  # inválido - muito curto
#     """
#     if not value:
#         return

#     # Remove caracteres não numéricos
#     cnpj_limpo = re.sub(r"\D", "", value)

#     # Verifica se tem exatamente 14 dígitos
#     if len(cnpj_limpo) != 14:
#         raise ValidationError("CNPJ deve ter exatamente 14 dígitos.")

#     # Verifica se contém apenas números
#     if not cnpj_limpo.isdigit():
#         raise ValidationError("CNPJ deve conter apenas números.")

#     # Validação básica para CNPJs conhecidos como inválidos
#     if cnpj_limpo == "00000000000000":
#         raise ValidationError("CNPJ inválido.")


# def validate_cpf(value: str) -> None:
#     """
#     Valida se o CPF está no formato correto.

#     Verifica se o CPF tem 11 dígitos e se o formato está válido.
#     Aceita tanto formato com máscara (XXX.XXX.XXX-XX) quanto sem.

#     Args:
#         value (str): CPF a ser validado

#     Raises:
#         ValidationError: Se o CPF não atender aos critérios de validação

#     Examples:
#         >>> validate_cpf("123.456.789-00")  # válido - com máscara
#         >>> validate_cpf("12345678900")      # válido - sem máscara
#         >>> validate_cpf("123")              # inválido - muito curto
#     """
#     if not value:
#         return

#     # Remove caracteres não numéricos
#     cpf_limpo = re.sub(r"\D", "", value)

#     # Verifica se tem exatamente 11 dígitos
#     if len(cpf_limpo) != 11:
#         raise ValidationError("CPF deve ter exatamente 11 dígitos.")

#     # Verifica se contém apenas números
#     if not cpf_limpo.isdigit():
#         raise ValidationError("CPF deve conter apenas números.")

#     # Validação básica para CPFs conhecidos como inválidos
#     if cpf_limpo == "00000000000":
#         raise ValidationError("CPF inválido.")


# def validate_cep(value: str) -> None:
#     """
#     Valida se o CEP está no formato correto.

#     Verifica se o CEP tem 8 dígitos e se o formato está válido.
#     Aceita tanto formato com hífen (XXXXX-XXX) quanto sem.

#     Args:
#         value (str): CEP a ser validado

#     Raises:
#         ValidationError: Se o CEP não atender aos critérios de validação

#     Examples:
#         >>> validate_cep("01234-567")  # válido - com hífen
#         >>> validate_cep("01234567")   # válido - sem hífen
#         >>> validate_cep("123")        # inválido - muito curto
#     """
#     if not value:
#         return

#     # Remove caracteres não numéricos
#     cep_limpo = re.sub(r"\D", "", value)

#     # Verifica se tem exatamente 8 dígitos
#     if len(cep_limpo) != 8:
#         raise ValidationError("CEP deve ter exatamente 8 dígitos.")

#     # Verifica se contém apenas números
#     if not cep_limpo.isdigit():
#         raise ValidationError("CEP deve conter apenas números.")


# class AtendenteHumano(models.Model):
#     """
#     Modelo para armazenar informações dos atendentes humanos.

#     Representa um atendente humano do sistema com informações completas
#     incluindo dados de contato, credenciais e metadados profissionais.

#     Attributes:
#         id: Chave primária do registro
#         telefone: Número de telefone único do atendente (usado como sessão)
#         nome: Nome completo do atendente
#         cargo: Cargo/função do atendente
#         departamento: Departamento ao qual pertence
#         email: E-mail corporativo do atendente
#         usuario_sistema: Usuário do sistema (se aplicável)
#         ativo: Status de atividade do atendente
#         disponivel: Disponibilidade atual para atendimento
#         max_atendimentos_simultaneos: Máximo de atendimentos simultâneos
#         especialidades: lista de especialidades/áreas de conhecimento
#         horario_trabalho: Horário de trabalho em formato JSON
#         data_cadastro: Data de cadastro no sistema
#         ultima_atividade: Data da última atividade no sistema
#         metadados: Informações adicionais do atendente
#     """

#     id: models.AutoField = models.AutoField(
#         primary_key=True, help_text="Chave primária do registro"
#     )
#     telefone: models.CharField = models.CharField(
#         max_length=20,
#         unique=True,
#         validators=[validate_telefone],
#         null=True,
#         blank=True,
#         help_text="Número de telefone do atendente (usado como sessão única)",
#     )
#     nome: models.CharField = models.CharField(
#         max_length=100, help_text="Nome completo do atendente"
#     )
#     cargo: models.CharField = models.CharField(
#         max_length=100, help_text="Cargo/função do atendente"
#     )
#     departamento: models.ForeignKey = models.ForeignKey(
#         Departamento,
#         on_delete=models.SET_NULL,
#         blank=True,
#         null=True,
#         related_name="atendentes",
#         help_text="Departamento ao qual o atendente pertence",
#     )
#     email: models.EmailField = models.EmailField(
#         blank=True, null=True, help_text="E-mail corporativo do atendente"
#     )
#     usuario_sistema: models.CharField = models.CharField(
#         max_length=50,
#         blank=True,
#         null=True,
#         help_text="Usuário do sistema para login (se aplicável)",
#     )
#     ativo: models.BooleanField = models.BooleanField(
#         default=True, help_text="Status de atividade do atendente"
#     )
#     disponivel: models.BooleanField = models.BooleanField(
#         default=True, help_text="Disponibilidade atual para receber novos atendimentos"
#     )
#     max_atendimentos_simultaneos: models.PositiveIntegerField = (
#         models.PositiveIntegerField(
#             default=5, help_text="Máximo de atendimentos simultâneos permitidos"
#         )
#     )
#     especialidades: models.JSONField = models.JSONField(
#         default=list,
#         blank=True,
#         help_text="lista de especialidades/áreas de conhecimento do atendente",
#     )
#     horario_trabalho: models.JSONField = models.JSONField(
#         default=dict,
#         blank=True,
#         help_text="Horário de trabalho (ex: {'segunda': '08:00-18:00', 'terca': '08:00-18:00'})",
#     )
#     data_cadastro: models.DateTimeField = models.DateTimeField(
#         auto_now_add=True, help_text="Data de cadastro no sistema"
#     )
#     ultima_atividade: models.DateTimeField = models.DateTimeField(
#         auto_now=True, help_text="Data da última atividade no sistema"
#     )
#     metadados: models.JSONField = models.JSONField(
#         default=dict,
#         blank=True,
#         help_text="Informações adicionais do atendente (configurações, preferências, etc.)",
#     )

#     class Meta:
#         verbose_name = "Atendente Humano"
#         verbose_name_plural = "Atendentes Humanos"
#         ordering = ["nome"]

#     def __str__(self):
#         """
#         Retorna representação string do atendente.

#         Returns:
#             str: Nome e cargo do atendente
#         """
#         return f"{self.nome} - {self.cargo}"

#     def save(self, *args, **kwargs):
#         """
#         Salva o atendente normalizando o número de telefone.

#         Normaliza o telefone para formato internacional (+55...) antes
#         de salvar no banco de dados.

#         Args:
#             *args: Argumentos posicionais do método save
#             **kwargs: Argumentos nomeados do método save
#         """
#         # Normaliza o número de telefone
#         if self.telefone:
#             # Remove caracteres não numéricos
#             telefone_limpo = re.sub(r"\D", "", self.telefone)
#             # Adiciona código do país se não tiver
#             if not telefone_limpo.startswith("55"):
#                 telefone_limpo = "55" + telefone_limpo
#             self.telefone = "+" + telefone_limpo

#         super().save(*args, **kwargs)

#     def clean(self) -> None:
#         """
#         Validação personalizada do modelo.

#         Executa validações customizadas do modelo.

#         Raises:
#             ValidationError: Se houver violação das regras de validação
#         """
#         super().clean()

#     def get_atendimentos_ativos(self) -> int:
#         """
#         Retorna a quantidade de atendimentos ativos do atendente.

#         Returns:
#             int: Número de atendimentos ativos
#         """
#         return self.atendimentos.filter(
#             status__in=[
#                 StatusAtendimento.EM_ANDAMENTO,
#                 StatusAtendimento.AGUARDANDO_CONTATO,
#                 StatusAtendimento.AGUARDANDO_ATENDENTE,
#             ]
#         ).count()

#     def pode_receber_atendimento(self) -> bool:
#         """
#         Verifica se o atendente pode receber um novo atendimento.

#         Considera se está ativo, disponível e se não excedeu o limite
#         de atendimentos simultâneos.

#         Returns:
#             bool: True se pode receber atendimento, False caso contrário
#         """
#         if not self.ativo or not self.disponivel:
#             return False

#         atendimentos_ativos = self.get_atendimentos_ativos()
#         return atendimentos_ativos < self.max_atendimentos_simultaneos

#     def adicionar_especialidade(self, especialidade: str) -> None:
#         """
#         Adiciona uma especialidade à lista de especialidades do atendente.

#         Args:
#             especialidade (str): Especialidade a ser adicionada
#         """
#         if not self.especialidades:
#             self.especialidades = []

#         if especialidade not in self.especialidades:
#             self.especialidades.append(especialidade)
#             self.save()

#     def remover_especialidade(self, especialidade: str) -> None:
#         """
#         Remove uma especialidade da lista de especialidades do atendente.

#         Args:
#             especialidade (str): Especialidade a ser removida
#         """
#         if self.especialidades and especialidade in self.especialidades:
#             self.especialidades.remove(especialidade)
#             self.save()


# class Contato(models.Model):
#     """
#     Modelo para armazenar informações dos contatos.

#     Representa um contato do sistema com informações básicas como
#     telefone, nome e metadados. O telefone é usado como identificador único.

#     Attributes:
#         id: Chave primária do registro
#         telefone: Número de telefone único do contato (formato brasileiro sem prefixo)
#         nome_contato: Nome do contato (opcional)
#         data_cadastro: Data de cadastro automática
#         ultima_interacao: Data da última interação (atualizada automaticamente)
#         ativo: Status de atividade do contato
#         metadados: Informações adicionais em formato JSON
#     """

#     id: models.AutoField = models.AutoField(
#         primary_key=True, help_text="Chave primária do registro"
#     )
#     telefone: models.CharField = models.CharField(
#         max_length=20,
#         unique=True,
#         validators=[validate_telefone],
#         help_text="Número de telefone do contato (formato: 5511999999999)",
#     )
#     nome_contato: models.CharField = models.CharField(
#         max_length=100, blank=True, null=True, help_text="Nome do contato"
#     )
#     # Campo de e-mail do contato (opcional), usado para comunicações por e-mail
#     email: models.EmailField = models.EmailField(
#         max_length=254,
#         blank=True,
#         null=True,
#         help_text="E-mail do contato",
#     )
#     nome_perfil_whatsapp: models.CharField = models.CharField(
#         max_length=100,
#         blank=True,
#         null=True,
#         help_text="Nome do perfil cadastrado no WhatsApp do contato",
#     )
#     data_cadastro: models.DateTimeField = models.DateTimeField(
#         auto_now_add=True, help_text="Data de cadastro do contato"
#     )
#     ultima_interacao: models.DateTimeField = models.DateTimeField(
#         auto_now=True, help_text="Data da última interação"
#     )
#     ativo: models.BooleanField = models.BooleanField(
#         default=True, help_text="Status de atividade do contato"
#     )
#     metadados = models.JSONField(
#         default=dict, blank=True, help_text="Informações adicionais do contato"
#     )

#     class Meta:
#         verbose_name = "Contato"
#         verbose_name_plural = "Contatos"
#         ordering = ["-ultima_interacao"]

#     def __str__(self):
#         """
#         Retorna representação string do contato.

#         Returns:
#             str: Nome do contato (ou 'Contato') seguido do telefone
#         """
#         return f"{self.nome_contato or 'Contato'} ({self.telefone})"

#     def save(self, *args, **kwargs):
#         """
#         Salva o contato normalizando o número de telefone.

#         Normaliza o telefone para formato brasileiro (55...) sem prefixo
#         antes de salvar no banco de dados.

#         Args:
#             *args: Argumentos posicionais do método save
#             **kwargs: Argumentos nomeados do método save
#         """
#         # Normaliza o número de telefone
#         if self.telefone:
#             # Remove caracteres não numéricos
#             telefone_limpo = re.sub(r"\D", "", self.telefone)
#             # Adiciona código do país se não tiver
#             if not telefone_limpo.startswith("55"):
#                 telefone_limpo = "55" + telefone_limpo
#             self.telefone = telefone_limpo

#         super().save(*args, **kwargs)


# class Cliente(models.Model):
#     """
#     Modelo para armazenar informações dos clientes.

#     Representa um cliente do sistema com informações completas incluindo
#     dados cadastrais, endereço e relacionamento many-to-many com contatos.

#     Attributes:
#         id: Chave primária do registro
#         nome_fantasia: Nome comum do cliente (obrigatório)
#         razao_social: Nome legal/oficial do cliente
#         tipo: Tipo de pessoa (física ou jurídica)
#         cnpj: CNPJ do cliente (para pessoa jurídica)
#         cpf: CPF do cliente (para pessoa física)
#         telefone: Telefone fixo ou corporativo
#         site: URL/website do cliente
#         ramo_atividade: Área de atuação do cliente
#         observacoes: Informações adicionais
#         cep: Código postal do endereço
#         logradouro: Rua ou avenida
#         numero: Número do endereço
#         complemento: Complemento do endereço
#         bairro: Bairro do cliente
#         cidade: Cidade do cliente
#         uf: Estado do cliente
#         pais: País do cliente
#         contatos: Relacionamento many-to-many com contatos
#         data_cadastro: Data de cadastro automática
#         ultima_atualizacao: Data da última atualização
#         ativo: Status de atividade do cliente
#         metadados: Informações adicionais em formato JSON
#     """

#     id: models.AutoField = models.AutoField(
#         primary_key=True, help_text="Chave primária do registro"
#     )

#     # Dados básicos do cliente
#     nome_fantasia: models.CharField = models.CharField(
#         max_length=200,
#         blank=False,
#         null=False,
#         help_text="Nome comum do cliente (obrigatório)",
#     )
#     razao_social: models.CharField = models.CharField(
#         max_length=200, blank=True, null=True, help_text="Nome legal/oficial do cliente"
#     )
#     tipo: models.CharField = models.CharField(
#         max_length=20,
#         choices=[("fisica", "Pessoa Física"), ("juridica", "Pessoa Jurídica")],
#         blank=True,
#         null=True,
#         help_text="Tipo de pessoa (física ou jurídica)",
#     )
#     cnpj: models.CharField = models.CharField(
#         max_length=18,  # formato XX.XXX.XXX/XXXX-XX
#         blank=True,
#         null=True,
#         validators=[validate_cnpj],
#         help_text="CNPJ do cliente (formato: 12.345.678/0001-99)",
#     )
#     cpf: models.CharField = models.CharField(
#         max_length=14,  # formato XXX.XXX.XXX-XX
#         blank=True,
#         null=True,
#         validators=[validate_cpf],
#         help_text="CPF do cliente informado durante a conversa (formato: 123.456.789-00)",
#     )
#     telefone: models.CharField = models.CharField(
#         max_length=20,
#         blank=True,
#         null=True,
#         validators=[validate_telefone],
#         help_text="Telefone fixo ou corporativo do cliente",
#     )
#     site: models.URLField = models.URLField(
#         blank=True, null=True, help_text="Website do cliente"
#     )
#     ramo_atividade: models.CharField = models.CharField(
#         max_length=200, blank=True, null=True, help_text="Área de atuação do cliente"
#     )
#     observacoes: models.TextField = models.TextField(
#         blank=True, null=True, help_text="Informações adicionais sobre o cliente"
#     )

#     # Dados de endereço
#     cep: models.CharField = models.CharField(
#         max_length=10,  # formato XXXXX-XXX
#         blank=True,
#         null=True,
#         validators=[validate_cep],
#         help_text="CEP do endereço (formato: 12345-678)",
#     )
#     logradouro: models.CharField = models.CharField(
#         max_length=200, blank=True, null=True, help_text="Rua, avenida ou logradouro"
#     )
#     numero: models.CharField = models.CharField(
#         max_length=10, blank=True, null=True, help_text="Número do endereço"
#     )
#     complemento: models.CharField = models.CharField(
#         max_length=100,
#         blank=True,
#         null=True,
#         help_text="Complemento do endereço (sala, andar, etc.)",
#     )
#     bairro: models.CharField = models.CharField(
#         max_length=100, blank=True, null=True, help_text="Bairro do cliente"
#     )
#     cidade: models.CharField = models.CharField(
#         max_length=100, blank=True, null=True, help_text="Cidade do cliente"
#     )
#     uf: models.CharField = models.CharField(
#         max_length=2, blank=True, null=True, help_text="Estado (UF) do cliente"
#     )
#     pais: models.CharField = models.CharField(
#         max_length=50,
#         blank=True,
#         null=True,
#         default="Brasil",
#         help_text="País do cliente",
#     )

#     # Relacionamentos
#     contatos: models.ManyToManyField = models.ManyToManyField(
#         Contato,
#         blank=True,
#         related_name="clientes",
#         help_text="Contatos vinculados ao cliente",
#     )

#     # Campos de controle
#     data_cadastro: models.DateTimeField = models.DateTimeField(
#         auto_now_add=True, help_text="Data de cadastro do cliente"
#     )
#     ultima_atualizacao: models.DateTimeField = models.DateTimeField(
#         auto_now=True, help_text="Data da última atualização"
#     )
#     ativo: models.BooleanField = models.BooleanField(
#         default=True, help_text="Status de atividade do cliente"
#     )
#     metadados: models.JSONField = models.JSONField(
#         default=dict, blank=True, help_text="Informações adicionais do cliente"
#     )

#     class Meta:
#         verbose_name = "Cliente"
#         verbose_name_plural = "Clientes"
#         ordering = ["nome_fantasia"]

#     def __str__(self):
#         """
#         Retorna representação string do cliente.

#         Returns:
#             str: Nome fantasia do cliente
#         """
#         return self.nome_fantasia

#     def save(self, *args, **kwargs):
#         """
#         Salva o cliente normalizando dados antes do salvamento.

#         Normaliza CNPJ, CPF, CEP e telefone para formatos padronizados.

#         Args:
#             *args: Argumentos posicionais do método save
#             **kwargs: Argumentos nomeados do método save
#         """
#         # Normaliza o CNPJ
#         if self.cnpj:
#             cnpj_limpo = re.sub(r"\D", "", self.cnpj)
#             if len(cnpj_limpo) == 14:
#                 # Formata CNPJ: XX.XXX.XXX/XXXX-XX
#                 self.cnpj = f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:14]}"

#         # Normaliza o CPF
#         if self.cpf:
#             cpf_limpo = re.sub(r"\D", "", self.cpf)
#             if len(cpf_limpo) == 11:
#                 # Formata CPF: XXX.XXX.XXX-XX
#                 self.cpf = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:11]}"

#         # Normaliza o CEP
#         if self.cep:
#             cep_limpo = re.sub(r"\D", "", self.cep)
#             if len(cep_limpo) == 8:
#                 # Formata CEP: XXXXX-XXX
#                 self.cep = f"{cep_limpo[:5]}-{cep_limpo[5:]}"

#         # Normaliza o telefone (se fornecido)
#         if self.telefone:
#             telefone_limpo = re.sub(r"\D", "", self.telefone)
#             if len(telefone_limpo) >= 10:
#                 # Para telefone fixo, não adiciona +55 automaticamente
#                 # Mantém formato original se já estiver no padrão internacional
#                 if not self.telefone.startswith("+"):
#                     self.telefone = f"({telefone_limpo[:2]}) {telefone_limpo[2:6]}-{telefone_limpo[6:]}"

#         # Normaliza UF para maiúscula
#         if self.uf:
#             self.uf = self.uf.upper()

#         super().save(*args, **kwargs)

#     def clean(self) -> None:
#         """
#         Validação personalizada do modelo.

#         Executa validações customizadas do modelo.

#         Raises:
#             ValidationError: Se houver violação das regras de validação
#         """
#         super().clean()

#         # Valida se o nome fantasia não está vazio
#         if not self.nome_fantasia or not self.nome_fantasia.strip():
#             raise ValidationError({"nome_fantasia": "Nome fantasia é obrigatório."})

#     def get_endereco_completo(self) -> str:
#         """
#         Retorna o endereço completo formatado.

#         Returns:
#             str: Endereço completo do cliente
#         """
#         partes_endereco = []

#         if self.logradouro:
#             endereco_linha = self.logradouro
#             if self.numero:
#                 endereco_linha += f", {self.numero}"
#             if self.complemento:
#                 endereco_linha += f", {self.complemento}"
#             partes_endereco.append(endereco_linha)

#         if self.bairro:
#             partes_endereco.append(self.bairro)

#         if self.cidade and self.uf:
#             partes_endereco.append(f"{self.cidade} - {self.uf}")
#         elif self.cidade:
#             partes_endereco.append(self.cidade)

#         if self.cep:
#             partes_endereco.append(f"CEP: {self.cep}")

#         if self.pais and self.pais != "Brasil":
#             partes_endereco.append(self.pais)

#         return ", ".join(partes_endereco) if partes_endereco else ""

#     def adicionar_contato(self, contato: "Contato") -> None:
#         """
#         Adiciona um contato ao cliente.

#         Args:
#             contato (Contato): Contato a ser vinculado ao cliente
#         """
#         self.contatos.add(contato)

#     def remover_contato(self, contato: "Contato") -> None:
#         """
#         Remove um contato do cliente.

#         Args:
#             contato (Contato): Contato a ser removido do cliente
#         """
#         self.contatos.remove(contato)

#     def get_contatos_ativos(self):
#         """
#         Retorna todos os contatos ativos vinculados ao cliente.

#         Returns:
#             QuerySet: Contatos ativos do cliente
#         """
#         return self.contatos.filter(ativo=True)

#     def atualizar_metadados(self, chave: str, valor: Any) -> None:
#         """
#         Atualiza uma chave nos metadados do cliente.

#         Args:
#             chave (str): Chave a ser atualizada nos metadados
#             valor: Valor a ser armazenado
#         """
#         if not self.metadados:
#             self.metadados = {}

#         self.metadados[chave] = valor
#         self.save()

#     def get_metadados(self, chave: str, padrao: Any = None) -> Any:
#         """
#         Recupera um valor dos metadados do cliente.

#         Args:
#             chave (str): Chave a ser recuperada dos metadados
#             padrao: Valor padrão se a chave não existir

#         Returns:
#             Valor armazenado na chave ou valor padrão
#         """
#         if not self.metadados:
#             return padrao

#         return self.metadados.get(chave, padrao)


# class StatusAtendimento(models.TextChoices):
#     """
#     Enum para definir os estados possíveis do atendimento.

#     Define todos os status que um atendimento pode ter durante seu ciclo de vida,
#     desde o início até a finalização.
#     """

#     AGUARDANDO_INICIAL = "aguardando_inicial", "Aguardando Interação Inicial"
#     EM_ANDAMENTO = "em_andamento", "Em Andamento"
#     AGUARDANDO_CONTATO = "aguardando_contato", "Aguardando Contato"
#     AGUARDANDO_ATENDENTE = "aguardando_atendente", "Aguardando Atendente"
#     RESOLVIDO = "resolvido", "Resolvido"
#     CANCELADO = "cancelado", "Cancelado"
#     TRANSFERIDO = "transferido", "Transferido para Humano"


# class TipoMensagem(models.TextChoices):
#     """
#     Enum para definir os tipos de mensagem disponíveis no sistema.

#     Define todos os tipos de conteúdo que podem ser enviados e recebidos
#     através dos canais de comunicação, baseado nos tipos suportados pela API.
#     """

#     TEXTO_FORMATADO = (
#         "extendedTextMessage",
#         "Texto com formatação, citações, fontes, etc.",
#     )
#     IMAGEM = "imageMessage", "Imagem recebida, JPG/PNG, com caption possível"
#     VIDEO = "videoMessage", "Vídeo recebido, com legenda possível"
#     AUDIO = "audioMessage", "Áudio recebido (.mp4, .mp3), com duração/ptt"
#     DOCUMENTO = "documentMessage", "Arquivo genérico (PDF, DOCX etc.)"
#     STICKER = "stickerMessage", "Sticker no formato WebP"
#     LOCALIZACAO = "locationMessage", "Coordinates de localização (lat/long)"
#     CONTATO = "contactMessage", "vCard com dados de contato"
#     LISTA = "listMessage", "Mensagem interativa com opções em lista"
#     BOTOES = "buttonsMessage", "Botões clicáveis dentro da mensagem"
#     ENQUETE = "pollMessage", "Opções de enquete dentro da mensagem"
#     REACAO = "reactMessage", "Reação (emoji) a uma mensagem existente"

#     @classmethod
#     def obter_por_chave_json(cls, chave_json: str):
#         """
#         Retorna o tipo de mensagem baseado na chave JSON recebida.

#         Args:
#             chave_json (Optional[str]): Chave JSON do tipo de mensagem (ex: 'extendedTextMessage') ou None

#         Returns:
#             Optional[TipoMensagem]: Tipo de mensagem correspondente ou None se não encontrado ou se chave_json for None

#         Examples:
#             >>> TipoMensagem.obter_por_chave_json('extendedTextMessage')
#             TipoMensagem.TEXTO_FORMATADO
#             >>> TipoMensagem.obter_por_chave_json('imageMessage')
#             TipoMensagem.IMAGEM
#             >>> TipoMensagem.obter_por_chave_json(None)
#             None
#         """

#         # Mapeamento direto das chaves JSON para os tipos
#         mapeamento = {
#             "conversation": cls.TEXTO_FORMATADO,  # Mensagem de texto simples
#             "extendedTextMessage": cls.TEXTO_FORMATADO,
#             "imageMessage": cls.IMAGEM,
#             "videoMessage": cls.VIDEO,
#             "audioMessage": cls.AUDIO,
#             "documentMessage": cls.DOCUMENTO,
#             "stickerMessage": cls.STICKER,
#             "locationMessage": cls.LOCALIZACAO,
#             "contactMessage": cls.CONTATO,
#             "listMessage": cls.LISTA,
#             "buttonsMessage": cls.BOTOES,
#             "pollMessage": cls.ENQUETE,
#             "reactMessage": cls.REACAO,
#         }
#         return mapeamento.get(chave_json, cls.TEXTO_FORMATADO)

#     @classmethod
#     def obter_chave_json(cls, tipo_mensagem):
#         """
#         Retorna a chave JSON correspondente ao tipo de mensagem.

#         Args:
#             tipo_mensagem: Tipo de mensagem do enum

#         Returns:
#             str: Chave JSON correspondente ou None se não encontrado

#         Examples:
#             >>> TipoMensagem.obter_chave_json(TipoMensagem.TEXTO_FORMATADO)
#             'extendedTextMessage'
#             >>> TipoMensagem.obter_chave_json(TipoMensagem.IMAGEM)
#             'imageMessage'
#         """
#         # Como o valor já é a chave JSON (primeiro elemento da tupla), retorna
#         # diretamente
#         if hasattr(tipo_mensagem, "value"):
#             return tipo_mensagem.value
#         return None


# class TipoRemetente(models.TextChoices):
#     """
#     Enum para definir os tipos de remetente das mensagens.

#     Define quem enviou a mensagem para controle do fluxo de interação
#     entre contato, bot e atendente humano.
#     """

#     CONTATO = "contato", "Contato"
#     BOT = "bot", "Bot/Sistema"
#     ATENDENTE_HUMANO = "atendente_humano", "Atendente Humano"


# class Atendimento(models.Model):
#     """
#     Modelo para controlar o fluxo de atendimento.

#     Representa um atendimento completo com controle de status, histórico,
#     contexto da conversa e metadados associados.

#     Attributes:
#         id: Chave primária do registro
#         contato: Contato vinculado ao atendimento
#         status: Status atual do atendimento
#         data_inicio: Data de início do atendimento
#         data_fim: Data de finalização do atendimento
#         assunto: Assunto/resumo do atendimento
#         prioridade: Prioridade do atendimento
#         atendente_humano: Nome do atendente humano (se transferido)
#         contexto_conversa: Contexto atual da conversa
#         historico_status: Histórico de mudanças de status
#         tags: Tags para categorização do atendimento
#         avaliacao: Avaliação do atendimento (1-5)
#         feedback: Feedback do contato
#     """

#     id: models.AutoField = models.AutoField(
#         primary_key=True, help_text="Chave primária do registro"
#     )
#     contato: models.ForeignKey = models.ForeignKey(
#         Contato,
#         on_delete=models.CASCADE,
#         related_name="atendimentos",
#         help_text="Contato vinculado ao atendimento",
#     )
#     status: models.CharField = models.CharField(
#         max_length=20,
#         choices=StatusAtendimento.choices,
#         default=StatusAtendimento.AGUARDANDO_INICIAL,
#         help_text="Status atual do atendimento",
#     )
#     data_inicio: models.DateTimeField = models.DateTimeField(
#         auto_now_add=True, help_text="Data de início do atendimento"
#     )
#     data_fim: models.DateTimeField = models.DateTimeField(
#         blank=True, null=True, help_text="Data de finalização do atendimento"
#     )
#     assunto: models.CharField = models.CharField(
#         max_length=200, blank=True, null=True, help_text="Assunto/resumo do atendimento"
#     )
#     prioridade: models.CharField = models.CharField(
#         max_length=10,
#         choices=[
#             ("baixa", "Baixa"),
#             ("normal", "Normal"),
#             ("alta", "Alta"),
#             ("urgente", "Urgente"),
#         ],
#         default="normal",
#         help_text="Prioridade do atendimento",
#     )
#     atendente_humano: models.ForeignKey = models.ForeignKey(
#         AtendenteHumano,
#         on_delete=models.SET_NULL,
#         blank=True,
#         null=True,
#         related_name="atendimentos",
#         help_text="Atendente humano responsável pelo atendimento (se transferido)",
#     )
#     contexto_conversa: models.JSONField = models.JSONField(
#         default=dict,
#         blank=True,
#         help_text="Contexto atual da conversa (variáveis, estado, etc.)",
#     )
#     historico_status: models.JSONField = models.JSONField(
#         default=list, blank=True, help_text="Histórico de mudanças de status"
#     )
#     tags: models.JSONField = models.JSONField(
#         default=list, blank=True, help_text="Tags para categorização do atendimento"
#     )
#     avaliacao: models.IntegerField = models.IntegerField(
#         blank=True,
#         null=True,
#         choices=[(i, i) for i in range(1, 6)],
#         help_text="Avaliação do atendimento (1-5)",
#     )
#     feedback: models.TextField = models.TextField(
#         blank=True, null=True, help_text="Feedback do contato"
#     )

#     class Meta:
#         verbose_name = "Atendimento"
#         verbose_name_plural = "Atendimentos"
#         ordering = ["-data_inicio"]

#     def __str__(self):
#         """
#         Retorna representação string do atendimento.

#         Returns:
#             str: ID do atendimento, telefone do contato e status atual
#         """
#         return f"Atendimento {self.id} - {self.contato.telefone} ({self.get_status_display()})"

#     def finalizar_atendimento(
#         self, novo_status: str = StatusAtendimento.RESOLVIDO
#     ) -> None:
#         """
#         Finaliza o atendimento alterando o status e registrando a data de fim.

#         Args:
#             novo_status: Status final do atendimento (padrão: RESOLVIDO)
#         """
#         self.status = novo_status
#         self.data_fim = timezone.now()
#         self.adicionar_historico_status(novo_status, "Atendimento finalizado")
#         self.save()

#     def adicionar_historico_status(
#         self, novo_status: str, observacao: str = ""
#     ) -> None:
#         """
#         Adiciona entrada no histórico de status.

#         Args:
#             novo_status: Novo status do atendimento
#             observacao (str): Observação sobre a mudança de status (opcional)
#         """
#         if not self.historico_status:
#             self.historico_status = []

#         self.historico_status.append(
#             {
#                 "status": novo_status,
#                 "timestamp": timezone.now().isoformat(),
#                 "observacao": observacao,
#             }
#         )

#     def atualizar_contexto(self, chave: str, valor: Any) -> None:
#         """
#         Atualiza uma chave no contexto da conversa.

#         Args:
#             chave: Chave a ser atualizada no contexto
#             valor: Valor a ser armazenado
#         """
#         if not self.contexto_conversa:
#             self.contexto_conversa = {}

#         self.contexto_conversa[chave] = valor
#         self.save()

#     def get_contexto(self, chave: str, padrao: Any = None) -> Any:
#         """
#         Recupera um valor do contexto da conversa.

#         Args:
#             chave: Chave a ser recuperada do contexto
#             padrao: Valor padrão se a chave não existir (opcional)

#         Returns:
#             Valor armazenado na chave ou valor padrão
#         """
#         if not self.contexto_conversa:
#             return padrao

#         return self.contexto_conversa.get(chave, padrao)

#     def transferir_para_humano(
#         self, atendente_humano: "AtendenteHumano", observacao: str = ""
#     ) -> None:
#         """
#         Transfere o atendimento para um atendente humano específico.

#         Args:
#             atendente_humano (AtendenteHumano): Atendente que receberá o atendimento
#             observacao (str): Observação sobre a transferência (opcional)

#         Raises:
#             ValidationError: Se o atendente não pode receber o atendimento
#         """
#         if not atendente_humano.pode_receber_atendimento():
#             raise ValidationError(
#                 f"O atendente {atendente_humano.nome} não pode receber novos atendimentos. "
#                 f"Motivos possíveis: inativo, indisponível ou limite de atendimentos atingido."
#             )

#         self.atendente_humano = atendente_humano
#         self.status = StatusAtendimento.TRANSFERIDO
#         self.adicionar_historico_status(
#             StatusAtendimento.TRANSFERIDO,
#             observacao or f"Transferido para {atendente_humano.nome}",
#         )
#         self.save()

#     def liberar_atendente_humano(self, observacao: str = "") -> None:
#         """
#         Remove a atribuição do atendente humano do atendimento.

#         Args:
#             observacao (str): Observação sobre a liberação (opcional)
#         """
#         if self.atendente_humano:
#             nome_anterior = self.atendente_humano.nome
#             self.atendente_humano = None
#             self.adicionar_historico_status(
#                 self.status, observacao or f"Liberado do atendente {nome_anterior}"
#             )
#             self.save()

#     def carregar_historico_mensagens(
#         self, excluir_mensagem_id: Optional[int] = None
#     ) -> dict[str, Any]:
#         """
#         Carrega o histórico completo de todas as mensagens do atendimento.

#         Args:
#             excluir_mensagem_id (Optional[int]): ID da mensagem a ser excluída do histórico
#                 (útil para excluir a mensagem atual ao analisar contexto)

#         Returns:
#             dict: Dicionário contendo:
#                 - 'conteudo_mensagens': lista de strings com o conteúdo das mensagens
#                 - 'intents_detectados': Set com todos os intents únicos detectados
#                 - 'entidades_extraidas': Set com todas as entidades únicas extraídas
#                 - 'historico_atendimentos': lista de strings com histórico de atendimentos anteriores no formato "DD/MM/YYYY - assunto tratado: {assunto}"

#         Example:
#             >>> # Para carregar histórico completo
#             >>> historico = atendimento.carregar_historico_mensagens()
#             >>>
#             >>> # Para carregar histórico excluindo mensagem atual
#             >>> historico = atendimento.carregar_historico_mensagens(excluir_mensagem_id=123)
#             >>> print(f"Total de mensagens: {len(historico['conteudo_mensagens'])}")
#             >>> print(f"Intents únicos: {historico['intents_detectados']}")
#             >>> print(f"Entidades únicas: {historico['entidades_extraidas']}")
#         """
#         try:
#             # Busca todas as mensagens do atendimento ordenadas por timestamp
#             # (mais antigas primeiro)
#             mensagens_query = self.mensagens.all().order_by("timestamp")

#             # Exclui mensagem específica se solicitado
#             if excluir_mensagem_id:
#                 mensagens_query = mensagens_query.exclude(id=excluir_mensagem_id)

#             mensagens = mensagens_query

#             # Inicializa as estruturas de dados
#             conteudo_mensagens = []
#             intents_detectados = set()
#             entidades_extraidas = set()

#             # Processa cada mensagem
#             for mensagem in mensagens:
#                 # Adiciona conteúdo da mensagem
#                 if mensagem.conteudo:
#                     conteudo_mensagens.append(mensagem.conteudo)

#                 # Processa intents detectados
#                 if mensagem.intent_detectado:
#                     # Espera uma lista de dicionários no formato
#                     # {"saudacao": "Olá", "pergunta": "tudo bem?"}
#                     if isinstance(mensagem.intent_detectado, list):
#                         for intent_dict in mensagem.intent_detectado:
#                             if isinstance(intent_dict, dict):
#                                 # Formato padrão: {"saudacao": "Olá"} -
#                                 # pega todos os valores dos intents
#                                 for tipo_intent, valor_intent in intent_dict.items():
#                                     if valor_intent and str(valor_intent).strip():
#                                         intents_detectados.add(
#                                             f"{tipo_intent}: {valor_intent}"
#                                         )

#                         # Se não é uma lista, continua sem processar

#                 # Processa entidades extraídas
#                 if mensagem.entidades_extraidas:
#                     # Espera sempre uma lista de dicionários no formato
#                     # {"tipo": "valor"}
#                     if isinstance(mensagem.entidades_extraidas, list):
#                         for entidade_dict in mensagem.entidades_extraidas:
#                             if isinstance(entidade_dict, dict):
#                                 # Formato padrão: {"pessoa": "João Silva"} -
#                                 # pega todos os valores
#                                 for chave, valor in entidade_dict.items():
#                                     if valor and str(valor).strip():
#                                         entidades_extraidas.add(str(valor))
#                     else:
#                         # Se não é uma lista, loga um aviso
#                         pass

#             # Remove strings vazias das entidades
#             entidades_extraidas.discard("")
#             entidades_extraidas.discard("None")
#             entidades_extraidas.discard("null")

#             # Busca histórico de atendimentos anteriores do contato
#             historico_atendimentos = []
#             atendimentos_anteriores = (
#                 Atendimento.objects.filter(contato=self.contato)
#                 .exclude(id=self.id)
#                 .filter(data_fim__isnull=False)
#                 .order_by("-data_fim")
#             )

#             for atendimento_anterior in atendimentos_anteriores:
#                 if atendimento_anterior.assunto:
#                     data_formatada = atendimento_anterior.data_fim.strftime("%d/%m/%Y")
#                     historico_atendimentos.append(
#                         f"{data_formatada} - assunto tratado: {atendimento_anterior.assunto}"
#                     )

#             resultado = {
#                 "conteudo_mensagens": conteudo_mensagens,
#                 "intents_detectados": intents_detectados,
#                 "entidades_extraidas": entidades_extraidas,
#                 "historico_atendimentos": historico_atendimentos,
#             }

#             return resultado

#         except Exception as e:
#             logger.error(
#                 f"Erro ao carregar histórico de mensagens do atendimento {self.id}: {e}"
#             )
#             return {
#                 "conteudo_mensagens": [],
#                 "intents_detectados": set(),
#                 "entidades_extraidas": set(),
#             }


# class Mensagem(models.Model):
#     """
#     Modelo para armazenar todas as mensagens da conversa.

#     Representa uma mensagem individual dentro de um atendimento, incluindo
#     metadados, tipo de conteúdo e informações de processamento.

#     Attributes:
#         id: Chave primária do registro
#         atendimento: Atendimento ao qual a mensagem pertence
#         tipo: Tipo da mensagem (texto, imagem, áudio, etc.)
#         conteudo: Conteúdo textual da mensagem
#         remetente: Tipo do remetente (contato, bot, atendente_humano)
#         timestamp: Data e hora da mensagem
#         message_id_whatsapp: ID da mensagem no WhatsApp (se aplicável)
#         metadados: Metadados adicionais da mensagem
#         respondida: Indica se a mensagem foi respondida
#         resposta_bot: Resposta gerada pelo bot
#         intent_detectado: Intent detectado pelo processamento de NLP
#         entidades_extraidas: Entidades extraídas da mensagem
#         confianca_resposta: Nível de confiança da resposta do bot
#     """

#     id: models.AutoField = models.AutoField(
#         primary_key=True, help_text="Chave primária do registro"
#     )
#     atendimento: models.ForeignKey = models.ForeignKey(
#         Atendimento,
#         on_delete=models.CASCADE,
#         related_name="mensagens",
#         help_text="Atendimento ao qual a mensagem pertence",
#     )
#     tipo: models.CharField = models.CharField(
#         max_length=25,
#         choices=TipoMensagem.choices,
#         default=TipoMensagem.TEXTO_FORMATADO,
#         help_text="Tipo da mensagem",
#     )
#     conteudo: models.TextField = models.TextField(help_text="Conteúdo da mensagem")
#     remetente: models.CharField = models.CharField(
#         max_length=20,
#         choices=TipoRemetente.choices,
#         default=TipoRemetente.CONTATO,
#         help_text="Tipo do remetente da mensagem",
#     )
#     timestamp: models.DateTimeField = models.DateTimeField(
#         auto_now_add=True, help_text="Timestamp da mensagem"
#     )
#     message_id_whatsapp: models.CharField = models.CharField(
#         max_length=100, blank=True, null=True, help_text="ID da mensagem no WhatsApp"
#     )
#     metadados = models.JSONField(
#         default=dict,
#         blank=True,
#         help_text="Metadados adicionais da mensagem (mídia, localização, etc.)",
#     )
#     respondida: models.BooleanField = models.BooleanField(
#         default=False, help_text="Indica se a mensagem foi respondida"
#     )
#     resposta_bot: models.TextField = models.TextField(
#         blank=True, null=True, help_text="Resposta gerada pelo bot"
#     )
#     intent_detectado = models.JSONField(
#         default=list,
#         blank=True,
#         help_text="Intents detectados pelo processamento de NLP (formato: lista de dicionários como {'saudacao': 'Olá', 'pergunta': 'tudo bem?'})",
#     )
#     entidades_extraidas = models.JSONField(
#         default=list,
#         blank=True,
#         help_text="Entidades extraídas da mensagem (formato: lista de dicionários como {'pessoa': 'João Silva'})",
#     )
#     confianca_resposta: models.FloatField = models.FloatField(
#         blank=True, null=True, help_text="Nível de confiança da resposta do bot (0-1)"
#     )

#     class Meta:
#         verbose_name = "Mensagem"
#         verbose_name_plural = "Mensagens"
#         ordering = ["timestamp"]

#     def __str__(self):
#         """
#         Retorna representação string da mensagem.

#         Returns:
#             str: Remetente e preview do conteúdo
#         """
#         remetente_display = self.get_remetente_display()
#         conteudo_preview = (
#             self.conteudo[:50] + "..." if len(self.conteudo) > 50 else self.conteudo
#         )
#         return f"{remetente_display}: {conteudo_preview}"

#     def marcar_como_respondida(
#         self, resposta: str, confianca: Optional[float] = None
#     ) -> None:
#         """
#         Marca a mensagem como respondida com a resposta fornecida.

#         Args:
#             resposta (str): Resposta gerada para a mensagem
#             confianca (float, optional): Nível de confiança da resposta (0-1)
#         """
#         self.respondida = True
#         self.resposta_bot = resposta
#         if confianca is not None:
#             self.confianca_resposta = confianca
#         self.save()

#     @property
#     def is_from_client(self) -> bool:
#         """
#         Propriedade para compatibilidade com código existente.

#         Returns:
#             bool: True se a mensagem é do contato
#         """
#         return self.remetente == TipoRemetente.CONTATO

#     @property
#     def is_from_bot(self) -> bool:
#         """
#         Verifica se a mensagem é do bot.

#         Returns:
#             bool: True se a mensagem é do bot
#         """
#         return self.remetente == TipoRemetente.BOT

#     def adicionar_intent(self, tipo_intent: str, valor_intent: str) -> None:
#         """
#         Adiciona um intent à lista de intents detectados.

#         Args:
#             tipo_intent (str): Tipo do intent (ex: 'saudacao', 'pergunta', 'solicitacao')
#             valor_intent (str): Valor/conteúdo do intent

#         Example:
#             >>> mensagem.adicionar_intent('saudacao', 'Olá')
#             >>> mensagem.adicionar_intent('pergunta', 'tudo bem?')
#         """
#         if not self.intent_detectado:
#             self.intent_detectado = []

#         # Adiciona o intent como dicionário
#         intent_dict = {tipo_intent: valor_intent}
#         self.intent_detectado.append(intent_dict)

#     def get_intents_por_tipo(self, tipo_intent: str) -> list[str]:
#         """
#         Retorna todos os valores de um tipo específico de intent.

#         Args:
#             tipo_intent (str): Tipo do intent a buscar

#         Returns:
#             list[str]: lista com todos os valores encontrados para o tipo

#         Example:
#             >>> mensagem.get_intents_por_tipo('pergunta')
#             ['tudo bem?', 'vocês produzem cones para crepe?']
#         """
#         valores = []
#         if self.intent_detectado:
#             for intent_dict in self.intent_detectado:
#                 if isinstance(intent_dict, dict) and tipo_intent in intent_dict:
#                     valores.append(intent_dict[tipo_intent])
#         return valores

#     def get_todos_intents(self) -> dict[str, list[str]]:
#         """
#         Retorna todos os intents organizados por tipo.

#         Returns:
#             dict: Dicionário com tipos como chaves e listas de valores

#         Example:
#             >>> mensagem.get_todos_intents()
#             {
#                 'saudacao': ['Olá'],
#                 'pergunta': ['tudo bem?', 'vocês produzem cones para crepe?'],
#                 'solicitacao': ['gostaria de uma cotação de uma embalagem']
#             }
#         """
#         intents_organizados = {}
#         if self.intent_detectado:
#             for intent_dict in self.intent_detectado:
#                 if isinstance(intent_dict, dict):
#                     for tipo, valor in intent_dict.items():
#                         if tipo not in intents_organizados:
#                             intents_organizados[tipo] = []
#                         intents_organizados[tipo].append(valor)
#         return intents_organizados

#     @property
#     def is_from_atendente_humano(self) -> bool:
#         """
#         Verifica se a mensagem é de um atendente humano.

#         Returns:
#             bool: True se a mensagem é de um atendente humano
#         """
#         return self.remetente == TipoRemetente.ATENDENTE_HUMANO


# class FluxoConversa(models.Model):
#     """
#     Modelo para definir fluxos de conversa e estados.

#     Gerencia os fluxos de conversação automatizados do sistema,
#     incluindo condições de entrada, estados e transições.

#     Attributes:
#         id: Chave primária do registro
#         nome: Nome único do fluxo de conversa
#         descricao: Descrição detalhada do fluxo
#         condicoes_entrada: Condições JSON para ativação do fluxo
#         estados: Estados e transições do fluxo em formato JSON
#         ativo: Indica se o fluxo está ativo
#         data_criacao: Data de criação automática
#         data_modificacao: Data de última modificação automática
#     """

#     id: models.AutoField = models.AutoField(
#         primary_key=True, help_text="Chave primária do registro"
#     )
#     nome: models.CharField = models.CharField(
#         max_length=100, unique=True, help_text="Nome do fluxo de conversa"
#     )
#     descricao: models.TextField = models.TextField(
#         blank=True, null=True, help_text="Descrição do fluxo"
#     )
#     condicoes_entrada: models.JSONField = models.JSONField(
#         default=dict, help_text="Condições para entrar neste fluxo"
#     )
#     estados: models.JSONField = models.JSONField(
#         default=dict, help_text="Estados e transições do fluxo"
#     )
#     ativo: models.BooleanField = models.BooleanField(
#         default=True, help_text="Fluxo ativo"
#     )
#     data_criacao: models.DateTimeField = models.DateTimeField(auto_now_add=True)
#     data_modificacao: models.DateTimeField = models.DateTimeField(auto_now=True)

#     class Meta:
#         verbose_name = "Fluxo de Conversa"
#         verbose_name_plural = "Fluxos de Conversa"

#     def __str__(self):
#         """
#         Retorna representação string do fluxo de conversa.

#         Returns:
#             str: Nome do fluxo de conversa
#         """
#         return self.nome


# # Função utilitária para inicializar contato e atendimento
# def inicializar_atendimento_whatsapp(
#     numero_telefone: str,
#     primeira_mensagem: str = "",
#     metadata_contato: Optional[dict[str, Any]] = None,
#     nome_contato: Optional[str] = None,
#     nome_perfil_whatsapp: Optional[str] = None,
# ) -> tuple["Contato", "Atendimento"]:
#     """
#     Inicializa ou recupera um contato e cria um novo atendimento baseado no número do WhatsApp.

#     Args:
#         numero_telefone (str): Número de telefone do contato
#         primeira_mensagem (str, optional): Primeira mensagem recebida do contato
#         metadata_contato (dict, optional): Metadados adicionais do contato
#         nome_contato (str, optional): Nome do contato (se conhecido)
#         nome_perfil_whatsapp (str, optional): Nome do perfil do WhatsApp (pushName)

#     Returns:
#         tuple: Tupla com (contato, atendimento) criados/recuperados

#     Raises:
#         Exception: Se houver erro durante a inicialização
#     """
#     try:
#         # Normaliza o número de telefone
#         telefone_limpo = re.sub(r"\D", "", numero_telefone)
#         if not telefone_limpo.startswith("55"):
#             telefone_limpo = "55" + telefone_limpo
#         telefone_formatado = telefone_limpo

#         # Busca ou cria o contato
#         contato, contato_criado = Contato.objects.get_or_create(
#             telefone=telefone_formatado,
#             defaults={
#                 "nome_contato": nome_contato,
#                 "nome_perfil_whatsapp": nome_perfil_whatsapp,
#                 "metadados": metadata_contato or {},
#                 "ativo": True,
#             },
#         )

#         # Se o contato já existe, atualiza informações se fornecidas
#         if not contato_criado:
#             atualizado = False

#             if nome_contato and not contato.nome_contato:
#                 contato.nome_contato = nome_contato
#                 atualizado = True

#             if (
#                 nome_perfil_whatsapp
#                 and nome_perfil_whatsapp != contato.nome_perfil_whatsapp
#             ):
#                 contato.nome_perfil_whatsapp = nome_perfil_whatsapp
#                 atualizado = True

#             if metadata_contato:
#                 contato.metadados.update(metadata_contato)
#                 atualizado = True

#             if atualizado:
#                 contato.save()

#         # Verifica se existe atendimento em andamento
#         atendimento_ativo = Atendimento.objects.filter(
#             contato=contato,
#             status__in=[
#                 StatusAtendimento.AGUARDANDO_INICIAL,
#                 StatusAtendimento.EM_ANDAMENTO,
#                 StatusAtendimento.AGUARDANDO_CONTATO,
#                 StatusAtendimento.AGUARDANDO_ATENDENTE,
#             ],
#         ).first()

#         # Se não existe atendimento ativo, cria um novo
#         if not atendimento_ativo:
#             atendimento = Atendimento.objects.create(
#                 contato=contato,
#                 status=StatusAtendimento.EM_ANDAMENTO,
#                 contexto_conversa={
#                     "canal": "whatsapp",
#                     "primeira_interacao": True,
#                     "sessao_iniciada": timezone.now().isoformat(),
#                 },
#             )

#             # Adiciona entrada no histórico
#             atendimento.adicionar_historico_status(
#                 StatusAtendimento.EM_ANDAMENTO,
#                 "Atendimento iniciado via WhatsApp",
#             )
#         else:
#             atendimento = atendimento_ativo

#         # REMOVIDO: Não cria mensagem aqui para evitar duplicação
#         # A mensagem será criada na função processar_mensagem_whatsapp

#         return contato, atendimento

#     except Exception as e:
#         logger.error(f"Erro ao inicializar atendimento WhatsApp: {e}")
#         raise


# def buscar_atendimento_ativo(numero_telefone: str) -> Optional["Atendimento"]:
#     """
#     Busca um atendimento ativo para o número de telefone fornecido.

#     Args:
#         numero_telefone (str): Número de telefone do contato

#     Returns:
#         Atendimento: Atendimento ativo ou None se não encontrado

#     Raises:
#         Exception: Se houver erro durante a busca
#     """
#     try:
#         # Normaliza o número de telefone
#         telefone_limpo = re.sub(r"\D", "", numero_telefone)
#         if not telefone_limpo.startswith("55"):
#             telefone_limpo = "55" + telefone_limpo
#         telefone_formatado = telefone_limpo

#         contato = Contato.objects.filter(telefone=telefone_formatado).first()
#         if not contato:
#             return None

#         atendimento = Atendimento.objects.filter(
#             contato=contato,
#             status__in=[
#                 StatusAtendimento.AGUARDANDO_INICIAL,
#                 StatusAtendimento.EM_ANDAMENTO,
#                 StatusAtendimento.AGUARDANDO_CONTATO,
#                 StatusAtendimento.AGUARDANDO_ATENDENTE,
#             ],
#         ).first()

#         return atendimento

#     except Exception as e:
#         logger.error(f"Erro ao buscar atendimento ativo: {e}")
#         return None


# def processar_mensagem_whatsapp(
#     numero_telefone: str,
#     conteudo: str,
#     message_type: str,
#     message_id: str,
#     metadados: Optional[dict[str, Any]] = None,
#     nome_perfil_whatsapp: Optional[str] = None,
#     from_me: bool = False,
# ) -> int:
#     """
#     Processa uma mensagem recebida do WhatsApp.

#     Args:
#         numero_telefone (str): Número de telefone do remetente
#         conteudo (str): Conteúdo da mensagem
#         tipo_mensagem (TipoMensagem): Tipo da mensagem (texto, imagem, etc.)
#         message_id (str, optional): ID da mensagem no WhatsApp
#         metadados (dict, optional): Metadados adicionais da mensagem
#         nome_perfil_whatsapp (str, optional): Nome do perfil do WhatsApp (pushName)
#         remetente (TipoRemetente, optional): Tipo do remetente da mensagem (se já determinado)

#     Returns:
#         Mensagem: Objeto mensagem criado

#     Raises:
#         Exception: Se houver erro durante o processamento
#     """
#     try:
#         if from_me:
#             remetente = TipoRemetente.ATENDENTE_HUMANO
#         else:
#             remetente = TipoRemetente.CONTATO

#         # Busca atendimento ativo ou inicializa novo
#         atendimento = buscar_atendimento_ativo(numero_telefone)

#         if not atendimento:
#             # Se não existe atendimento ativo, inicializa um novo
#             _, atendimento = inicializar_atendimento_whatsapp(
#                 numero_telefone,
#                 conteudo,
#                 metadata_contato=metadados,
#                 nome_perfil_whatsapp=nome_perfil_whatsapp,
#             )

#         # Verifica se a mensagem já foi processada (evita duplicação)
#         if message_id:
#             mensagem_existente = Mensagem.objects.filter(
#                 message_id_whatsapp=message_id, atendimento=atendimento
#             ).first()

#             if mensagem_existente:
#                 return mensagem_existente.id
#         tipo_mensagem = TipoMensagem.obter_por_chave_json(message_type)
#         # Cria a mensagem
#         mensagem = Mensagem.objects.create(
#             atendimento=atendimento,
#             tipo=tipo_mensagem,
#             conteudo=conteudo,
#             remetente=remetente,
#             message_id_whatsapp=message_id,
#             metadados=metadados or {},
#         )

#         # Atualiza timestamp da última interação do contato
#         if remetente == TipoRemetente.CONTATO:
#             atendimento.contato.ultima_interacao = timezone.now()
#             atendimento.contato.save()

#             # Atualiza status do atendimento se for a primeira mensagem
#             if atendimento.status == StatusAtendimento.AGUARDANDO_INICIAL:
#                 atendimento.status = StatusAtendimento.EM_ANDAMENTO
#                 atendimento.adicionar_historico_status(
#                     StatusAtendimento.EM_ANDAMENTO, "Primeira mensagem recebida"
#                 )
#                 atendimento.save()

#         return mensagem.id

#     except Exception as e:
#         logger.error(f"Erro ao processar mensagem WhatsApp: {e}")
#         raise


# def buscar_atendente_disponivel(
#     especialidades: Optional[list[str]] = None,
#     departamento: Optional["Departamento"] = None,
# ) -> Optional["AtendenteHumano"]:
#     """
#     Busca um atendente humano disponível para receber um novo atendimento.

#     Args:
#         especialidades (list, optional): lista de especialidades requeridas
#         departamento (Departamento, optional): Objeto departamento específico

#     Returns:
#         AtendenteHumano: Atendente disponível ou None se nenhum encontrado
#     """
#     try:
#         # Query base: atendentes ativos e disponíveis
#         query = AtendenteHumano.objects.filter(ativo=True, disponivel=True)

#         # Filtra por departamento se especificado
#         if departamento:
#             query = query.filter(departamento=departamento)

#         # Filtra atendentes que podem receber novos atendimentos
#         atendentes_disponiveis = []
#         for atendente in query:
#             if atendente.pode_receber_atendimento():
#                 # Verifica especialidades se especificadas
#                 if especialidades:
#                     if any(esp in atendente.especialidades for esp in especialidades):
#                         atendentes_disponiveis.append(atendente)
#                 else:
#                     atendentes_disponiveis.append(atendente)

#         if not atendentes_disponiveis:
#             return None

#         # Retorna o atendente com menos atendimentos ativos (balanceamento)
#         return min(atendentes_disponiveis, key=lambda a: a.get_atendimentos_ativos())

#     except Exception as e:
#         logger.error(f"Erro ao buscar atendente disponível: {e}")
#         return None


# def transferir_atendimento_automatico(
#     atendimento: "Atendimento",
#     especialidades: Optional[list[str]] = None,
#     departamento: Optional["Departamento"] = None,
# ) -> Optional["AtendenteHumano"]:
#     """
#     Transfere automaticamente um atendimento para um atendente humano disponível.

#     Args:
#         atendimento (Atendimento): Atendimento a ser transferido
#         especialidades (list, optional): lista de especialidades requeridas
#         departamento (Departamento, optional): Objeto departamento específico

#     Returns:
#         AtendenteHumano: Atendente que recebeu o atendimento ou None se nenhum disponível

#     Raises:
#         Exception: Se houver erro durante a transferência
#     """
#     try:
#         atendente = buscar_atendente_disponivel(especialidades, departamento)

#         if not atendente:
#             return None

#         # Realiza a transferência
#         observacao = "Transferência automática do sistema"
#         if especialidades:
#             observacao += f" - Especialidades: {', '.join(especialidades)}"
#         if departamento:
#             observacao += f" - Departamento: {departamento.nome}"

#         atendimento.transferir_para_humano(atendente, observacao)

#         return atendente

#     except Exception as e:
#         logger.error(f"Erro ao transferir atendimento automaticamente: {e}")
#         raise


# def listar_atendentes_por_disponibilidade() -> dict[str, list["AtendenteHumano"]]:
#     """
#     lista todos os atendentes agrupados por disponibilidade.

#     Returns:
#         dict: Dicionário com atendentes agrupados por status de disponibilidade
#     """
#     try:
#         atendentes = AtendenteHumano.objects.filter(ativo=True)

#         resultado: dict[str, list[dict[str, Any]]] = {
#             "disponiveis": [],
#             "ocupados": [],
#             "indisponiveis": [],
#         }

#         for atendente in atendentes:
#             info_atendente = {
#                 "id": atendente.id,
#                 "nome": atendente.nome,
#                 "cargo": atendente.cargo,
#                 "departamento": atendente.departamento.nome
#                 if atendente.departamento
#                 else None,
#                 "telefone": atendente.telefone,
#                 "atendimentos_ativos": atendente.get_atendimentos_ativos(),
#                 "max_atendimentos": atendente.max_atendimentos_simultaneos,
#                 "especialidades": atendente.especialidades,
#             }

#             if not atendente.disponivel:
#                 resultado["indisponiveis"].append(info_atendente)
#             elif atendente.pode_receber_atendimento():
#                 resultado["disponiveis"].append(info_atendente)
#             else:
#                 resultado["ocupados"].append(info_atendente)

#         return resultado

#     except Exception as e:
#         logger.error(f"Erro ao listar atendentes por disponibilidade: {e}")
#         return {"disponiveis": [], "ocupados": [], "indisponiveis": []}


# def enviar_mensagem_atendente(
#     atendimento: "Atendimento",
#     atendente_humano: "AtendenteHumano",
#     conteudo: str,
#     tipo_mensagem: "TipoMensagem" = TipoMensagem.TEXTO_FORMATADO,
#     metadados: Optional[dict[str, Any]] = None,
# ) -> "Mensagem":
#     """
#     Envia uma mensagem de um atendente humano para um atendimento.

#     Args:
#         atendimento (Atendimento): Atendimento onde a mensagem será enviada
#         atendente_humano (AtendenteHumano): Atendente que está enviando a mensagem
#         conteudo (str): Conteúdo da mensagem
#         tipo_mensagem (TipoMensagem): Tipo da mensagem (padrão: TEXTO)
#         metadados (dict, optional): Metadados adicionais da mensagem

#     Returns:
#         Mensagem: Objeto mensagem criado

#     Raises:
#         ValidationError: Se o atendente não estiver associado ao atendimento
#     """
#     try:
#         # Verifica se o atendente está associado ao atendimento
#         if atendimento.atendente_humano != atendente_humano:
#             raise ValidationError(
#                 f"O atendente {atendente_humano.nome} não está associado a este atendimento."
#             )

#         # Cria a mensagem
#         mensagem = Mensagem.objects.create(
#             atendimento=atendimento,
#             tipo=tipo_mensagem,
#             conteudo=conteudo,
#             remetente=TipoRemetente.ATENDENTE_HUMANO,
#             metadados=metadados
#             or {
#                 "atendente_id": atendente_humano.id,
#                 "atendente_nome": atendente_humano.nome,
#             },
#         )

#         # Atualiza a última atividade do atendente
#         atendente_humano.ultima_atividade = timezone.now()
#         atendente_humano.save()

#         return mensagem

#     except Exception as e:
#         logger.error(f"Erro ao enviar mensagem do atendente: {e}")
#         raise
