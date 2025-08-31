import os
import argparse

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# Observação: Este script segue a metodologia em docs_dev/normalizacao/
# e os padrões reais do projeto (imports absolutos nos usecases e
# imports relativos na facade features_compose).

console = Console()


# ------------------------- Helpers -------------------------

def get_project_name() -> str:
    """Retorna o nome fixo do projeto (package root)."""
    return "smart_core_assistant_painel"


def sanitize_name(name: str) -> str:
    """Normaliza nome para snake_case básico."""
    return name.strip().lower().replace(" ", "_")


def camel_case(name: str) -> str:
    """Converte snake_case para CamelCase simples."""
    return "".join(word.capitalize() for word in name.split("_"))


def get_feature_initials(feature_name: str) -> str:
    """Gera o acrônimo da feature a partir das palavras (ex: set_environ_remote -> SER).

    - Usa a primeira letra de cada palavra separada por underscore
    - Converte para maiúsculas
    """
    words = [w for w in sanitize_name(feature_name).split("_") if w]
    if not words:
        return "FX"
    return "".join(w[0].upper() for w in words)


# ------------------------- IO utils -------------------------

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def touch_init(path: str) -> None:
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n")


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def append_text(path: str, text: str) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n" + text.rstrip() + "\n")


# --------------------- Content generators -------------------

def gen_error_block(cc_name: str) -> str:
    return (
        "from dataclasses import dataclass\n"
        "from py_return_success_or_error import AppError\n\n"
        f"@dataclass\nclass {cc_name}Error(AppError):\n"
        "    message: str\n\n"
        f"    def __str__(self) -> str:\n"
        f"        return f\"{cc_name}Error - {{self.message}}\"\n"
    )


def gen_parameters_block(cc_name: str) -> str:
    return (
        "from dataclasses import dataclass\n"
        "from typing import Any\n"
        "from py_return_success_or_error import AppError, ParametersReturnResult\n"
        f"from .erros import {cc_name}Error\n\n"
        f"@dataclass\nclass {cc_name}Parameters(ParametersReturnResult):\n"
        "    # TODO: Adicione os atributos específicos da feature aqui\n"
        "    param_exemplo: str = \"valor_default\"\n"
        f"    error: type[AppError] = {cc_name}Error\n\n"
        "    def __str__(self) -> str:\n"
        "        return self.__repr__()\n"
    )


def gen_types_block(module: str, cc_name: str, fi: str, feature_type: str) -> str:
    if feature_type == "base":
        return (
            "from typing import TypeAlias\n"
            "from py_return_success_or_error import UsecaseBase\n"
            f"from .parameters import {cc_name}Parameters\n\n"
            f"{fi}Usecase: TypeAlias = UsecaseBase[\n"
            f"    None,\n    {cc_name}Parameters,\n]"
        )
    else:
        return (
            "from typing import TypeAlias\n"
            "from py_return_success_or_error import Datasource, UsecaseBaseCallData\n"
            f"from .parameters import {cc_name}Parameters\n\n"
            f"{fi}Data: TypeAlias = Datasource[None, {cc_name}Parameters]\n"
            f"{fi}Usecase: TypeAlias = UsecaseBaseCallData[\n"
            f"    None,\n    {fi}Data,\n    {cc_name}Parameters,\n]"
        )


def gen_usecase_content(project: str, module: str, cc_name: str, fi: str,
                        snake: str, feature_type: str) -> str:
    abs_utils_params = (
        f"from {project}.modules.{module}.utils.parameters import "
        f"{cc_name}Parameters"
    )
    abs_utils_types = (
        f"from {project}.modules.{module}.utils.types import {fi}Usecase"
    )

    header = (
        "from py_return_success_or_error import (\n"
        "    ErrorReturn, ReturnSuccessOrError, SuccessReturn,\n)\n"
        f"{abs_utils_params}\n{abs_utils_types}\n\n"
        f"class {cc_name}UseCase({fi}Usecase):\n"
        f"    def __call__(self, parameters: {cc_name}Parameters)"
        f" -> ReturnSuccessOrError[None]:\n"
    )

    if feature_type == "base":
        body = (
            "        # TODO: Implementar regra de negócio da feature.\n"
            "        # Retorne SuccessReturn(...) ou ErrorReturn(...).\n"
            "        pass\n"
        )
    else:
        body = (
            "        # Chamada segura ao datasource provida por UsecaseBaseCallData\n"
            "        data = self._resultDatasource(\n"
            "            parameters=parameters, datasource=self._datasource\n        )\n\n"
            "        if isinstance(data, SuccessReturn):\n"
            "            return SuccessReturn(data.result)\n"
            "        elif isinstance(data, ErrorReturn):\n"
            f"            return ErrorReturn(parameters.error(message=\"Erro ao executar {snake}: \" + str(data.result)))\n"
            "        else:\n"
            "            return ErrorReturn(parameters.error(message=\"Tipo de retorno inesperado do datasource.\"))\n"
        )

    return header + body


def gen_datasource_content(project: str, module: str, cc_name: str, fi: str,
                           snake: str) -> str:
    abs_utils_params = (
        f"from {project}.modules.{module}.utils.parameters import "
        f"{cc_name}Parameters"
    )
    abs_utils_types = f"from {project}.modules.{module}.utils.types import {fi}Data"

    return (
        f"{abs_utils_params}\n{abs_utils_types}\n\n"
        f"class {cc_name}Datasource({fi}Data):\n"
        f"    def __call__(self, parameters: {cc_name}Parameters) -> None:\n"
        "        # TODO: Implementar acesso a dados/API.\n"
        "        pass\n"
    )


def build_facade_imports(module: str, snake: str, cc_name: str, fi: str,
                          feature_type: str) -> list[str]:
    lines: list[str] = []
    # py_return_success_or_error (garantir ReturnSuccessOrError)
    base_imp = (
        "from py_return_success_or_error import (ErrorReturn, SuccessReturn, "
        "ReturnSuccessOrError)"
    )
    lines.append(base_imp)

    # utils
    lines.append(f"from ..utils.erros import {cc_name}Error")
    if feature_type == "call_data":
        lines.append(f"from ..utils.types import {fi}Data, {fi}Usecase")
    else:
        lines.append(f"from ..utils.types import {fi}Usecase")
    lines.append(f"from ..utils.parameters import {cc_name}Parameters")

    # feature classes
    if feature_type == "call_data":
        lines.append(
            f"from .{snake}.datasource.{snake}_datasource import {cc_name}Datasource"
        )
    lines.append(
        f"from .{snake}.domain.usecase.{snake}_usecase import {cc_name}UseCase"
    )

    return lines


def build_facade_method(snake: str, cc_name: str, fi: str,
                        feature_type: str) -> str:
    indent = " " * 4
    m: list[str] = []
    m.append(f"{indent}@staticmethod")
    m.append(f"{indent}def {snake}() -> None:")
    m.append(
        f"{indent*2}error = {cc_name}Error(\"Erro ao executar {snake}!\")"
    )
    m.append(
        f"{indent*2}parameters = {cc_name}Parameters(\n{indent*3}# TODO: mapear parâmetros da fachada para os parâmetros do UseCase\n{indent*3}error=error,\n{indent*2})"
    )

    if feature_type == "call_data":
        m.append(
            f"{indent*2}datasource: {fi}Data = {cc_name}Datasource()"
        )
        m.append(
            f"{indent*2}usecase: {fi}Usecase = {cc_name}UseCase(datasource)"
        )
    else:
        m.append(f"{indent*2}usecase: {fi}Usecase = {cc_name}UseCase()")

    m.append(
        f"{indent*2}data: ReturnSuccessOrError[None] = usecase(parameters)"
    )
    m.append(f"{indent*2}if isinstance(data, SuccessReturn):")
    m.append(f"{indent*3}return data.result")
    m.append(f"{indent*2}elif isinstance(data, ErrorReturn):")
    m.append(f"{indent*3}raise data.result")
    m.append(f"{indent*2}else:")
    m.append(
        f"{indent*3}raise ValueError(\"Unexpected return type from usecase\")"
    )

    return "\n".join(m) + "\n"


# ------------------------- Core flow ------------------------

def get_user_input() -> tuple[str, str]:
    module_name = Prompt.ask(
        "[bold cyan]Digite o nome do módulo[/bold cyan] (ex: ai_engine)"
    )
    feature_name = Prompt.ask(
        "[bold cyan]Digite o nome da feature[/bold cyan] (ex: generate_chunks)"
    )
    return sanitize_name(module_name), sanitize_name(feature_name)


def update_utils(module_name: str, feature_name: str, feature_type: str) -> None:
    project = get_project_name()
    cc = camel_case(feature_name)
    fi = get_feature_initials(feature_name)

    utils_dir = os.path.join(
        "src", project, "modules", module_name, "utils"
    )
    erros_path = os.path.join(utils_dir, "erros.py")
    params_path = os.path.join(utils_dir, "parameters.py")
    types_path = os.path.join(utils_dir, "types.py")

    if not (os.path.exists(erros_path) and os.path.exists(params_path)
            and os.path.exists(types_path)):
        raise FileNotFoundError(
            "Arquivos utils não encontrados. Verifique o módulo informado."
        )

    # erros.py
    erros_txt = read_text(erros_path)
    if f"class {cc}Error" not in erros_txt:
        console.log("Inserindo erro em utils/erros.py...")
        append_text(erros_path, gen_error_block(cc))
    else:
        console.log("[yellow]Erro já existe em utils/erros.py[/yellow]")

    # parameters.py
    params_txt = read_text(params_path)
    if f"class {cc}Parameters" not in params_txt:
        console.log("Inserindo parâmetros em utils/parameters.py...")
        append_text(params_path, gen_parameters_block(cc))
    else:
        console.log("[yellow]Parâmetros já existem em utils/parameters.py[/yellow]")

    # types.py
    types_txt = read_text(types_path)
    need_usecase = f"{fi}Usecase" not in types_txt
    need_data = feature_type == "call_data" and f"{fi}Data" not in types_txt
    if need_usecase or need_data:
        console.log("Inserindo tipos em utils/types.py...")
        append_text(types_path, gen_types_block(module_name, cc, fi, feature_type))
    else:
        console.log("[yellow]Tipos já existem em utils/types.py[/yellow]")


def create_feature_files(module_name: str, feature_name: str,
                         feature_type: str) -> None:
    project = get_project_name()
    snake = sanitize_name(feature_name)
    cc = camel_case(feature_name)
    fi = get_feature_initials(feature_name)

    base_dir = os.path.join(
        "src", project, "modules", module_name, "features", snake
    )
    usecase_dir = os.path.join(base_dir, "domain", "usecase")
    ensure_dir(usecase_dir)
    touch_init(os.path.join(base_dir, "__init__.py"))
    touch_init(os.path.join(base_dir, "domain", "__init__.py"))
    touch_init(os.path.join(base_dir, "domain", "usecase", "__init__.py"))

    # usecase file
    usecase_path = os.path.join(usecase_dir, f"{snake}_usecase.py")
    if not os.path.exists(usecase_path):
        content = gen_usecase_content(project, module_name, cc, fi, snake,
                                      feature_type)
        with open(usecase_path, "w", encoding="utf-8") as f:
            f.write(content)
        console.log(f"Usecase criado: [green]{usecase_path}[/green]")
    else:
        console.log("[yellow]Usecase já existe, não sobrescrito[/yellow]")

    # datasource (se call_data)
    if feature_type == "call_data":
        datasource_dir = os.path.join(base_dir, "datasource")
        ensure_dir(datasource_dir)
        touch_init(os.path.join(datasource_dir, "__init__.py"))
        ds_path = os.path.join(datasource_dir, f"{snake}_datasource.py")
        if not os.path.exists(ds_path):
            content = gen_datasource_content(project, module_name, cc, fi, snake)
            with open(ds_path, "w", encoding="utf-8") as f:
                f.write(content)
            console.log(f"Datasource criado: [green]{ds_path}[/green]")
        else:
            console.log(
                "[yellow]Datasource já existe, não sobrescrito[/yellow]"
            )


def update_features_compose(module_name: str, feature_name: str,
                            feature_type: str) -> None:
    """Atualiza a facade inserindo imports e método estático na classe FeaturesCompose.

    Estratégia:
    - Garante imports necessários (sem duplicar) após o docstring, se houver.
    - Insere o novo método ao final do corpo da classe FeaturesCompose, respeitando indentação.
    """
    project = get_project_name()
    snake = sanitize_name(feature_name)
    cc = camel_case(feature_name)
    fi = get_feature_initials(feature_name)

    compose_path = os.path.join(
        "src", project, "modules", module_name, "features", "features_compose.py"
    )
    if not os.path.exists(compose_path):
        raise FileNotFoundError(
            f"features_compose.py não encontrado em '{module_name}'."
        )

    content = read_text(compose_path)

    # Inserir imports necessários
    import_lines = build_facade_imports(module_name, snake, cc, fi, feature_type)
    to_insert: list[str] = []
    for line in import_lines:
        if line not in content:
            to_insert.append(line)

    if to_insert:
        # Detecta docstring inicial
        insert_idx = 0
        stripped = content.lstrip()
        if stripped.startswith('"""'):
            # encontra fechamento do docstring
            start = content.find('"""')
            end = content.find('"""', start + 3)
            if end != -1:
                insert_idx = end + 3
                if insert_idx < len(content) and content[insert_idx] == "\n":
                    insert_idx += 1
        new_content = (
            content[:insert_idx]
            + ("\n" if insert_idx != 0 and content[insert_idx - 1] != "\n" else "")
            + "\n".join(to_insert)
            + "\n\n"
            + content[insert_idx:]
        )
        content = new_content

    # Garante que a classe exista
    class_token = "class FeaturesCompose"
    if class_token not in content:
        raise ValueError("Classe FeaturesCompose não encontrada na facade.")

    # Não duplica o método
    if f"def {snake}(" in content:
        console.log(
            f"[yellow]Método '{snake}' já existe em features_compose.py[/yellow]"
        )
        return

    # Constrói o método com indentação de um nível (4 espaços)
    method_block = build_facade_method(snake, cc, fi, feature_type)

    # Inserir dentro da classe FeaturesCompose
    lines = content.splitlines()
    # Localiza a linha da classe
    class_idx = None
    for idx, line in enumerate(lines):
        if line.lstrip().startswith("class FeaturesCompose"):
            class_idx = idx
            break
    assert class_idx is not None

    # Indentação da classe
    class_line = lines[class_idx]
    class_indent = len(class_line) - len(class_line.lstrip(" "))

    # Procura o final do corpo da classe (última linha ainda indentada além da indentação da classe)
    last_body_line = class_idx
    for i in range(class_idx + 1, len(lines)):
        l = lines[i]
        # Ignora linhas em branco
        if not l.strip():
            last_body_line = i
            continue
        indent = len(l) - len(l.lstrip(" "))
        if indent > class_indent:
            last_body_line = i
            continue
        # Voltou ao nível da classe (ou menor): corpo terminou na linha anterior
        break

    # Insere o método após a última linha do corpo
    insertion_index = last_body_line + 1
    insert_lines = [""] + method_block.rstrip("\n").splitlines()
    new_lines = lines[:insertion_index] + insert_lines + lines[insertion_index:]
    new_content = "\n".join(new_lines) + ("\n" if content.endswith("\n") else "")

    with open(compose_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    console.log(
        f"Método adicionado à facade: [green]{module_name}.features.{snake}[/green]"
    )


# --------------------------- CLI ----------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Cria uma nova feature seguindo a Clean Architecture, "
            "atualiza utils e a facade automaticamente."
        )
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=["base", "call_data"],
        required=True,
        help="Tipo da feature a ser criada (base ou call_data).",
    )
    args = parser.parse_args()

    console.print(
        Panel(
            f"Assistente de Criação de Feature - Tipo: [bold yellow]{args.type}[/bold yellow]",
            title="[bold blue]Smart Core Assistant[/bold blue]",
            border_style="blue",
        )
    )

    module_name, feature_name = get_user_input()

    try:
        console.log(
            f"Atualizando utils para a feature '[green]{feature_name}[/green]' "
            f"no módulo '[green]{module_name}[/green]'..."
        )
        update_utils(module_name, feature_name, args.type)

        console.log("Criando arquivos da feature...")
        create_feature_files(module_name, feature_name, args.type)

        console.log("Atualizando facade (features_compose.py)...")
        update_features_compose(module_name, feature_name, args.type)

        console.print(
            Panel(
                "[bold green]Feature criada com sucesso![/bold green]\n"
                "- utils/erros.py, utils/parameters.py e utils/types.py atualizados\n"
                "- Usecase/Datasource gerados na pasta da feature\n"
                "- features_compose.py atualizado automaticamente",
                title="[bold yellow]Concluído[/bold yellow]",
                border_style="green",
            )
        )
    except Exception as e:  # noqa: BLE001
        console.print(f"[bold red]Erro:[/bold red] {e}")


if __name__ == "__main__":
    main()