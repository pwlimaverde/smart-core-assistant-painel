import sys
import os

print(f"Python Executable: {sys.executable}")
print("Sys Path:")
for p in sys.path:
    print(f"  {p}")

try:
    import dateutil

    print(f"Dateutil found: {dateutil.__file__}")
except ImportError as e:
    print(f"Dateutil import failed: {e}")

try:
    import django

    print(f"Django found: {django.__file__}")
except ImportError as e:
    print(f"Django import failed: {e}")
