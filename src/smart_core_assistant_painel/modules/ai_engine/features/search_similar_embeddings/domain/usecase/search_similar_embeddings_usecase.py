import math
from typing import Tuple

from py_return_success_or_error import (
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    SearchSimilarEmbeddingsParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import SSEUsecase


class SearchSimilarEmbeddingsUseCase(SSEUsecase):
    """Use case para buscar embeddings similares usando cálculo de distância.

    Esta classe contém apenas lógica Python pura para calcular similaridade
    entre embeddings usando distância cosseno. Não utiliza datasource por
    ser processamento matemático local.
    """

    def __call__(
        self, parameters: SearchSimilarEmbeddingsParameters
    ) -> ReturnSuccessOrError[list[dict]]:
        """Busca embeddings similares ao embedding de consulta.

        Args:
            parameters (SearchSimilarEmbeddingsParameters): Parâmetros contendo
                o embedding de consulta, dados para busca e número de resultados.

        Returns:
            ReturnSuccessOrError[list[dict]]: Um objeto de retorno que contém
                uma lista ordenada por similaridade em caso de sucesso
                (SuccessReturn) ou um `AppError` em caso de falha
                (ErrorReturn).
        """
        try:
            query_embedding = parameters.query_embedding
            embeddings_data = parameters.embeddings_data
            top_k = parameters.top_k
            
            if not query_embedding or len(query_embedding) == 0:
                error = parameters.error
                error.message = "Embedding de consulta vazio ou inválido"
                return ErrorReturn(error)
            
            if not embeddings_data or len(embeddings_data) == 0:
                error = parameters.error
                error.message = "Dados de embeddings vazios ou inválidos"
                return ErrorReturn(error)
            
            # Calcular similaridades
            similarities = []
            
            for item in embeddings_data:
                if 'embedding' not in item:
                    continue
                    
                item_embedding = item['embedding']
                if not item_embedding or len(item_embedding) != len(query_embedding):
                    continue
                
                # Calcular similaridade cosseno
                similarity = self._cosine_similarity(query_embedding, item_embedding)
                
                # Criar resultado com similaridade
                result_item = dict(item)  # Copia todos os dados originais
                result_item['similarity'] = similarity
                similarities.append(result_item)
            
            # Ordenar por similaridade (decrescente - mais similar primeiro)
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Retornar top_k resultados
            top_results = similarities[:top_k]
            
            return SuccessReturn(top_results)
            
        except Exception as e:
            error = parameters.error
            error.message = f"Erro ao buscar embeddings similares: {str(e)}"
            return ErrorReturn(error)
    
    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calcula a similaridade cosseno entre dois vetores.
        
        Args:
            vec1 (list[float]): Primeiro vetor.
            vec2 (list[float]): Segundo vetor.
            
        Returns:
            float: Similaridade cosseno (entre -1 e 1).
        """
        # Produto escalar
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        # Evitar divisão por zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Similaridade cosseno
        return dot_product / (magnitude1 * magnitude2)