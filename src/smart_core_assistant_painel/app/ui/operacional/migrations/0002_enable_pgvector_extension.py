# Generated migration for pgvector extension
from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):
    """Habilita a extensão pgvector no PostgreSQL."""

    dependencies = [
        ("operacional", "0001_initial"),
    ]

    operations = [
        VectorExtension(),
    ]
