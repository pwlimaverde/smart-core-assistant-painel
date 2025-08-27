"""
Classe responsável por gerenciar embeddings.

Esta classe centraliza todas as operações relacionadas a embeddings,
incluindo geração, configuração de modelos e criação de instâncias.
"""

from typing import List
from django.conf import settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from loguru import logger
from smart_core_assistant_painel.modules.services import SERVICEHUB


class EmbeddingData:
    """
    Classe responsável por operações de embedding.
    
    Centraliza a lógica de geração de embeddings usando diferentes
    provedores (Ollama, OpenAI, HuggingFace).
    """
    
    @staticmethod
    def gerar_embedding_texto(texto: str) -> List[float]:
        """
        Gera embedding para um texto específico.
        
        Args:
            texto: Texto para gerar embedding
            
        Returns:
            Lista de floats representando o embedding
            
        Raises:
            Exception: Se houver erro na geração do embedding
        """
        if not texto.strip():
            logger.warning("Texto vazio para geração de embedding")
            return []
            
        try:
            embeddings_instance = EmbeddingData._criar_instancia_embeddings()
            embedding_vector = embeddings_instance.embed_query(texto)
            return list(map(float, embedding_vector))
            
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            raise
    
    @staticmethod
    def _criar_instancia_embeddings():
        """
        Cria instância de embeddings baseada na configuração do ServiceHub.
        
        Returns:
            Instância configurada do provedor de embeddings
            
        Raises:
            ValueError: Se a classe de embeddings não for suportada
        """
        embeddings_class = SERVICEHUB.EMBEDDINGS_CLASS
        embeddings_model = SERVICEHUB.EMBEDDINGS_MODEL
        
        if embeddings_class == "OllamaEmbeddings":
            return EmbeddingData._criar_ollama_embeddings(embeddings_model)
        
        elif embeddings_class == "OpenAIEmbeddings":
            return EmbeddingData._criar_openai_embeddings(embeddings_model)
        
        elif embeddings_class == "HuggingFaceEmbeddings":
            return EmbeddingData._criar_huggingface_embeddings(embeddings_model)
        
        elif embeddings_class == "HuggingFaceInferenceAPIEmbeddings":
            return EmbeddingData._criar_huggingface_inference_embeddings(embeddings_model)
        
        else:
            # Fallback para OpenAI
            logger.warning(f"Classe de embeddings não reconhecida: {embeddings_class}. Usando OpenAI como fallback.")
            return EmbeddingData._criar_openai_embeddings(embeddings_model)
    
    @staticmethod
    def _criar_ollama_embeddings(modelo: str):
        """Cria instância do OllamaEmbeddings."""
        from langchain_ollama import OllamaEmbeddings
        
        kwargs = {}
        if modelo:
            kwargs["model"] = modelo
        
        base_url = getattr(settings, "OLLAMA_BASE_URL", "")
        if base_url:
            kwargs["base_url"] = base_url
            
        return OllamaEmbeddings(**kwargs)
    
    @staticmethod
    def _criar_openai_embeddings(modelo: str):
        """Cria instância do OpenAIEmbeddings."""
        from langchain_openai import OpenAIEmbeddings
        
        if modelo:
            return OpenAIEmbeddings(model=modelo)
        return OpenAIEmbeddings()
    
    @staticmethod
    def _criar_huggingface_embeddings(modelo: str):
        """Cria instância do HuggingFaceEmbeddings."""
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        
        if modelo:
            return HuggingFaceEmbeddings(model_name=modelo)
        return HuggingFaceEmbeddings()
    
    @staticmethod
    def _criar_huggingface_inference_embeddings(modelo: str):
        """Cria instância do HuggingFaceInferenceAPIEmbeddings."""
        from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
        from pydantic import SecretStr
        import os
        
        api_key = os.environ.get("HUGGINGFACE_API_KEY", "")
        return HuggingFaceInferenceAPIEmbeddings(
            api_key=SecretStr(api_key),
            model_name=modelo
        )
    
    @classmethod
    def gerar_embedding_para_documento(cls, conteudo: str) -> List[float]:
        """
        Método específico para gerar embedding de documentos.
        
        Args:
            conteudo: Conteúdo do documento
            
        Returns:
            Lista de floats do embedding ou lista vazia se falhar
        """
        try:
            return cls.gerar_embedding_texto(conteudo)
        except Exception as e:
            logger.error(f"Erro ao gerar embedding para documento: {e}")
            return []
            
    