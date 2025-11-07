from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        (
            "operacional",
            "0004_alter_atendente_fluxo",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="atendente",
            name="fluxo",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="atendentes",
                to="operacional.fluxoatendimento",
                help_text=(
                    "Fluxo de atendimento (quadro) ao qual o atendente sera convidado"
                ),
            ),
        ),
    ]