import math

from py_return_success_or_error import (
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    EmbeddingToTextParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import ETTUsecase


class EmbeddingToTextUseCase(ETTUsecase):
    """Use case para converter um embedding em representação textual.

    Esta classe contém apenas lógica Python pura para processar um vetor
    de embeddings e gerar uma representação textual aproximada. Não utiliza
    datasource por ser processamento local.
    """

    def __call__(
        self, parameters: EmbeddingToTextParameters
    ) -> ReturnSuccessOrError[str]:
        """Converte um vetor de embedding em representação textual.

        Args:
            parameters (EmbeddingToTextParameters): Parâmetros contendo o
                vetor de embedding a ser convertido.

        Returns:
            ReturnSuccessOrError[str]: Um objeto de retorno que contém a
                representação textual do embedding em caso de sucesso
                (SuccessReturn) ou um `AppError` em caso de falha
                (ErrorReturn).
        """
        try:
            embedding = parameters.embedding_vector
            
            if not embedding or len(embedding) == 0:
                error = parameters.error
                error.message = "Vetor de embedding vazio ou inválido"
                return ErrorReturn(error)
            
            # Calcular estatísticas básicas do vetor
            magnitude = self._calculate_magnitude(embedding)
            mean_value = sum(embedding) / len(embedding)
            max_value = max(embedding)
            min_value = min(embedding)
            
            # Identificar dimensões dominantes (valores mais altos)
            dominant_dims = self._get_dominant_dimensions(embedding, top_k=5)
            
            # Gerar representação textual
            text_representation = (
                f"Embedding[dim={len(embedding)}, "
                f"mag={magnitude:.3f}, "
                f"mean={mean_value:.3f}, "
                f"range=[{min_value:.3f}, {max_value:.3f}], "
                f"dominant_dims={dominant_dims}]"
            )
            
            return SuccessReturn(text_representation)
            
        except Exception as e:
            error = parameters.error
            error.message = f"Erro ao converter embedding em texto: {str(e)}"
            return ErrorReturn(error)
    
    def _calculate_magnitude(self, vector: list[float]) -> float:
        """Calcula a magnitude (norma) de um vetor.
        
        Args:
            vector (list[float]): Vetor de embeddings.
            
        Returns:
            float: Magnitude do vetor.
        """
        return math.sqrt(sum(x * x for x in vector))
    
    def _get_dominant_dimensions(self, vector: list[float], top_k: int = 5) -> list[int]:
        """Identifica as dimensões com valores mais altos.
        
        Args:
            vector (list[float]): Vetor de embeddings.
            top_k (int): Número de dimensões a retornar.
            
        Returns:
            list[int]: Índices das dimensões dominantes.
        """
        # Criar lista de (índice, valor absoluto)
        indexed_values = [(i, abs(val)) for i, val in enumerate(vector)]
        
        # Ordenar por valor absoluto decrescente
        indexed_values.sort(key=lambda x: x[1], reverse=True)
        
        # Retornar os top_k índices
        return [idx for idx, _ in indexed_values[:top_k]]