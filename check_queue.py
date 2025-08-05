from django_q.models import Task

print(f'Tarefas na fila: {Task.objects.count()}')
print('Últimas 5 tarefas:')
for task in Task.objects.all()[:5]:
    print(f'ID: {task.id}, Nome: {task.name}, Status: {task.success}')

# Limpar tarefas antigas se necessário
if Task.objects.count() > 0:
    print('\nLimpando tarefas antigas...')
    Task.objects.all().delete()
    print('Tarefas limpas!')