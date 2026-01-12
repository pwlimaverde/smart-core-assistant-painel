import os
import sys
import django

# Setup environment
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(PROJECT_ROOT, "src"))
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings",
)
django.setup()

from smart_core_assistant_painel.app.tenants.models import Plan


def create_plans():
    plans = [
        {
            "name": "Básico",
            "description": "Ideal para quem está começando.",
            "max_instances": 4,
            "max_departments": 2,
            "price": 197.00,
        },
        {
            "name": "Profissional",
            "description": "Para empresas em crescimento.",
            "max_instances": 8,
            "max_departments": 5,
            "price": 497.00,
        },
        {
            "name": "Ilimitado",
            "description": "Para grandes operações.",
            "max_instances": -1,
            "max_departments": -1,
            "price": None,  # Sob consulta
        },
    ]

    for p_data in plans:
        plan, created = Plan.objects.get_or_create(
            name=p_data["name"], defaults=p_data
        )
        if created:
            print(f"Created plan: {plan.name}")
        else:
            # Update values if needed
            for key, value in p_data.items():
                setattr(plan, key, value)
            plan.save()
            print(f"Updated plan: {plan.name}")


if __name__ == "__main__":
    create_plans()
