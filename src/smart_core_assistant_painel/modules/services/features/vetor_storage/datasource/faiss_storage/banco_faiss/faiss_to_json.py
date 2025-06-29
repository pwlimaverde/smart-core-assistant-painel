import json
import os

import faiss


def faiss_para_json():
    """Converte dados FAISS para JSON - busca index.faiss no diretório atual"""

    # Buscar index.faiss no diretório atual
    caminho_indice = "index.faiss"
    arquivo_saida = "dados_faiss.json"

    # Verificar se o arquivo existe
    if not os.path.exists(caminho_indice):
        print("❌ Arquivo 'index.faiss' não encontrado no diretório atual!")
        return

    print(f"📂 Carregando: {caminho_indice}")

    # Carregar o índice
    index = faiss.read_index(caminho_indice)

    # Criar estrutura básica
    dados = {
        "total_vetores": index.ntotal,
        "dimensao": index.d,
        "vetores": []
    }

    # Extrair vetores (limitando a 100 para não ficar muito pesado)
    limite = min(100, index.ntotal)

    print(f"📊 Exportando {limite} vetores de {index.ntotal} disponíveis...")

    for i in range(limite):
        try:
            vetor = index.reconstruct(i)
            dados["vetores"].append({
                "id": i,
                "dados": vetor[:10].tolist()
            })
        except BaseException:
            continue

    # Salvar JSON no mesmo diretório
    with open(arquivo_saida, 'w') as arquivo:
        json.dump(dados, arquivo, indent=2)

    print(f"✅ Arquivo salvo: {arquivo_saida}")
    print(f"📈 Vetores exportados: {len(dados['vetores'])}")
    print(f"📏 Dimensão dos vetores: {dados['dimensao']}")


# Executar
if __name__ == "__main__":
    faiss_para_json()
