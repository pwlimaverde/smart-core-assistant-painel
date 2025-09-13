#!/usr/bin/env python
"""
Teste para verificar se os logs aparecem durante o processamento real de mensagens.
"""

import os
import sys
import django
from loguru import logger

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_core_assistant_painel.app.ui.core.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
django.setup()

from smart_core_assistant_painel.app.ui.atendimentos.models import Mensagem
from smart_core_assistant_painel.app.ui.atendimentos.utils import (
    send_message_response,
    set_wa_buffer,
    _analisar_conteudo_mensagem
)
from smart_core_assistant_painel.modules.ai_engine.features.load_mensage_data.domain.model.message_data import MessageData


def test_message_processing_with_logs() -> None:
    """Testa o processamento completo de uma mensagem com logs."""
    try:
        # Buscar a mensagem ID 5
        mensagem = Mensagem.objects.get(id=5)
        print(f"Mensagem ID: {mensagem.id}")
        print(f"Conteúdo: {mensagem.conteudo}")
        print(f"Intent detectado: {mensagem.intent_detectado}")
        
        # Criar MessageData para simular o buffer
        message_data = MessageData(
            instance="test_instance",
            api_key="test_api_key",
            numero_telefone="5511999999999",
            from_me=False,
            conteudo=mensagem.conteudo,
            message_type="conversation",
            message_id="test_message_id",
            metadados={},
            nome_perfil_whatsapp="Teste"
        )
        
        # Adicionar ao buffer
        print("\n=== Adicionando ao buffer ===")
        set_wa_buffer(message_data)
        
        # Chamar send_message_response que deve processar o buffer
        print("\n=== Processando mensagem ===")
        logger.info(f"Iniciando processamento para: {message_data.numero_telefone}")
        send_message_response(message_data.numero_telefone)
        
        print("✅ Processamento completo executado!")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()


def test_analyze_content_directly() -> None:
    """Testa diretamente a função de análise de conteúdo."""
    try:
        print("\n=== Teste Direto da Análise de Conteúdo ===")
        
        # Buscar a mensagem ID 5
        mensagem = Mensagem.objects.get(id=5)
        
        # Chamar diretamente a função de análise
        logger.info(f"Analisando conteúdo: {mensagem.conteudo}")
        resultado = _analisar_conteudo_mensagem(mensagem.conteudo)
        
        print(f"Resultado da análise: {resultado}")
        print(f"Intent types: {resultado.intent_types}")
        
        print("✅ Análise direta executada!")
        
    except Exception as e:
        print(f"❌ Erro durante análise direta: {e}")
        import traceback
        traceback.print_exc()


def test_direct_log_output() -> None:
    """Testa se os logs diretos funcionam."""
    print("\n=== Teste Direto de Logs ===")
    logger.debug("Este é um log DEBUG")
    logger.info("Este é um log INFO")
    logger.warning("Este é um log WARNING")
    logger.error("Este é um log ERROR")
    logger.critical("Este é um log CRITICAL")
    print("✅ Logs diretos executados!")


if __name__ == "__main__":
    test_direct_log_output()
    test_analyze_content_directly()
    test_message_processing_with_logs()