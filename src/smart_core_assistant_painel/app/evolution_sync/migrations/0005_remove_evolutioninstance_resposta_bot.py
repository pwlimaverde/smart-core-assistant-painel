"""Remove campo resposta_bot duplicado de EvolutionInstance.

A fonte da verdade para controle do bot é AppInstance.resposta_bot.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        (
            "evolution_sync",
            "0004_evolutioninstance_resposta_bot",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="evolutioninstance",
            name="resposta_bot",
        ),
    ]
