import os
import django
import ast
import sys

# Setup Django environment
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings",
)
django.setup()

from django_q.models import Schedule


def clean_broken_schedules():
    print("Checking for broken schedules...")
    schedules = Schedule.objects.all()
    broken_count = 0

    for s in schedules:
        try:
            # Try to parse args just like django-q does
            ast.literal_eval(s.args)
            # Also check kwargs just in case
            ast.literal_eval(s.kwargs)
        except (ValueError, SyntaxError) as e:
            print(
                f"Found broken schedule: ID={s.id} Name='{s.name}' Args='{s.args}' Error={e}"
            )
            print(f"Deleting broken schedule {s.id}...")
            s.delete()
            broken_count += 1
        except Exception as e:
            print(f"Unexpected error checking schedule {s.id}: {e}")

    print(f"Finished. Deleted {broken_count} broken schedules.")


if __name__ == "__main__":
    clean_broken_schedules()
