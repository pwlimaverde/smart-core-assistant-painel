
from py_return_success_or_error import (
    ErrorReturn,
    SuccessReturn,
)

from smart_core_assistant_painel.app.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource import (
    AnaliseConteudoLangchainDatasource, )
from smart_core_assistant_painel.app.features.analise_conteudo.domain.usecase.analise_conteudo_usecase import (
    AnaliseConteudoUseCase, )
from smart_core_assistant_painel.app.features.whatsapp_services.datasource.whatsapp_services_datasource import (
    WhatsappServicesDatasource, )
from smart_core_assistant_painel.app.features.whatsapp_services.domain.usecase.whatsapp_services_usecase import (
    WhatsappServicesUseCase, )
from smart_core_assistant_painel.utils.consts import LLM_CLASS
from smart_core_assistant_painel.utils.erros import LlmError
from smart_core_assistant_painel.utils.parameters import (
    LlmParameters,
    MessageParameters,
)
from smart_core_assistant_painel.utils.types import (
    ACData,
    ACUsecase,
    WSData,
    WSUsecase,
)


class FeaturesCompose:

    @staticmethod
    def send_message_whatsapp(parameters: MessageParameters) -> None:

        dataSource: WSData = WhatsappServicesDatasource()
        usecase: WSUsecase = WhatsappServicesUseCase(dataSource)

        data = usecase(parameters)
        if isinstance(data, ErrorReturn):
            raise data.result

    @staticmethod
    def analise_conteudo() -> str:

        parameters = LlmParameters(
            llm_class=LLM_CLASS,
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

        datasource: ACData = AnaliseConteudoLangchainDatasource()
        usecase: ACUsecase = AnaliseConteudoUseCase(datasource)

        data = usecase(parameters)
        if isinstance(data, SuccessReturn):
            raise data.result
        elif isinstance(data, ErrorReturn):
            raise data.result
        raise ValueError("Unexpected return type from usecase")
