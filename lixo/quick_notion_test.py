import os
from notion_client import Client
from notion_client.errors import APIResponseError
from decouple import config

token = config("NOTION_TOKEN", default=None)
print('Token presente:', bool(token))
client = Client(auth=token)

for name, dbid in [
    ('Contatos', '1ac5bb99-62b3-4338-8059-5a3ed786eaf4'),
    ('Clientes', 'fda35cef-7d48-43b2-b6ad-d27681fc9502'),
]:
    print('\n===', name, '===')
    try:
        db = client.databases.retrieve(database_id=dbid)
        props = db.get('properties', {})
        print('Propriedades:', len(props))
        print('Chaves:', list(props.keys())[:10])
    except APIResponseError as e:
        print('API error:', e.code, str(e))
    except Exception as e:
        print('Erro:', str(e))