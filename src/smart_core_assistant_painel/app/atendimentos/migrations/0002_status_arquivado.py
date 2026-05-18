from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("atendimentos", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="atendimento",
            name="status",
            field=models.CharField(
                choices=[
                    ("fila", "Fila"),
                    ("em_atendimento", "Em Atendimento"),
                    ("pendencia", "Pendência"),
                    ("resolvido", "Resolvido"),
                    ("cancelado", "Cancelado"),
                    ("arquivado", "Arquivado"),
                ],
                default="fila",
                help_text="Status atual do atendimento (legado - será substituído por fluxo)",
                max_length=20,
            ),
        ),
    ]
