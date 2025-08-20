"""
Este módulo centraliza e expõe as funcionalidades de carregamento inicial
da aplicação, como a inicialização de serviços externos (Firebase).
"""
from .features.features_compose import FeaturesCompose
from .start_initial_loading import start_initial_loading
from .utils.erros import FirebaseInitError
from .utils.parameters import FirebaseInitParameters
from .utils.types import FIUsecase

__all__ = [
    # Facade
    "FeaturesCompose",
    # Start
    "start_initial_loading",
    # Erros
    "FirebaseInitError",
    # Parameters
    "FirebaseInitParameters",
    # Types
    "FIUsecase",
]
