#!/usr/bin/env python3
"""Script para testar o cenário real do FaissVetorStorage."""

import os
import sys
sys.path.append('/app/src')

def test_faiss_real_scenario():
    """Testa o cenário real do FaissVetorStorage."""
    print("=== Teste do Cenário Real FaissVetorStorage ===")
    
    try:
        # Importar as classes necessárias
        from smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage import FaissVetorStorage
        from smart_core_assistant_painel.modules.services.features.service_hub import SERVICEHUB
        
        print("✅ Importações realizadas com sucesso")
        
        # Verificar configurações do SERVICEHUB
        print(f"\n📋 SERVICEHUB.EMBEDDINGS_MODEL: {SERVICEHUB.EMBEDDINGS_MODEL}")
        print(f"📋 SERVICEHUB.EMBEDDINGS_CLASS: {SERVICEHUB.EMBEDDINGS_CLASS}")
        print(f"📋 OLLAMA_BASE_URL: {os.environ.get('OLLAMA_BASE_URL')}")
        
        # Criar instância do FaissVetorStorage
        print("\n🔄 Criando instância de FaissVetorStorage...")
        storage = FaissVetorStorage()
        print("✅ FaissVetorStorage criado com sucesso")
        
        # Testar criação de embeddings diretamente
        print("\n🔄 Testando criação de embeddings...")
        embeddings = storage._FaissVetorStorage__create_embeddings()
        print("✅ Embeddings criados com sucesso")
        print(f"📊 Tipo: {type(embeddings)}")
        
        # Testar geração de embedding
        print("\n🔄 Testando geração de embedding...")
        test_text = "Este é um teste de embedding"
        result = embeddings.embed_query(test_text)
        print(f"✅ Embedding gerado com sucesso")
        print(f"📊 Dimensões: {len(result)}")
        
        # Testar adição de documentos usando o método correto da interface
        print("\n🔄 Testando adição de documentos...")
        from langchain.schema import Document
        
        docs = [
            Document(page_content="Documento de teste 1", metadata={"source": "test1"}),
            Document(page_content="Documento de teste 2", metadata={"source": "test2"})
        ]
        
        storage.write(docs)
        print("✅ Documentos adicionados com sucesso")
        
        # Testar busca de documentos
        print("\n🔄 Testando busca de documentos...")
        results = storage.read("documento teste", k=2)
        print(f"✅ Busca realizada com sucesso")
        print(f"📊 Documentos encontrados: {len(results)}")
        for i, doc in enumerate(results):
            print(f"📄 Doc {i+1}: {doc.page_content[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        print(f"📋 Tipo do erro: {type(e).__name__}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_faiss_real_scenario()
    exit(0 if success else 1)