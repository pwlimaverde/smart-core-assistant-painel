from django.db import migrations


def map_status_forward(apps, schema_editor):
    Atendimento = apps.get_model('atendimentos', 'Atendimento')

    mapping_simple = {
        'aguardando_inicial': 'novo',
        'aguardando_contato': 'aguardando_cliente',
        'aguardando_atendente': 'fila_humana',
        'em_andamento': 'humano_atendimento',
        'resolvido': 'resolvido',
        'cancelado': 'cancelado',
    }

    # Atualiza mapeamento simples
    for old, new in mapping_simple.items():
        Atendimento.objects.filter(status=old).update(status=new)

    # Transferido: decidir com base em atribuição atual
    qs_transferido = Atendimento.objects.filter(status='transferido')
    for a in qs_transferido.iterator():
        if a.atendente_humano_id:
            a.status = 'humano_atendimento'
        else:
            a.status = 'fila_humana'
        a.save(update_fields=['status'])


def map_status_backward(apps, schema_editor):
    Atendimento = apps.get_model('atendimentos', 'Atendimento')

    mapping_simple = {
        'novo': 'aguardando_inicial',
        'aguardando_cliente': 'aguardando_contato',
        'fila_humana': 'aguardando_atendente',
        'humano_atendimento': 'em_andamento',
        'resolvido': 'resolvido',
        'cancelado': 'cancelado',
    }

    for new, old in mapping_simple.items():
        Atendimento.objects.filter(status=new).update(status=old)

    # Não há mapeamento reverso confiável para 'transferido'


class Migration(migrations.Migration):
    dependencies = [
        ('atendimentos', '0002_atendimento_data_ultima_mensagem_and_more'),
    ]

    operations = [
        migrations.RunPython(map_status_forward, map_status_backward),
    ]