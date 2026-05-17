"""Usecase para extração de campos personalizados."""

from __future__ import annotations

from py_return_success_or_error import (
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.features.extracao_campos.datasource.extracao_campos_datasource import (
    ExtracaoCamposDatasource,
)
from smart_core_assistant_painel.modules.ai_engine.features.extracao_campos.domain.model.campo_extraido import (
    CampoExtraido,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import (
    ExtracaoCamposError,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    ExtracaoCamposParameters,
)


class ExtracaoCamposUsecase:
    """Valida parâmetros e delega extração ao datasource."""

    def __call__(
        self, parameters: ExtracaoCamposParameters
    ) -> ReturnSuccessOrError[list[CampoExtraido]]:
        if not parameters.campos_a_extrair:
            return SuccessReturn([])

        if not parameters.historico_conversa:
            return SuccessReturn([])

        try:
            datasource = ExtracaoCamposDatasource()
            resultado = datasource(parameters)
            return SuccessReturn(resultado)
        except Exception as exc:
            return ErrorReturn(
                ExtracaoCamposError(
                    f"Falha na extração de campos para atendimento "
                    f"{parameters.atendimento_id}: {exc}"
                )
            )
