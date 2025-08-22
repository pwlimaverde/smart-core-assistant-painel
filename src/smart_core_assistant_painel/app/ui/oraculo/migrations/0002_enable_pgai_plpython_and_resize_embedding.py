from __future__ import annotations

from django.db import migrations
import pgvector.django


class Migration(migrations.Migration):
    dependencies = [
        ("oraculo", "0001_enable_pgvector"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS plpython3u;",
            reverse_sql="DROP EXTENSION IF EXISTS plpython3u;",
        ),
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS ai;",
            reverse_sql="DROP EXTENSION IF EXISTS ai;",
        ),
        migrations.AlterField(
            model_name="treinamentos",
            name="embedding",
            field=pgvector.django.VectorField(
                dimensions=1024,
                null=True,
                blank=True,
                help_text=(
                    "Vetor de embedding (dim=1024) para busca semântica via pgvector"
                ),
            ),
        ),
    ]