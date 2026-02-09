import os

from cryptography.fernet import Fernet

key = Fernet.generate_key().decode()
print(f"Generated Key: {key}")

env_path = ".env"
lines = []
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

updates = {
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5436",
    "POSTGRES_DB": "smart_core_db",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "postgres123",
    "POSTGRES_SSLMODE": "disable",
    "REDIS_PORT": "6382",
}

# Check if ENCRYPTION_KEY exists
key_exists = False
for line in lines:
    if line.strip().startswith("ENCRYPTION_KEY="):
        key_exists = True
        break

if not key_exists:
    updates["ENCRYPTION_KEY"] = key

new_lines = []
processed_keys = set()
for line in lines:
    parts = line.split("=", 1)
    if len(parts) == 2:
        k = parts[0].strip()
        if k in updates:
            new_lines.append(f"{k}={updates[k]}\n")
            processed_keys.add(k)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

# Append remaining
if lines and not lines[-1].endswith("\n"):
    new_lines.append("\n")

for k, v in updates.items():
    if k not in processed_keys:
        new_lines.append(f"{k}={v}\n")

with open(env_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("ENV UPDATED SUCCESS")
