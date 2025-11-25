"""Habilita a extensão pgvector no PostgreSQL para o app Treinamento.

Esta migração deve ser executada antes de qualquer criação de tabela
com campos `VectorField`, garantindo que o tipo `vector` exista.
"""

from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):
    # Primeira migração do app Treinamento
    initial = True

    dependencies: list[tuple[str, str]] = []

    operations = [VectorExtension()]
