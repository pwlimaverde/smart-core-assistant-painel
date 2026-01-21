import os
import sys
import django

# Setup path
sys.path.append(r"c:\PROJETOS\PYTHON\APPS\smart-core-assistant-painel\src")
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings",
)

try:
    django.setup()
except Exception as e:
    print(f"Setup Error: {e}")
    sys.exit(1)

from django.test import Client
from django.contrib.auth.models import User
from smart_core_assistant_painel.app.ui.operacional.models import (
    Atendente,
    Departamento,
    FluxoAtendimento,
)


def run_test():
    print("Starting Login Redirect Verification...")

    # 1. Cleanup
    try:
        User.objects.filter(
            username__in=["test_plain", "test_atendente"]
        ).delete()
        Departamento.objects.filter(nome="Test Dept").delete()
    except Exception as e:
        print(f"Cleanup warning: {e}")

    client = Client()

    # 2. Test Plain User
    print("\n--- Test Case 1: Plain User ---")
    try:
        user_plain = User.objects.create_user(
            username="test_plain", password="password123"
        )
        response = client.post(
            "/usuarios/login/",
            {"username": "test_plain", "senha": "password123"},
        )

        print(f"Status Code: {response.status_code}")
        if response.status_code == 302:
            print(f"Redirect URL: {response.url}")
        else:
            print("FAIL: Did not redirect.")
    except Exception as e:
        print(f"Error in Case 1: {e}")

    # 3. Test Atendente User
    print("\n--- Test Case 2: Atendente User ---")
    try:
        dept = Departamento.objects.create(nome="Test Dept")
        # Ensure flux exists (model has helper ensure_fluxo but let's create manually to be safe)
        fluxo = FluxoAtendimento.objects.create(
            departamento=dept, nome="Fluxo Test"
        )

        user_atendente = User.objects.create_user(
            username="test_atendente", password="password123"
        )

        atendente = Atendente.objects.create(
            nome="Test Atendente",
            usuario_sistema="test_atendente",
            departamento=dept,
            email="test@example.com",
            fluxo=fluxo,  # Required field
        )
        print("Atendente created successfully.")

        response = client.post(
            "/usuarios/login/",
            {"username": "test_atendente", "senha": "password123"},
        )

        print(f"Status Code: {response.status_code}")
        if response.status_code == 302:
            print(f"Redirect URL: {response.url}")
        else:
            print(f"FAIL: Status {response.status_code}")

    except Exception as e:
        print(f"Error in Case 2: {e}")


if __name__ == "__main__":
    run_test()
