"""Inicializa as funcionalidades de carregamento inicial da aplicação.

Este módulo é responsável por acionar a sequência de carregamento inicial
da aplicação, chamando a composição de funcionalidades necessária.

Funções:
    start_initial_loading: A função principal para iniciar o carregamento
    inicial.
"""

import os

from .features.features_compose import FeaturesCompose


def start_initial_loading() -> None:
    """Inicia o processo de carregamento inicial da aplicação.

    Esta função chama a composição de funcionalidades para inicializar o Firebase,
    que é um passo crítico para a inicialização da aplicação.
    """
    # Bypass controlado: permite rodar scripts sem inicializar Firebase.
    # Defina DISABLE_APP_SERVICES_INIT="1" para pular esta etapa.
    if os.environ.get("DISABLE_APP_SERVICES_INIT") == "1":
        return

    FeaturesCompose.init_firebase()
