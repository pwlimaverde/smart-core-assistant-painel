from django.db import migrations


def map_status_forward(apps, schema_editor):
    Atendimento = apps.get_model('atendimentos', 'Atendimento')

    mapping = {
        'novo': 'fila',
        'bot_triagem': 'fila',
        'bot_atendimento': 'em_atendimento',
        'fila_humana': 'fila',
        'humano_atendimento': 'em_atendimento',
        'aguardando_cliente': 'aguardando_retorno',
        'resolvido': 'resolvido',
        'cancelado': 'cancelado',
    }

    for old, new in mapping.items():
        Atendimento.objects.filter(status=old).update(status=new)


def map_status_backward(apps, schema_editor):
    Atendimento = apps.get_model('atendimentos', 'Atendimento')

    mapping = {
        'fila': 'fila_humana',
        'em_atendimento': 'humano_atendimento',
        'aguardando_retorno': 'aguardando_cliente',
        'resolvido': 'resolvido',
        'cancelado': 'cancelado',
    }

    for new, old in mapping.items():
        Atendimento.objects.filter(status=new).update(status=old)


class Migration(migrations.Migration):
    dependencies = [
        ('atendimentos', '0003_status_refactor'),
    ]

    operations = [
        migrations.RunPython(map_status_forward, map_status_backward),
    ]