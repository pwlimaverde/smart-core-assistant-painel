"""Define apelidos de tipo para o módulo de carregamento inicial.

Este módulo centraliza as definições de tipo usadas nas funcionalidades de
carregamento inicial, melhorando a legibilidade e a manutenção do código.
Ele define um apelido de tipo para o caso de uso de inicialização do Firebase.
"""
from typing import TypeAlias

from py_return_success_or_error import Empty, UsecaseBase

from .parameters import FirebaseInitParameters

FIUsecase: TypeAlias = UsecaseBase[Empty, FirebaseInitParameters]
