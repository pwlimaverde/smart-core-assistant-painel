"""[ATD-MIG-005] Adiciona campos de read receipts em Mensagem.

Novos campos:
- ``status_envio``: estado de entrega (pending/sent/delivered/read/failed).
- ``data_entregue``: timestamp de entrega confirmada pelo WhatsApp.
- ``data_lida``: timestamp de leitura confirmada pelo WhatsApp.

Atualizado via evento MESSAGE_UPDATE do webhook Evolution Go.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "atendimentos",
            "0004_mensagem_analise_midia_mensagem_arquivo_midia",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="mensagem",
            name="status_envio",
            field=models.CharField(
                choices=[
                    ("pending", "Pendente"),
                    ("sent", "Enviada (✓)"),
                    ("delivered", "Entregue (✓✓)"),
                    ("read", "Lida (✓✓ azul)"),
                    ("failed", "Falhou"),
                ],
                default="pending",
                db_index=True,
                help_text=(
                    "Status de entrega/leitura da mensagem enviada pelo bot/atendente. "
                    "Atualizado via evento MESSAGE_UPDATE do webhook Evolution. "
                    "Não se aplica a mensagens inbound (do contato)."
                ),
                max_length=15,
            ),
        ),
        migrations.AddField(
            model_name="mensagem",
            name="data_entregue",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="Data/hora em que o WhatsApp confirmou entrega ao dispositivo do contato.",
            ),
        ),
        migrations.AddField(
            model_name="mensagem",
            name="data_lida",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="Data/hora em que o contato visualizou a mensagem no WhatsApp.",
            ),
        ),
    ]
