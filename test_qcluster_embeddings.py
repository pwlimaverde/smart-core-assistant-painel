#!/usr/bin/env python3
"""Script para testar OllamaEmbeddings no contêiner qcluster."""

import os
from langchain_ollama import OllamaEmbeddings

def test_ollama_embeddings():
    """Testa a criação e uso de OllamaEmbeddings."""
    print("=== Teste de OllamaEmbeddings no QCluster ===")
    
    # Verificar variáveis de ambiente
    embeddings_model = os.environ.get("EMBEDDINGS_MODEL")
    embeddings_class = os.environ.get("EMBEDDINGS_CLASS")
    ollama_base_url = os.environ.get("OLLAMA_BASE_URL")
    
    print(f"EMBEDDINGS_MODEL: {embeddings_model}")
    print(f"EMBEDDINGS_CLASS: {embeddings_class}")
    print(f"OLLAMA_BASE_URL: {ollama_base_url}")
    
    if not all([embeddings_model, embeddings_class, ollama_base_url]):
        print("❌ Variáveis de ambiente não configuradas corretamente")
        return False
    
    try:
        # Criar instância de OllamaEmbeddings
        print("\n🔄 Criando instância de OllamaEmbeddings...")
        embeddings = OllamaEmbeddings(
            model=embeddings_model,
            base_url=ollama_base_url
        )
        print("✅ Instância criada com sucesso")
        
        # Testar geração de embeddings
        print("\n🔄 Testando geração de embeddings...")
        test_text = "Este é um teste de embeddings"
        result = embeddings.embed_query(test_text)
        
        print(f"✅ Embeddings gerados com sucesso")
        print(f"📊 Dimensões do vetor: {len(result)}")
        print(f"📊 Primeiros 5 valores: {result[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar OllamaEmbeddings: {e}")
        print(f"📋 Tipo do erro: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_ollama_embeddings()
    exit(0 if success else 1)