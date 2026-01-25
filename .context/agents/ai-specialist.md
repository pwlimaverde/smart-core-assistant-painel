# AI/ML Specialist

## Contexto

O AI/ML Specialist é responsável pelo motor de IA do Smart Core Assistant Painel, incluindo LangChain, embeddings, RAG, prompts e integração com provedores de LLM.

---

## Habilidades

- LangChain para orquestração de LLMs
- Desenvolvimento de prompts eficazes
- RAG (Retrieval-Augmented Generation)
- Embeddings e busca semântica
- Integração com múltiplos provedores (OpenAI, Groq, Ollama)
- pgvector para armazenamento de vetores

---

## Stack de IA

| Tecnologia | Uso |
|------------|-----|
| LangChain | Orquestração de LLM |
| OpenAI | Modelos GPT-4, embeddings |
| Groq | Modelos rápidos (Llama) |
| Ollama | Modelos locais |
| pgvector | Armazenamento de embeddings |
| Firebase Remote Config | Gestão de prompts |

---

## Estrutura de Features AI

```
modules/ai_engine/
├── __init__.py
├── features_compose.py          # Factory de features
│
└── features/
    ├── analise_mensage/         # Análise de mensagens
    │   ├── datasource/
    │   ├── domain/
    │   │   ├── model/
    │   │   └── usecase/
    │   └── __init__.py
    │
    ├── generate_embeddings/     # Geração de embeddings
    │   ├── datasource/
    │   ├── domain/
    │   │   └── usecase/
    │   └── __init__.py
    │
    ├── load_document_file/      # Carregamento de documentos
    │   ├── datasource/
    │   ├── domain/
    │   │   └── usecase/
    │   └── __init__.py
    │
    └── generate_chunks/         # Chunking de texto
        ├── domain/
        │   └── usecase/
        └── __init__.py
```

---

## Padrões de Implementação

### Usecase com LangChain

```python
# modules/ai_engine/features/analise_mensage/domain/usecase/analise_mensage_usecase.py

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from py_return_success_or_error import Success, Failure, Result


class AnaliseResult(BaseModel):
    """Resultado da análise de mensagem."""

    intent: str = Field(description="Intenção detectada")
    sentiment: str = Field(description="Sentimento: positivo, negativo, neutro")
    entities: list[str] = Field(default_factory=list, description="Entidades extraídas")
    suggested_response: str = Field(description="Resposta sugerida")


class AnaliseMensageUsecase:
    """Analisa mensagem de cliente usando LLM."""

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm
        self._parser = PydanticOutputParser(pydantic_object=AnaliseResult)
        self._prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", "{message}"),
        ])

    def execute(
        self,
        message: str,
        context: str | None = None,
    ) -> Result[AnaliseResult, Exception]:
        """Executa análise da mensagem."""
        if not message.strip():
            return Failure(ValueError("Mensagem vazia"))

        try:
            chain = self._prompt | self._llm | self._parser
            result = chain.invoke({
                "message": message,
                "context": context or "",
                "format_instructions": self._parser.get_format_instructions(),
            })
            return Success(result)
        except Exception as e:
            return Failure(e)

    def _get_system_prompt(self) -> str:
        return """Você é um assistente de análise de mensagens.
Analise a mensagem do cliente e retorne:
- Intent: a intenção principal
- Sentiment: positivo, negativo ou neutro
- Entities: entidades mencionadas
- Suggested_response: uma resposta adequada

Contexto adicional: {context}

{format_instructions}"""
```

### Geração de Embeddings

```python
# modules/ai_engine/features/generate_embeddings/domain/usecase/generate_embeddings_usecase.py

from langchain_openai import OpenAIEmbeddings
from py_return_success_or_error import Success, Failure, Result


class GenerateEmbeddingsUsecase:
    """Gera embeddings para texto."""

    def __init__(self, model: str = "text-embedding-3-small") -> None:
        self._embeddings = OpenAIEmbeddings(model=model)

    def execute(self, text: str) -> Result[list[float], Exception]:
        """Gera embedding para texto."""
        if not text.strip():
            return Failure(ValueError("Texto vazio"))

        try:
            embedding = self._embeddings.embed_query(text)
            return Success(embedding)
        except Exception as e:
            return Failure(e)

    def execute_batch(
        self,
        texts: list[str],
    ) -> Result[list[list[float]], Exception]:
        """Gera embeddings para múltiplos textos."""
        if not texts:
            return Failure(ValueError("Lista vazia"))

        try:
            embeddings = self._embeddings.embed_documents(texts)
            return Success(embeddings)
        except Exception as e:
            return Failure(e)
```

### RAG com pgvector

```python
# modules/ai_engine/features/rag_search/domain/usecase/rag_search_usecase.py

from pgvector.django import CosineDistance
from py_return_success_or_error import Success, Failure, Result

from app.ui.treinamento.models import DocumentoChunk


class RAGSearchUsecase:
    """Busca documentos relevantes usando RAG."""

    def __init__(self, embeddings_usecase: GenerateEmbeddingsUsecase) -> None:
        self._embeddings = embeddings_usecase

    def execute(
        self,
        query: str,
        tenant_id: int,
        top_k: int = 5,
    ) -> Result[list[DocumentoChunk], Exception]:
        """Busca chunks relevantes para a query."""
        # Gerar embedding da query
        embedding_result = self._embeddings.execute(query)
        if embedding_result.is_failure():
            return embedding_result

        query_embedding = embedding_result.value

        try:
            # Buscar chunks similares
            chunks = (
                DocumentoChunk.objects
                .filter(documento__tenant_id=tenant_id)
                .annotate(
                    distance=CosineDistance("embedding", query_embedding)
                )
                .order_by("distance")[:top_k]
            )
            return Success(list(chunks))
        except Exception as e:
            return Failure(e)
```

---

## Gestão de Prompts

### Firebase Remote Config

```python
# modules/ai_engine/utils/prompt_manager.py

import firebase_admin
from firebase_admin import remote_config


class PromptManager:
    """Gerencia prompts via Firebase Remote Config."""

    def __init__(self) -> None:
        self._template = remote_config.get_template()

    def get_prompt(self, key: str, default: str = "") -> str:
        """Obtém prompt por chave."""
        try:
            param = self._template.parameters.get(key)
            if param and param.default_value:
                return param.default_value.value
            return default
        except Exception:
            return default

    def refresh(self) -> None:
        """Atualiza template do Remote Config."""
        self._template = remote_config.get_template()
```

### Uso de Prompts

```python
# Carregar prompt dinâmico
prompt_manager = PromptManager()
system_prompt = prompt_manager.get_prompt(
    "analise_mensagem_system",
    default="Você é um assistente..."
)
```

---

## Configuração de Provedores

### Seleção Dinâmica de LLM

```python
# modules/ai_engine/utils/llm_factory.py

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_community.llms import Ollama


def create_llm(provider: str, model: str, **kwargs):
    """Factory para criação de LLM."""
    if provider == "openai":
        return ChatOpenAI(model=model, **kwargs)
    elif provider == "groq":
        return ChatGroq(model=model, **kwargs)
    elif provider == "ollama":
        return Ollama(model=model, **kwargs)
    else:
        raise ValueError(f"Provider desconhecido: {provider}")


# Uso
llm = create_llm(
    provider="openai",
    model="gpt-4-turbo",
    temperature=0.7,
)
```

---

## Chunking de Documentos

```python
# modules/ai_engine/features/generate_chunks/domain/usecase/generate_chunks_usecase.py

from langchain.text_splitter import RecursiveCharacterTextSplitter
from py_return_success_or_error import Success, Failure, Result


class GenerateChunksUsecase:
    """Divide documento em chunks."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def execute(self, text: str) -> Result[list[str], Exception]:
        """Divide texto em chunks."""
        if not text.strip():
            return Failure(ValueError("Texto vazio"))

        try:
            chunks = self._splitter.split_text(text)
            return Success(chunks)
        except Exception as e:
            return Failure(e)
```

---

## Ferramentas

```bash
# Testar LLM
python -c "
from langchain_openai import ChatOpenAI
llm = ChatOpenAI()
print(llm.invoke('Olá!'))
"

# Verificar embeddings
python -c "
from langchain_openai import OpenAIEmbeddings
emb = OpenAIEmbeddings()
print(len(emb.embed_query('teste')))
"
```

---

## Restrições

- **SEMPRE** tratar erros de API (rate limits, timeouts)
- **SEMPRE** validar inputs antes de enviar ao LLM
- **SEMPRE** usar Result pattern para retorno
- **NUNCA** expor API keys em logs
- **NUNCA** processar documentos muito grandes de uma vez
- **NUNCA** ignorar custos de API (monitorar usage)
