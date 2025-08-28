"""Datasource para geração de embeddings usando bibliotecas LangChain.

Este módulo implementa a camada de dados para gerar embeddings de texto,
encapsulando a lógica de integração com diferentes provedores de embeddings
como OpenAI, Ollama e HuggingFace através da biblioteca LangChain.
As configurações vêm do ServiceHub seguindo o padrão do projeto.
"""

from langchain_core.embeddings.embeddings import Embeddings
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    GenerateEmbeddingsParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import GEData
from smart_core_assistant_painel.modules.services import SERVICEHUB


class GenerateEmbeddingsLangchainDatasource(GEData):
    """Datasource para gerar embeddings usando LangChain.

    Esta classe encapsula a integração com bibliotecas externas para geração
    de embeddings, usando as configurações do ServiceHub para determinar o
    provedor e modelo apropriados.
    """

    def __call__(self, parameters: GenerateEmbeddingsParameters) -> list[float]:
        """Gera embeddings para o texto fornecido.

        Args:
            parameters (GenerateEmbeddingsParameters): Parâmetros contendo o
                texto para geração de embeddings.

        Returns:
            list[float]: Vetor de embeddings gerado.

        Raises:
            Exception: Em caso de erro na geração dos embeddings.
        """
        try:
            # Criar instância de embeddings usando configurações do ServiceHub
            embeddings_instance: Embeddings = self._create_embeddings_instance()
            
            # Gerar embeddings usando LangChain
            embedding_vector: list[float] = embeddings_instance.embed_query(parameters.text)
            
            return embedding_vector
            
        except Exception as e:
            raise Exception(f"Erro ao gerar embeddings: {str(e)}")
    
    def _create_embeddings_instance(self) -> Embeddings:
        """Cria uma instância de embeddings baseada na configuração do ServiceHub.
        
        Returns:
            Instância do modelo de embeddings configurado.
        """
        embeddings_class: str = SERVICEHUB.EMBEDDINGS_CLASS
        embeddings_model: str = SERVICEHUB.EMBEDDINGS_MODEL
        
        if embeddings_class == "OpenAIEmbeddings":
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(model=embeddings_model)
        
        elif embeddings_class == "OllamaEmbeddings":
            from langchain_ollama import OllamaEmbeddings
            return OllamaEmbeddings(model=embeddings_model)
        
        elif embeddings_class == "HuggingFaceEmbeddings":
            from langchain_community.embeddings import HuggingFaceEmbeddings
            return HuggingFaceEmbeddings(model_name=embeddings_model)
        
        elif embeddings_class == "HuggingFaceInferenceAPIEmbeddings":
            from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
            from pydantic import SecretStr
            return HuggingFaceInferenceAPIEmbeddings(
                api_key=SecretStr(secret_value=SERVICEHUB.HUGGINGFACE_API_KEY),
                model_name=embeddings_model
            )
        
        else:
            # Fallback para OpenAI como padrão
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(model=embeddings_model or "text-embedding-ada-002")
