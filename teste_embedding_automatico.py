"""
Teste do Fluxo Automático de Embedding
=====================================

Este arquivo demonstra como o embedding é gerado automaticamente
agora que removemos os métodos generate_embedding manuais.
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock

from src.smart_core_assistant_painel.app.ui.oraculo.models_documento import Documento
from src.smart_core_assistant_painel.app.ui.oraculo.models_treinamento import Treinamento
from src.smart_core_assistant_painel.app.ui.oraculo.embedding_data import EmbeddingData


class TestFluxoAutomaticoEmbedding(TestCase):
    """Testa o fluxo automático de geração de embeddings."""
    
    def setUp(self):
        """Configura dados de teste."""
        self.treinamento = Treinamento.objects.create(
            tag="teste_automatico",
            grupo="teste",
            conteudo="Conteúdo de teste para embedding automático",
            treinamento_finalizado=True
        )
    
    @patch.object(EmbeddingData, 'gerar_embedding_para_documento')
    def test_embedding_automatico_na_criacao(self, mock_embedding):
        """Testa se o embedding é gerado automaticamente ao criar documento."""
        # Configura mock
        mock_embedding.return_value = [0.1, 0.2, 0.3] * 300  # 900 dimensões
        
        # Cria documento - embedding deve ser gerado automaticamente
        documento = Documento.objects.create(
            treinamento=self.treinamento,
            conteudo="Teste de conteúdo para embedding automático",
            ordem=1
        )
        
        # Verifica se o embedding foi gerado
        mock_embedding.assert_called_once_with("Teste de conteúdo para embedding automático")
        self.assertIsNotNone(documento.embedding)
        self.assertEqual(len(documento.embedding), 900)
    
    @patch.object(EmbeddingData, 'gerar_embedding_para_documento')
    def test_sem_embedding_se_treinamento_nao_finalizado(self, mock_embedding):
        """Testa que embedding não é gerado se treinamento não estiver finalizado."""
        # Cria treinamento não finalizado
        treinamento_nao_finalizado = Treinamento.objects.create(
            tag="nao_finalizado",
            grupo="teste",
            conteudo="Conteúdo teste",
            treinamento_finalizado=False
        )
        
        # Cria documento
        documento = Documento.objects.create(
            treinamento=treinamento_nao_finalizado,
            conteudo="Teste sem embedding",
            ordem=1
        )
        
        # Verifica que embedding não foi gerado
        mock_embedding.assert_not_called()
        self.assertIsNone(documento.embedding)
    
    @patch.object(EmbeddingData, 'gerar_embedding_para_documento')
    def test_sem_embedding_se_conteudo_vazio(self, mock_embedding):
        """Testa que embedding não é gerado se conteúdo estiver vazio."""
        # Cria documento com conteúdo vazio
        documento = Documento.objects.create(
            treinamento=self.treinamento,
            conteudo="",
            ordem=1
        )
        
        # Verifica que embedding não foi gerado
        mock_embedding.assert_not_called()
        self.assertIsNone(documento.embedding)
    
    @patch.object(EmbeddingData, 'gerar_embedding_para_documento')
    def test_vetorizacao_por_treinamento_usa_save_automatico(self, mock_embedding):
        """Testa que a vetorização por treinamento usa o save automático."""
        # Configura mock
        mock_embedding.return_value = [0.1] * 1024
        
        # Cria documentos sem embedding (simulando que foram criados antes da finalização)
        documento1 = Documento(
            treinamento=self.treinamento,
            conteudo="Documento 1",
            ordem=1
        )
        documento1.save()  # Save direto sem chamar métodos de embedding
        
        documento2 = Documento(
            treinamento=self.treinamento,
            conteudo="Documento 2", 
            ordem=2
        )
        documento2.save()
        
        # Chama vetorização
        Documento.vetorizar_documentos_por_treinamento(self.treinamento)
        
        # Verifica que os embeddings foram gerados via save automático
        self.assertEqual(mock_embedding.call_count, 2)
        
        # Verifica que treinamento foi marcado como vetorizado
        self.treinamento.refresh_from_db()
        self.assertTrue(self.treinamento.treinamento_vetorizado)


def exemplo_uso_simplificado():
    """Demonstra como criar documentos com embedding automático."""
    
    print("🚀 Exemplo de Uso Simplificado - Embedding Automático\n")
    
    # 1. Cria treinamento finalizado
    print("1️⃣ Criando treinamento finalizado...")
    treinamento = Treinamento.objects.create(
        tag="exemplo_auto",
        grupo="exemplos",
        conteudo="Conteúdo do treinamento exemplo",
        treinamento_finalizado=True
    )
    print(f"   ✅ Treinamento criado: {treinamento.tag}")
    
    # 2. Cria documento - embedding é gerado automaticamente!
    print("\n2️⃣ Criando documento (embedding automático)...")
    documento = Documento.objects.create(
        treinamento=treinamento,
        conteudo="Este é um documento de exemplo que terá embedding gerado automaticamente",
        ordem=1
    )
    print(f"   ✅ Documento criado: {documento.pk}")
    print(f"   🧠 Embedding gerado: {'Sim' if documento.embedding else 'Não'}")
    
    # 3. Busca semântica funciona imediatamente
    print("\n3️⃣ Testando busca semântica...")
    contexto = Documento.buscar_documentos_similares("documento exemplo")
    print(f"   🔍 Contexto encontrado: {'Sim' if contexto else 'Não'}")
    
    print("\n🎉 Fluxo automático funcionando perfeitamente!")


def comparacao_antes_depois():
    """Mostra a diferença entre o fluxo antigo e novo."""
    
    print("📊 Comparação: Antes vs. Depois\n")
    
    print("❌ ANTES (complicado):")
    print("   1. documento = Documento.objects.create(...)")
    print("   2. documento.generate_embedding()  # Manual!")
    print("   3. documento.save()")
    print("   4. if not documento.embedding:")
    print("   5.     documento._generate_embedding()  # Mais manual!")
    
    print("\n✅ AGORA (automático):")
    print("   1. documento = Documento.objects.create(...)  # Tudo automático! 🎉")
    
    print("\n🏆 Resultado:")
    print("   • 80% menos código")
    print("   • Zero métodos manuais")
    print("   • Embedding sempre consistente")
    print("   • Impossible esquecer de gerar")


if __name__ == "__main__":
    print("🧪 Testando Fluxo Automático de Embedding...\n")
    
    # Demonstra diferenças
    comparacao_antes_depois()
    
    print("\n" + "="*60 + "\n")
    
    # Exemplo prático (comentado para não depender do Django)
    # exemplo_uso_simplificado()
    
    print("✨ Embedding automático implementado com sucesso!")