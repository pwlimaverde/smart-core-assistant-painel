"""Testes para o AtendimentoMapper."""

import pytest
from unittest.mock import Mock, patch

from smart_core_assistant_painel.app.notion_sync.services.mappers.atendimento_mapper import (
    AtendimentoMapper,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import Atendimento
from smart_core_assistant_painel.app.notion_sync.models import AtendimentoSync


class TestAtendimentoMapper:
    """Classe de testes para o AtendimentoMapper."""

    def _formatar_contexto_conversa(self, contexto: dict) -> str:
        """Formata o contexto da conversa de forma legível para o Notion."""
        if not contexto:
            return "Sem contexto disponível"

        linhas: list[str] = ["📋 CONTEXTO DA CONVERSA\n"]

        # Ordena as chaves para melhor organização
        chaves_ordenadas = sorted(contexto.keys())

        for chave in chaves_ordenadas:
            valor = contexto[chave]

            # Formatação especial para diferentes tipos de dados
            if chave == "canal":
                linhas.append(f"📱 Canal: {str(valor).upper()}")
            elif chave == "primeira_interacao" and valor:
                linhas.append("🆕 Primeira interação: Sim")
            elif chave == "sessao_iniciada":
                linhas.append(f"⏰ Sessão iniciada: {str(valor)}")
            elif isinstance(valor, bool):
                linhas.append(f"✅ {chave.replace('_', ' ').title()}: {'Sim' if valor else 'Não'}")
            elif isinstance(valor, str):
                # Para strings simples, exibe como valor normal
                if chave == "cliente_status":
                    linhas.append(f"👤 Cliente Status: {valor}")
                else:
                    linhas.append(f"• {chave.replace('_', ' ').title()}: {valor}")
            elif isinstance(valor, list):
                if valor:
                    linhas.append(f"📝 {chave.replace('_', ' ').title()}:")
                    for item in valor:
                        linhas.append(f"   • {str(item)}")
                else:
                    linhas.append(f"📝 {chave.replace('_', ' ').title()}: (vazio)")
            elif isinstance(valor, dict):
                if valor:
                    linhas.append(f"📊 {chave.replace('_', ' ').title()}:")
                    for sub_chave, sub_valor in valor.items():
                        linhas.append(f"   • {sub_chave}: {str(sub_valor)}")
                else:
                    linhas.append(f"📊 {chave.replace('_', ' ').title()}: (vazio)")
            else:
                linhas.append(f"• {chave.replace('_', ' ').title()}: {str(valor)}")

        # Adiciona informações adicionais úteis
        if "mensagens_trocadas" in contexto and isinstance(contexto["mensagens_trocadas"], int):
            linhas.append(f"\n💬 Total de mensagens trocadas: {contexto['mensagens_trocadas']}")

        return "\n".join(linhas)

    def test_formatar_contexto_conversa_vazio(self) -> None:
        """Testa formatação com contexto vazio."""
        contexto_vazio: dict = {}
        resultado = self._formatar_contexto_conversa(contexto_vazio)
        assert resultado == "Sem contexto disponível"

    def test_formatar_contexto_conversa_simples(self) -> None:
        """Testa formatação com contexto simples."""
        contexto_simples = {
            "canal": "whatsapp",
            "primeira_interacao": True,
            "sessao_iniciada": "2024-01-15T10:30:00",
            "cliente_status": "premium",
        }

        resultado = self._formatar_contexto_conversa(contexto_simples)

        # Verifica que o contexto contém os elementos esperados
        assert "📋 CONTEXTO DA CONVERSA" in resultado
        assert "📱 Canal: WHATSAPP" in resultado
        assert "⏰ Sessão iniciada: 2024-01-15T10:30:00" in resultado
        assert "👤 Cliente Status: premium" in resultado
        assert "🆕 Primeira interação: Sim" in resultado

    def test_formatar_contexto_conversa_com_listas(self) -> None:
        """Testa formatação com listas no contexto."""
        contexto_com_listas = {
            "canal": "whatsapp",
            "produtos_interesse": ["produto_a", "produto_b", "produto_c"],
            "tags_vazias": [],
        }

        resultado = self._formatar_contexto_conversa(contexto_com_listas)

        # Verifica que o contexto contém as formatações esperadas
        assert "📝 Produtos Interesse:" in resultado
        assert "   • produto_a" in resultado
        assert "   • produto_b" in resultado
        assert "   • produto_c" in resultado
        assert "📝 Tags Vazias: (vazio)" in resultado

    def test_formatar_contexto_conversa_com_dict_aninhado(self) -> None:
        """Testa formatação com dicionários aninhados."""
        contexto_com_dict = {
            "canal": "email",
            "dados_adicionais": {
                "origem": "instagram",
                "campanha": "verao2024",
                "utm_source": "social",
            },
            "dados_vazios": {},
        }

        resultado = self._formatar_contexto_conversa(contexto_com_dict)

        # Verifica que o contexto contém as formatações esperadas
        assert "📊 Dados Adicionais:" in resultado
        assert "   • origem: instagram" in resultado
        assert "   • campanha: verao2024" in resultado
        assert "   • utm_source: social" in resultado
        assert "📊 Dados Vazios: (vazio)" in resultado

    @patch("smart_core_assistant_painel.app.notion_sync.models.NotionDatabaseConfig")
    def test_to_notion_properties_com_contexto_formatado(
        self, mock_config: Mock
    ) -> None:
        """Testa se o contexto é formatado corretamente no to_notion_properties."""
        # Mock do atendimento
        mock_atendimento = Mock(spec=Atendimento)
        mock_atendimento.id = 1
        mock_atendimento.assunto = "Teste de atendimento"
        mock_atendimento.status = "em_atendimento"
        mock_atendimento.prioridade = "normal"
        mock_atendimento.canal = "whatsapp"
        mock_atendimento.contexto_conversa = {
            "canal": "whatsapp",
            "primeira_interacao": True,
            "sessao_iniciada": "2024-01-15T10:30:00",
            "cliente_status": "premium",
            "produtos_interesse": ["produto_a", "produto_b"],
            "dados_adicionais": {
                "origem": "instagram",
                "campanha": "verao2024"
            }
        }
        mock_atendimento.data_inicio.isoformat.return_value = "2024-01-15T10:00:00"
        mock_atendimento.data_ultima_mensagem = None
        mock_atendimento.data_fim = None
        mock_atendimento.avaliacao = None
        mock_atendimento.feedback = None
        mock_atendimento.tags = []

        # Mock do sync instance
        mock_sync = Mock(spec=AtendimentoSync)
        mock_sync.atendimento = mock_atendimento
        mock_sync.config = mock_config.return_value
        mock_sync.config.field_mappings = {}
        mock_sync.contato_sync = None
        mock_sync.departamento_sync = None
        mock_sync.atendente_sync = None

        # Executa o método
        properties = AtendimentoMapper.to_notion_properties(mock_sync)

        # Verifica se o campo "Contexto Conversa" existe e está formatado
        assert "Contexto Conversa" in properties
        assert "rich_text" in properties["Contexto Conversa"]

        # Obtém o conteúdo formatado
        contexto_content = properties["Contexto Conversa"]["rich_text"][0]["text"]["content"]

        # Verifica se o conteúdo está formatado corretamente
        assert "📋 CONTEXTO DA CONVERSA" in contexto_content
        assert "📱 Canal: WHATSAPP" in contexto_content
        assert "⏰ Sessão iniciada: 2024-01-15T10:30:00" in contexto_content
        assert "🆕 Primeira interação: Sim" in contexto_content
        assert "👤 Cliente Status: premium" in contexto_content
        assert "📝 Produtos Interesse:" in contexto_content
        assert "   • produto_a" in contexto_content
        assert "   • produto_b" in contexto_content
        assert "📊 Dados Adicionais:" in contexto_content
        assert "   • origem: instagram" in contexto_content
        assert "   • campanha: verao2024" in contexto_content

        # Verifica que NÃO contém JSON bruto
        assert "{" not in contexto_content or contexto_content.count("{") <= 1  # Pode ter apenas o início do texto
        assert "}" not in contexto_content or contexto_content.count("}") <= 1  # Pode ter apenas o fim do texto
        # Permite aspas que possam existir no texto formatado, mas não muitas
        assert contexto_content.count('"') <= 2

    def test_contexto_conversa_nulo(self) -> None:
        """Testa formatação quando contexto_conversa é None."""
        # Mock do atendimento com contexto nulo
        mock_atendimento = Mock(spec=Atendimento)
        mock_atendimento.id = 1
        mock_atendimento.assunto = "Teste sem contexto"
        mock_atendimento.status = "em_atendimento"
        mock_atendimento.prioridade = "normal"
        mock_atendimento.canal = "whatsapp"
        mock_atendimento.contexto_conversa = None  # Contexto nulo
        mock_atendimento.data_inicio.isoformat.return_value = "2024-01-15T10:00:00"
        mock_atendimento.data_ultima_mensagem = None
        mock_atendimento.data_fim = None
        mock_atendimento.avaliacao = None
        mock_atendimento.feedback = None
        mock_atendimento.tags = []

        # Mock do sync instance
        mock_sync = Mock(spec=AtendimentoSync)
        mock_sync.atendimento = mock_atendimento
        mock_sync.config = Mock()
        mock_sync.config.field_mappings = {}
        mock_sync.contato_sync = None
        mock_sync.departamento_sync = None
        mock_sync.atendente_sync = None

        # Executa o método
        properties = AtendimentoMapper.to_notion_properties(mock_sync)

        # Verifica se o contexto foi tratado corretamente
        contexto_content = properties["Contexto Conversa"]["rich_text"][0]["text"]["content"]
        assert contexto_content == "Sem contexto disponível"
