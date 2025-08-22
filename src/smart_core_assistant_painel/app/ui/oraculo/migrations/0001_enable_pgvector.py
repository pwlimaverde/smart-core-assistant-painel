from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):
    initial = False

    dependencies = []

    operations = [
        # Habilita a extensão pgvector no banco de dados
        VectorExtension(),
    ]