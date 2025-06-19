import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dotenv import find_dotenv, load_dotenv
from groq import Groq
from langchain.docstore.document import Document
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredExcelLoader,
)
from langchain_groq import ChatGroq

from smart_core_assistant_painel.app.features.features_compose import FeaturesCompose
from smart_core_assistant_painel.utils.erros import LlmError
from smart_core_assistant_painel.utils.parameters import LlmParameters

load_dotenv(find_dotenv())
client = Groq()


class DocumentProcessor:
    """Processador universal para diferentes tipos de documentos"""

    SUPPORTED_EXTENSIONS = {
        ".pdf": PyPDFLoader,
        ".doc": Docx2txtLoader,
        ".docx": Docx2txtLoader,
        ".txt": TextLoader,
        ".xlsx": UnstructuredExcelLoader,
        ".xls": UnstructuredExcelLoader,
        ".csv": TextLoader,
    }

    # @staticmethod
    # def _pre_analise_document(parameters: LlmParameters) -> str:

    #     llm = parameters.create_llm

    #     messages = ChatPromptTemplate.from_messages([
    #         ('system', parameters.prompt_system),
    #         ('human', '{prompt_human}: {context}')
    #     ])

    #     chain = messages | llm

    #     response = chain.invoke(
    #         {'prompt_human': parameters.prompt_human, 'context': parameters.context, }).content

    #     if isinstance(response, str):
    #         # ✅ Filtrar tags <think> e </think>
    #         cleaned_response = re.sub(
    #             r'<think>.*?</think>',
    #             '',
    #             response,
    #             flags=re.DOTALL)

    #         return cleaned_response.strip()
    #     else:
    #         raise TypeError(
    #             f"Resposta do LLM deve ser uma string, mas recebeu: {
    #                 type(response)}")

    @classmethod
    def load_document(
        cls,
        id: str,
        path: Optional[str],
        tag: str,
        grupo: str,
        conteudo: Optional[str],
    ) -> str:

        try:
            todos_documentos: List[Document] = []

            parameters = LlmParameters(
                llm_class=ChatGroq,
                model='qwen/qwen3-32b',
                extra_params={
                    'temperature': 0},
                prompt_system="""
                    Você é um assistente especializado em organização e análise de documentos
                    empresariais. Sua tarefa é analisar o conteúdo completo de um documento e
                    segmentá-lo em seções, agrupando os trechos correspondentes a cada tema identificado.
                    É imperativo que o conteúdo original do documento seja preservado sem nenhuma
                    alteração — nenhuma frase, palavra ou formatação interna deve ser modificada.

                    Para cumprir essa tarefa, siga as instruções abaixo:

                    1. **Leitura e Compreensão:** Leia atentamente o documento fornecido, identificando
                    todos os temas ou assuntos abordados.

                    2. **Identificação de Temas:** Reconheça os diferentes tópicos presentes no
                    documento. Se o documento não apresentar títulos ou marcadores evidentes,
                    utilize pistas contextuais para inferir os assuntos (por exemplo: Políticas da
                    Empresa, Procedimentos Operacionais, Informações de Contato, etc.).

                    3. **Segregação por Seções:** Separe o texto em seções correspondentes a cada
                    tema identificado. Caso o documento possua trechos que não se encaixem claramente
                    em um tema principal, agrupe-os em uma seção denominada “Outros” ou “Conteúdo
                    Diverso”.

                    4. **Preservação do Conteúdo:** Mantenha inalterado cada trecho do texto original.
                    Sua responsabilidade é apenas organizar o conteúdo, sem realizar qualquer edição,
                    correção ou modificação.

                    5. **Formatação do Resultado:** Apresente o resultado final com um título para cada
                    seção seguido do conteúdo original referente a esse tema. Você pode utilizar o
                    seguinte formato:

                        ----------------------------------------------------

                        **[Título da Seção 1: Nome do Tema]**
                        [Conteúdo original relacionado a esse tema]

                        **[Título da Seção 2: Nome do Tema]**
                        [Conteúdo original relacionado a esse tema]

                        _(Repita para cada tema identificado)_

                    Siga rigorosamente essas diretrizes para garantir que o documento seja segmentado de
                    forma coerente e organizada, sem perder nenhum detalhe do conteúdo original.
                """,
                prompt_human="Analise e organize o conteudo a seguir",
                context="",
                error=LlmError('teste erro'))

            if conteudo:
                # parameters.context = conteudo
                pre_analise = FeaturesCompose.pre_analise_ia_treinamento(
                    conteudo)
                text_doc = Document(
                    page_content=pre_analise,
                )

                todos_documentos.append(text_doc)

            if path:
                ext = Path(path).suffix.lower()

                if ext not in cls.SUPPORTED_EXTENSIONS:
                    raise ValueError(f"Extensão {ext} não suportada")

                loader_class = cls.SUPPORTED_EXTENSIONS[ext]
                loader = loader_class(path)
                documents = loader.load()

                for doc in documents:
                    # parameters.context = doc.page_content
                    pre_analise = FeaturesCompose.pre_analise_ia_treinamento(
                        doc.page_content)
                    doc.page_content = pre_analise

                todos_documentos.extend(documents)

            conteudo_completo = "\n\n".join(
                [doc.page_content for doc in todos_documentos])

            completo_doc = Document(
                id=id,
                page_content=conteudo_completo,
                metadata={
                    "id_treinamento": id,
                    "tag": tag,
                    "grupo": grupo,
                    "source": "treinamento_ia",
                    "processed_at": datetime.now().isoformat(),
                }
            )

            completo_json = completo_doc.model_dump_json(indent=2)

            return completo_json
        except Exception as e:
            raise RuntimeError(
                f"Falha carregar o documento '{id}': {
                    str(e)}") from e


def gerar_documentos(
    id: str,
    path: Optional[str],
    tag: str,
    grupo: str,
    conteudo: Optional[str],
) -> str:
    """
    Gerar documentos RAG a partir de múltiplas fontes

    Args:
        id: Identificador único do documento
        path: Caminho para arquivo (opcional)
        tag: Tag de classificação
        conteudo: Conteúdo direto (opcional)

    Returns:
        str: Resultado do processamento

    Raises:
        ValueError: Quando nem path nem conteudo são fornecidos
        DocumentProcessingError: Quando há erro no processamento
    """
    # Validação de entrada
    if not (path or conteudo):
        raise ValueError(
            "É obrigatório fornecer pelo menos um dos parâmetros: 'path' ou 'conteudo'"
        )

    try:
        treinamento = DocumentProcessor.load_document(
            id=id,
            path=path,
            tag=tag,
            grupo=grupo,
            conteudo=conteudo
        )
        logging.info(f"treinamento {treinamento}")
        return treinamento

    except Exception as e:
        raise RuntimeError(
            f"Falha no processamento do documento '{id}': {
                str(e)}") from e


# def melhoria_texto(texto: str) -> str:

#     parameters = LlmParameters(
#         llm_class=ChatGroq,
#         model='qwen/qwen3-32b',
#         extra_params={
#             'temperature': 0},
#         prompt_system="""
#             Você é um assistente especializado em reedição textual, com foco em
#             aprimorar a clareza e a compreensão dos conteúdos, sem modificar o
#             significado das informações originais. Sua tarefa é receber um documento
#             que já está organizado em seções (cada uma delimitada por um título) e,
#             para cada seção, reescrever o texto de forma a torná-lo mais claro,
# coeso e fácil de entender, mantendo todas as informações intactas.

#             Siga estas instruções:

#             1. **Análise Detalhada:** Leia atentamente cada seção do texto para
#             compreender o contexto e identificar pontos onde a clareza pode ser
#             otimizada.

#             2. **Melhoria da Redação:** Para cada seção, reescreva o texto buscando:
#                 - Estruturar frases de forma mais direta e organizada.
#                 - Utilizar conexões lógicas que mantenham a fluidez do conteúdo.
#                 - Substituir termos confusos ou redundantes por expressões mais claras.
#                 - Preservar o significado e a integridade de todas as informações.

#             3. **Conservação do Conteúdo:** Garanta que nenhum dado, fato ou detalhe
#             importante seja alterado ou omitido. Sua intervenção se dará apenas na
#             forma de apresentação.

#             4. **Formatação do Resultado:** Apresente o documento com cada seção
# devidamente formatada e identificada, utilizando o seguinte modelo:

#                 ----------------------------------------------------
#                 **[Título da Seção: Nome do Tema]**
#                 [Texto aprimorado para maior clareza e compreensão]
#                 ----------------------------------------------------

#             Repita o formato para todas as seções do documento.

#             5. **Revisão Final:** Após a reescrita, revise cada seção para confirmar
#             que o conteúdo original foi preservado e que a nova redação realmente torna
#             o texto mais compreensível sem perder sua essência.
#         """,
#         prompt_human="Aprimore o texto a seguir",
#         context=texto,
#         error=LlmError('teste erro'))

#     return DocumentProcessor._pre_analise_document(parameters)
