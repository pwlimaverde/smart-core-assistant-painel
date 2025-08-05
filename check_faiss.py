from smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage import FaissVetorStorage
import os
from pathlib import Path

# Caminho correto baseado no código
faiss_dir = '/app/src/smart_core_assistant_painel/modules/services/features/vetor_storage/datasource/faiss_storage/banco_faiss'
faiss_index_path = os.path.join(faiss_dir, 'index.faiss')
faiss_pkl_path = os.path.join(faiss_dir, 'index.pkl')

print(f'Diretório FAISS: {faiss_dir}')
print(f'Arquivo index.faiss existe: {os.path.exists(faiss_index_path)}')
print(f'Arquivo index.pkl existe: {os.path.exists(faiss_pkl_path)}')

if os.path.exists(faiss_index_path):
    print(f'Tamanho do index.faiss: {os.path.getsize(faiss_index_path)} bytes')

if os.path.exists(faiss_pkl_path):
    print(f'Tamanho do index.pkl: {os.path.getsize(faiss_pkl_path)} bytes')

# Tentar inicializar o FaissVetorStorage
try:
    faiss_storage = FaissVetorStorage()
    print('FaissVetorStorage inicializado com sucesso!')
    
    # Verificar se há dados no índice
    if hasattr(faiss_storage, '_FaissVetorStorage__vectordb') and faiss_storage._FaissVetorStorage__vectordb is not None:
        vectordb = faiss_storage._FaissVetorStorage__vectordb
        if hasattr(vectordb, 'index') and vectordb.index is not None:
            print(f'Número de vetores no índice: {vectordb.index.ntotal}')
            print(f'Dimensão dos vetores: {vectordb.index.d}')
        else:
            print('Índice FAISS não está disponível no vectordb')
            
        # Tentar fazer uma busca de teste
        try:
            results = vectordb.similarity_search('teste', k=1)
            print(f'Busca de teste retornou {len(results)} resultados')
            if results:
                print(f'Primeiro resultado: {results[0].page_content[:100]}...')
        except Exception as e:
            print(f'Erro na busca de teste: {e}')
    else:
        print('VectorDB não está disponível')
        
except Exception as e:
    print(f'Erro ao inicializar FaissVetorStorage: {e}')