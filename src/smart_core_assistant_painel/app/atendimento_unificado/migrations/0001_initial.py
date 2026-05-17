"""Migration inicial do app Atendimento Unificado.

Cria apenas tabelas próprias (`atu_*`). Não altera nenhuma tabela legada.
Reverter equivale a `DROP TABLE atu_leitura_atendimento`, sem perda de
dados de produção.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies: list[tuple[str, str]] = []

    operations = [
        migrations.CreateModel(
            name="LeituraAtendimento",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "atendimento_id",
                    models.BigIntegerField(
                        help_text=(
                            "ID lógico de atendimentos.Atendimento "
                            "(sem FK cruzada)."
                        )
                    ),
                ),
                (
                    "atendente_id",
                    models.BigIntegerField(
                        help_text=(
                            "ID lógico de operacional.Atendente "
                            "(sem FK cruzada)."
                        )
                    ),
                ),
                (
                    "ultima_leitura_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text=(
                            "Momento da última leitura do atendimento "
                            "pelo atendente."
                        ),
                    ),
                ),
            ],
            options={
                "verbose_name": "Leitura de Atendimento",
                "verbose_name_plural": "Leituras de Atendimentos",
                "db_table": "atu_leitura_atendimento",
                "unique_together": {("atendimento_id", "atendente_id")},
            },
        ),
        migrations.AddIndex(
            model_name="leituraatendimento",
            index=models.Index(
                fields=["atendimento_id", "ultima_leitura_at"],
                name="atu_leit_atend_ultima_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="leituraatendimento",
            index=models.Index(
                fields=["atendente_id", "ultima_leitura_at"],
                name="atu_leit_atend_at_idx",
            ),
        ),
    ]
