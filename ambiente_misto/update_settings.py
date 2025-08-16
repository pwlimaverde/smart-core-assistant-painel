import os

# Caminho para o arquivo settings.py
settings_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 
    "..", 
    "src", 
    "smart_core_assistant_painel", 
    "app", 
    "ui", 
    "core", 
    "settings.py"
))

# Lê o conteúdo do arquivo settings.py
with open(settings_path, "r") as f:
    settings_content = f.read()

# Altera a configuração do banco de dados
new_db_config = """
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'smart_core_db'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'postgres123'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5434'),
    }
}
"""

# Encontra a configuração do banco de dados existente e a substitui
start_index = settings_content.find("DATABASES = {")
end_index = settings_content.find("}", start_index) + 1
settings_content = settings_content[:start_index] + new_db_config + settings_content[end_index:]

# Altera a configuração do cache
new_cache_config = f"""
CACHES = {{
    "default": {{
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://127.0.0.1:{{os.getenv('REDIS_PORT', '6381')}}/1",
        "OPTIONS": {{
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }}
    }}
}}
"""

# Encontra a configuração de cache existente e a substitui
start_index = settings_content.find("CACHES = {")
end_index = settings_content.find("}", start_index) + 1
settings_content = settings_content[:start_index] + new_cache_config + settings_content[end_index:]

# Salva o arquivo settings.py modificado
with open(settings_path, "w") as f:
    f.write(settings_content)

print(f"Arquivo settings.py atualizado em: {settings_path}")