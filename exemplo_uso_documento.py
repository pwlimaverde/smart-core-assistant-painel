"""
Exemplo de Uso do Modelo Documento com Embedding Automático
==========================================================

Este arquivo demonstra como usar a busca semântica simplificada
do modelo Documento com embedding gerado automaticamente no save().
"""

from src.smart_core_assistant_painel.app.ui.oraculo.models_documento import Documento
from src.smart_core_assistant_painel.app.ui.oraculo.embedding_data import EmbeddingData


def processar_mensagem_webhook(mensagem_recebida: str) -> str:
    """
    Processa uma mensagem recebida pelo webhook e retorna contexto relevante.
    
    Args:
        mensagem_recebida: Texto da mensagem do usuário
        
    Returns:
        Contexto formatado com documentos relevantes
    """
    
    # FLUXO PRINCIPAL - APENAS UMA LINHA!
    contexto = Documento.buscar_documentos_similares(mensagem_recebida)
    
    return contexto


# ===================================================
# EXEMPLOS DE USO PRÁTICO
# ===================================================

def exemplo_uso():
    """Exemplos de como usar a busca em diferentes cenários."""
    
    # Exemplo 1: Pergunta sobre produto
    mensagem1 = "Como funciona o sistema de pagamento?"
    contexto1 = processar_mensagem_webhook(mensagem1)
    print("🔍 Pergunta:", mensagem1)
    print("📋 Contexto encontrado:")
    print(contexto1)
    print("\n" + "="*50 + "\n")
    
    # Exemplo 2: Dúvida sobre suporte
    mensagem2 = "Preciso falar com o suporte técnico"
    contexto2 = processar_mensagem_webhook(mensagem2)
    print("🔍 Pergunta:", mensagem2)
    print("📋 Contexto encontrado:")
    print(contexto2)
    print("\n" + "="*50 + "\n")
    
    # Exemplo 3: Busca customizada com mais resultados
    mensagem3 = "Quais são os horários de funcionamento?"
    contexto3 = Documento.buscar_documentos_similares(mensagem3, top_k=3)
    print("🔍 Pergunta:", mensagem3)
    print("📋 Contexto encontrado (top 3):")
    print(contexto3)


def exemplo_embedding_data():
    """Exemplos de uso direto da classe EmbeddingData."""
    
    print("🧠 Testando EmbeddingData diretamente...\n")
    
    # Exemplo 1: Gerar embedding de um texto
    texto1 = "Esta é uma mensagem de teste"
    try:
        embedding1 = EmbeddingData.gerar_embedding_texto(texto1)
        print(f"✅ Embedding gerado para: '{texto1}'")
        print(f"   Dimensões: {len(embedding1)}")
        print(f"   Primeiros valores: {embedding1[:5]}...")
    except Exception as e:
        print(f"❌ Erro ao gerar embedding: {e}")
    
    print("\n" + "-"*30 + "\n")
    
    # Exemplo 2: Gerar embedding para documento (agora automático!)
    conteudo_doc = "Informações sobre políticas de privacidade e termos de uso"
    print(f"ℹ️ Embedding é gerado automaticamente no Documento.objects.create()!")
    print(f"   Conteúdo: '{conteudo_doc[:50]}...'")
    print(f"   🎉 Zero código manual necessário!")


# ===================================================
# INTEGRAÇÃO COM WEBHOOK
# ===================================================

def webhook_handler(request_data: dict) -> dict:
    """
    Handler simplificado para webhook que demonstra a integração.
    
    Args:
        request_data: Dados da requisição do webhook
        
    Returns:
        Resposta processada
    """
    
    # Extrai mensagem do webhook
    mensagem = request_data.get('message', {}).get('text', '')
    
    if not mensagem:
        return {"erro": "Mensagem vazia"}
    
    # Busca contexto relevante - APENAS UMA LINHA!
    contexto = Documento.buscar_documentos_similares(mensagem)
    
    # Resposta estruturada
    return {
        "mensagem_original": mensagem,
        "contexto_encontrado": contexto,
        "tem_contexto": bool(contexto.strip())
    }


if __name__ == "__main__":
    print("🚀 Testando o modelo Documento com EmbeddingData...\n")
    
    # Testa busca de documentos
    exemplo_uso()
    
    print("\n" + "="*60 + "\n")
    
    # Testa EmbeddingData diretamente
    exemplo_embedding_data()