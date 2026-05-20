"""[ATD-MIG-006] Suporte a reply / mensagem citada em Mensagem.

Novos campos:
- ``mensagem_citada``: FK self nullable — aponta para a mensagem original
  quando o stanzaId do contextInfo do WhatsApp é encontrado no banco.
- ``quoted_preview``: JSONField nullable — armazena preview serializado do
  bloco citado quando a mensagem original não está armazenada localmente.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "atendimentos",
            "0005_mensagem_status_envio_e_timestamps",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="mensagem",
            name="mensagem_citada",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="respostas",
                to="atendimentos.mensagem",
                help_text=(
                    "Mensagem original citada (reply). Preenchida via "
                    "contextInfo.stanzaId do webhook quando a mensagem "
                    "original está no banco local."
                ),
            ),
        ),
        migrations.AddField(
            model_name="mensagem",
            name="quoted_preview",
            field=models.JSONField(
                blank=True,
                null=True,
                help_text=(
                    "Preview serializado do bloco citado quando mensagem_citada "
                    "não pôde ser resolvida. "
                    "Formato: {remetente, conteudo_preview, tipo, stanza_id}."
                ),
            ),
        ),
    ]
