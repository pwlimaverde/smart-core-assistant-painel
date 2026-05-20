"""[EVO-MIG-006] Adiciona campos de suporte ao Evolution Go em EvolutionInstance.

Novos campos:
- ``api_version``: feature flag que seleciona o adapter (v2/go).
- ``media_storage_backend``: indica se o servidor Evolution Go tem S3/MinIO.
- ``subscribed_events``: lista de eventos assinados no /instance/connect.
- ``last_connection_state``: último estado de conexão via webhook CONNECTION.

O default de ``api_version`` é ``"go"`` para novas instâncias.
Instâncias existentes são migradas para ``"v2"`` (retrocompat seguro)
via RunPython abaixo.
"""

from django.db import migrations, models


def set_existing_instances_to_v2(apps, schema_editor):
    """Define api_version='v2' em instâncias já existentes antes da migration.

    Garante que o cutover para Go seja explícito e opt-in,
    não automático para instâncias em produção.
    """
    EvolutionInstance = apps.get_model("evolution_sync", "EvolutionInstance")
    # IMPORTANTE: usar o alias da conexão da própria migration. Em ambiente
    # multi-tenant, ``.objects.update()`` sem ``.using()`` é roteado por uma
    # conexão separada onde a coluna recém-criada (ainda não commitada nesta
    # transação) não é visível → "column api_version does not exist" e rollback
    # de toda a migration. Fixar o alias garante mesma conexão/transação.
    alias = schema_editor.connection.alias
    EvolutionInstance.objects.using(alias).update(api_version="v2")


class Migration(migrations.Migration):
    dependencies = [
        (
            "evolution_sync",
            "0005_remove_evolutioninstance_resposta_bot",
        ),
    ]

    operations = [
        # 1. api_version
        migrations.AddField(
            model_name="evolutioninstance",
            name="api_version",
            field=models.CharField(
                choices=[
                    ("v2", "Evolution API v2 (Baileys)"),
                    ("go", "Evolution Go"),
                ],
                default="go",
                help_text=(
                    "Feature flag: seleciona o adapter REST correto. "
                    "Altere para 'v2' para rollback imediato sem deploy."
                ),
                max_length=5,
            ),
        ),
        # 2. media_storage_backend
        migrations.AddField(
            model_name="evolutioninstance",
            name="media_storage_backend",
            field=models.CharField(
                choices=[
                    ("none", "Sem storage (download on-demand)"),
                    ("s3", "S3 / MinIO no servidor Evolution"),
                ],
                default="s3",
                help_text=(
                    "Backend de mídia do servidor Evolution Go. "
                    "Se 's3', o webhook já traz mediaUrl — sem chamadas extras. "
                    "Se 'none', o painel chama POST /message/downloadmedia."
                ),
                max_length=10,
            ),
        ),
        # 3. subscribed_events
        migrations.AddField(
            model_name="evolutioninstance",
            name="subscribed_events",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=(
                    "Eventos assinados no POST /instance/connect (Evolution Go). "
                    "Ex: ['MESSAGE', 'MESSAGE_UPDATE', 'PRESENCE', 'CONNECTION', 'CONTACTS', 'QRCODE']"
                ),
            ),
        ),
        # 4. last_connection_state
        migrations.AddField(
            model_name="evolutioninstance",
            name="last_connection_state",
            field=models.CharField(
                blank=True,
                help_text=(
                    "Último estado de conexão recebido via evento CONNECTION do webhook. "
                    "Substitui o polling de /instance/connectionState em instâncias Go."
                ),
                max_length=50,
                null=True,
            ),
        ),
        # 5. Migrar instâncias existentes para api_version='v2' (segurança)
        migrations.RunPython(
            set_existing_instances_to_v2,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
