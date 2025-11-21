from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("operacional", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="atendente",
            name="fluxo",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="atendentes",
                to="operacional.fluxoatendimento",
                help_text=(
                    "Fluxo de atendimento (quadro) ao qual o atendente sera convidado"
                ),
                null=True,
                blank=True,
            ),
        ),
        migrations.AddIndex(
            model_name="atendente",
            index=models.Index(
                fields=["fluxo"],
                name="oraculo_ate_fluxo_76c2fe_idx",
            ),
        ),
    ]
