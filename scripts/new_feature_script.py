import os
import argparse
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text

console = Console()


def get_user_input():
    """Solicita o nome do módulo e da feature ao usuário."""
    module_name = Prompt.ask("[bold cyan]Digite o nome do módulo[/bold cyan] (ex: ai_engine)")
    feature_name = Prompt.ask("[bold cyan]Digite o nome da feature[/bold cyan] (ex: chat_completions)")
    return module_name, feature_name


def create_feature_structure(module_name: str, feature_name: str, feature_type: str):
    """Cria a estrutura de diretórios e arquivos para a nova feature."""
    console.log(f"Iniciando criação da feature '{feature_name}' no módulo '{module_name}'...")
    base_path = os.path.join("src", "smart_core_assistant_painel", "modules", module_name, "features", feature_name)
    
    try:
        os.makedirs(base_path, exist_ok=True)
        console.log(f"Diretório base criado em: [green]{base_path}[/green]")

        capitalized_feature = "".join(word.capitalize() for word in feature_name.split('_'))

        files_to_create = {
            "erros.py": f'"""Módulo de erros da feature {feature_name}."""\n\nfrom src.smart_core_assistant_painel.modules.utils.errors import FeatureError\n\nclass {capitalized_feature}Error(FeatureError):\n    """Classe base para erros da feature {feature_name}."""\n    pass\n',
            "parameters.py": f'"""Módulo de parâmetros da feature {feature_name}."""\n\nfrom src.smart_core_assistant_painel.modules.utils.parameters import BaseParameters\n\nclass {capitalized_feature}Parameters(BaseParameters):\n    """Parâmetros para a feature {feature_name}."""\n    pass\n',
            "types.py": f'"""Módulo de tipos da feature {feature_name}."""\n\nfrom typing import TypeAlias\n\n# Exemplo de TypeAlias\n{capitalized_feature}Type: TypeAlias = str\n',
            "usecase.py": f'"""Módulo de caso de uso da feature {feature_name}."""\n\nfrom src.smart_core_assistant_painel.modules.utils.usecase import BaseUseCase\nfrom .erros import {capitalized_feature}Error\nfrom .parameters import {capitalized_feature}Parameters\nfrom .types import {capitalized_feature}Type\n\nclass {capitalized_feature}UseCase(BaseUseCase):\n    """Caso de uso para a feature {feature_name}."""\n\n    def execute(self, params: {capitalized_feature}Parameters) -> {capitalized_feature}Type:\n        # Adicione a lógica do caso de uso aqui\n        print(f"Executando o caso de uso para {feature_name} com os parâmetros: {{params}}")\n        return "Resultado do caso de uso"\n'
        }

        if feature_type == 'call_data':
            files_to_create['datasource.py'] = f'"""Módulo de fonte de dados da feature {feature_name}."""\n\nfrom src.smart_core_assistant_painel.modules.utils.datasource import BaseDatasource\nfrom .types import {capitalized_feature}Type\n\nclass {capitalized_feature}Datasource(BaseDatasource):\n    """Fonte de dados para a feature {feature_name}."""\n\n    def get_data(self, filters: dict) -> {capitalized_feature}Type:\n        # Adicione a lógica para buscar dados aqui\n        print(f"Buscando dados para {feature_name} com os filtros: {{filters}}")\n        return "Dados da fonte de dados"\n'

        for file_name, content in files_to_create.items():
            file_path = os.path.join(base_path, file_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            console.log(f"Arquivo criado: [green]{file_path}[/green]")

        # Criar/Atualizar __init__.py
        init_path = os.path.join(base_path, "__init__.py")
        init_content = [f'"""Módulo da feature {feature_name}."""\n']
        init_content.append(f'from .usecase import {capitalized_feature}UseCase')
        __all__ = [f'"{capitalized_feature}UseCase"']

        if feature_type == 'call_data':
            init_content.append(f'from .datasource import {capitalized_feature}Datasource')
            __all__.append(f'"{capitalized_feature}Datasource"')
        
        init_content.append(f'\\n__all__ = [{", ".join(__all__)}]\\n')

        with open(init_path, 'w', encoding='utf-8') as f:
            f.write("\\n".join(init_content))
        console.log(f"Arquivo __init__.py criado/atualizado em: [green]{base_path}[/green]")

        console.log(f"\\n[bold green]Estrutura da feature '{feature_name}' criada com sucesso![/bold green]")

    except OSError as e:
        console.print(f"[bold red]Erro ao criar a estrutura de diretórios/arquivos:[/bold red] {e}")


def show_instructions(module_name: str, feature_name: str):
    """Exibe as instruções para a ação manual necessária."""
    capitalized_feature = "".join(word.capitalize() for word in feature_name.split('_'))
    method_name = f"with_{feature_name}"
    usecase_class = f"{capitalized_feature}UseCase"

    instructions_text = Text.from_markup(f'''
    Adicione o seguinte método estático ao arquivo [bold cyan]features_compose.py[/bold cyan] do módulo [bold cyan]{module_name}[/bold cyan]:

    [green]@staticmethod[/green]
    [green]def {method_name}() -> {usecase_class}:[/green]
    [green]    """Retorna uma instância do caso de uso {feature_name}."""[/green]
    [green]    from src.smart_core_assistant_painel.modules.{module_name}.features.{feature_name}.usecase import {usecase_class}[/green]
    [green]    return {usecase_class}()[/green]
    ''')

    console.print(Panel(instructions_text, title="[bold yellow]Ação Manual Necessária![/bold yellow]", border_style="yellow"))


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(description="Cria a estrutura de uma nova feature para o Smart Core Assistant.")
    parser.add_argument('--type', type=str, choices=['base', 'call_data'], required=True, help='O tipo da feature a ser criada (base ou call_data).')
    args = parser.parse_args()

    console.print(Panel(f"Assistente de Criação de Feature - Tipo: [bold yellow]{args.type}[/bold yellow]", title="[bold blue]Smart Core Assistant[/bold blue]", border_style="blue"))

    module_name, feature_name = get_user_input()
    create_feature_structure(module_name, feature_name, args.type)
    show_instructions(module_name, feature_name)


if __name__ == "__main__":
    main()