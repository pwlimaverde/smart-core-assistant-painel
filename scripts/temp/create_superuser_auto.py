import os

import django
from django.contrib.auth import get_user_model

# Configura o ambiente Django
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.core.settings",
)
django.setup()

User = get_user_model()
username = "admin"
email = "admin@example.com"
password = "123456"

try:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username, email=email, password=password
        )
        print("SUPERUSER_CREATED")
    else:
        print("SUPERUSER_EXISTS")
except Exception as e:
    print(f"ERROR: {e}")
