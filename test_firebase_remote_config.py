#!/usr/bin/env python3
"""
Script para testar e configurar o Firebase Remote Config
"""

import asyncio
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, remote_config


def init_firebase():
    """Inicializa o Firebase Admin SDK"""
    try:
        # Carrega variáveis de ambiente
        load_dotenv()
        
        # Verifica se já foi inicializado
        try:
            app = firebase_admin.get_app()
            print("✅ Firebase já inicializado")
            return app
        except ValueError:
            # Inicializa o Firebase
            cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if not cred_path:
                raise ValueError("GOOGLE_APPLICATION_CREDENTIALS não definido")
            
            if not os.path.exists(cred_path):
                raise ValueError(f"Arquivo de credenciais não encontrado: {cred_path}")
            
            cred = credentials.Certificate(cred_path)
            app = firebase_admin.initialize_app(cred)
            print("✅ Firebase inicializado com sucesso")
            return app
    except Exception as e:
        print(f"❌ Erro ao inicializar Firebase: {e}")
        raise


async def test_remote_config():
    """Testa o Firebase Remote Config"""
    try:
        print("🔧 Testando Firebase Remote Config...")
        
        # Inicializa o template do Remote Config
        template = remote_config.init_server_template()
        print("✅ Template do Remote Config criado")
        
        # Carrega o template do backend
        await template.load()
        print("✅ Template carregado do backend")
        
        # Avalia o template para obter os parâmetros atuais
        config = template.evaluate()
        print("✅ Template avaliado")
        
        # Lista de chaves que precisamos
        required_keys = [
            "secret_key_django",
            "groq_api_key", 
            "openai_api_key",
            "whatsapp_api_base_url",
            "whatsapp_api_send_text_url",
            "whatsapp_api_start_typing_url",
            "whatsapp_api_stop_typing_url",
            "llm_class",
            "model",
            "temperature",
            "prompt_system_analise_conteudo",
            "prompt_human_analise_conteudo",
            "prompt_system_melhoria_conteudo",
            "chunk_overlap",
            "chunk_size",
            "faiss_model",
            "prompt_human_analise_previa_mensagem",
            "prompt_system_analise_previa_mensagem",
            "valid_entity_types",
            "valid_intent_types"
        ]
        
        print("\n📋 Verificando chaves do Remote Config:")
        missing_keys = []
        
        for key in required_keys:
            try:
                value = config.get_string(key)
                if value:
                    print(f"✅ {key}: {value[:20]}..." if len(value) > 20 else f"✅ {key}: {value}")
                else:
                    print(f"⚠️  {key}: (vazio)")
                    missing_keys.append(key)
            except Exception as e:
                print(f"❌ {key}: Não encontrado - {e}")
                missing_keys.append(key)
        
        if missing_keys:
            print(f"\n❌ Chaves faltando no Remote Config: {missing_keys}")
            print("\n💡 Você precisa configurar essas chaves no Firebase Console:")
            print("   https://console.firebase.google.com/project/smart-core-assistant-painel/config")
        else:
            print("\n✅ Todas as chaves estão configuradas no Remote Config!")
            
        return len(missing_keys) == 0
        
    except Exception as e:
        print(f"❌ Erro ao testar Remote Config: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal"""
    try:
        print("🚀 Iniciando teste do Firebase Remote Config...\n")
        
        # Inicializa o Firebase
        init_firebase()
        
        # Testa o Remote Config
        success = asyncio.run(test_remote_config())
        
        if success:
            print("\n🎉 Teste concluído com sucesso!")
        else:
            print("\n❌ Teste falhou. Verifique as configurações.")
            
    except Exception as e:
        print(f"\n💥 Erro fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()