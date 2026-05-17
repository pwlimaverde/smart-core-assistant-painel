"""Migration E.3.4: GIN index em ValorCampoAtendimento.valor (JSONField).

Melhora consultas do tipo campo_<slug>=<valor> no filtro de conversas.
Usa jsonb_path_ops para cobrir consultas de containment (@> e path expressions).
ZERO alteração em tabelas legadas.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento_unificado", "0002_campos_personalizados"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS atu_valor_campo_valor_gin_idx "
                "ON atu_valor_campo USING gin (valor jsonb_path_ops);"
            ),
            reverse_sql=(
                "DROP INDEX IF EXISTS atu_valor_campo_valor_gin_idx;"
            ),
        ),
    ]
