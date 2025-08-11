#!/usr/bin/env python3
"""
Script simples para testar conectividade Redis sem Django.
"""

import redis
import os

def test_redis_connection():
    """Testa a conectividade com o Redis."""
    try:
        # Configuração do Redis baseada nas variáveis de ambiente
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_db = int(os.getenv('REDIS_DB', '1'))
        
        print(f"Tentando conectar ao Redis em {redis_host}:{redis_port}/{redis_db}")
        
        # Conecta ao Redis
        r = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        
        # Testa a conexão
        r.ping()
        print("✅ Conexão com Redis estabelecida com sucesso!")
        
        # Testa operações básicas
        test_key = "test_qcluster_connection"
        test_value = "working"
        
        r.set(test_key, test_value, ex=60)  # Expira em 60 segundos
        retrieved_value = r.get(test_key)
        
        if retrieved_value == test_value:
            print(f"✅ Teste de escrita/leitura bem-sucedido: {test_key} = {retrieved_value}")
        else:
            print(f"❌ Erro no teste de escrita/leitura: esperado '{test_value}', obtido '{retrieved_value}'")
        
        # Verifica se há chaves relacionadas ao WhatsApp
        whatsapp_keys = r.keys("*whatsapp*")
        if whatsapp_keys:
            print(f"📱 Encontradas {len(whatsapp_keys)} chaves relacionadas ao WhatsApp:")
            for key in whatsapp_keys[:5]:  # Mostra apenas as primeiras 5
                print(f"  - {key}")
        else:
            print("📱 Nenhuma chave relacionada ao WhatsApp encontrada")
        
        # Verifica informações do Redis
        info = r.info()
        print(f"📊 Informações do Redis:")
        print(f"  - Versão: {info.get('redis_version', 'N/A')}")
        print(f"  - Clientes conectados: {info.get('connected_clients', 'N/A')}")
        print(f"  - Chaves no DB {redis_db}: {r.dbsize()}")
        
        return True
        
    except redis.ConnectionError as e:
        print(f"❌ Erro de conexão com Redis: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    print("=== Teste de Conectividade Redis para QCluster ===")
    success = test_redis_connection()
    exit(0 if success else 1)