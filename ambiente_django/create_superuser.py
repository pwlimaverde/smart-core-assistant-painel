import os
import django

# Configura o Django settings
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings",
)

django.setup()
from django.contrib.auth import get_user_model

User = get_user_model()
# Cria ou atualiza o usuário admin de forma idempotente
user, created = User.objects.get_or_create(
    username="admin", defaults={"email": "admin@example.com"}
)
user.is_superuser = True
user.is_staff = True
user.set_password("123456")
user.save()
print("created" if created else "updated")