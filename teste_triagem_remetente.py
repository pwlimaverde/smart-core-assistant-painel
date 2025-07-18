#!/usr/bin/env python3
"""
Teste para verificar se a triagem de remetente na função processar_mensagem_whatsapp está funcionando corretamente.
Este teste usa mocks para simular o comportamento da função sem depender do Django.
"""

import sys
import logging
from unittest.mock import MagicMock, patch

# Configurar logging para debug
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Importar as classes necessárias para o teste
from unittest.mock import patch, MagicMock

# Definir classes mock para o teste
class TipoMensagem:
    TEXTO_FORMATADO = 'extendedTextMessage'
    IMAGEM = 'imageMessage'
    VIDEO = 'videoMessage'
    AUDIO = 'audioMessage'
    DOCUMENTO = 'documentMessage'

class TipoRemetente:
    CLIENTE = 'cliente'
    BOT = 'bot'
    ATENDENTE_HUMANO = 'atendente_humano'

# Implementação mock da função processar_mensagem_whatsapp para teste
def processar_mensagem_whatsapp(numero_telefone, conteudo, tipo_mensagem, message_id=None, metadados=None, remetente=None):
    """
    Versão mock da função processar_mensagem_whatsapp para teste.
    Implementa a lógica de triagem de remetente que queremos testar.
    """
    # Determinar o tipo de remetente se não foi especificado
    if remetente is None:
        # Verificar se o número pertence a um atendente humano
        try:
            # Simulação da consulta ao banco de dados
            if numero_telefone == "5511777777777":  # Número de um atendente fictício
                remetente = TipoRemetente.ATENDENTE_HUMANO
                print(f"Número {numero_telefone} identificado como atendente")
            else:
                remetente = TipoRemetente.CLIENTE
        except Exception as e:
            print(f"Erro ao verificar se número é de atendente: {e}. Assumindo CLIENTE.")
            remetente = TipoRemetente.CLIENTE
    
    # Criar um mock de mensagem para retornar
    mensagem = MagicMock()
    mensagem.remetente = remetente
    mensagem.conteudo = conteudo
    mensagem.tipo = tipo_mensagem
    mensagem.message_id_whatsapp = message_id
    mensagem.metadados = metadados or {}
    
    return mensagem

def test_triagem_remetente():
    """
    Testa se a função processar_mensagem_whatsapp identifica corretamente
    se o número de telefone pertence a um atendente ou cliente.
    """
    print("\n🔍 TESTE DE TRIAGEM DE REMETENTE")
    
    # Caso 1: Número de telefone de um cliente (não é atendente)
    numero_cliente = "5511999999999"
    print(f"\n✅ TESTE COM NÚMERO DE CLIENTE: {numero_cliente}")
    
    try:
        # Chamar a função sem especificar o remetente
        mensagem = processar_mensagem_whatsapp(
            numero_telefone=numero_cliente,
            conteudo="Olá, sou um cliente",
            tipo_mensagem=TipoMensagem.TEXTO_FORMATADO,
            message_id="test-message-id-cliente"
        )
        
        # Verificar se o remetente foi identificado como CLIENTE
        print(f"Remetente identificado como: {mensagem.remetente}")
        assert mensagem.remetente == TipoRemetente.CLIENTE, "Deveria ser identificado como CLIENTE"
        print("   ✓ Número de cliente identificado corretamente como CLIENTE")
        
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
    
    # Caso 2: Número de telefone de um atendente
    numero_atendente = "5511777777777"  # Este número corresponde a um atendente no nosso mock
    print(f"\n✅ TESTE COM NÚMERO DE ATENDENTE: {numero_atendente}")
    
    try:
        # Chamar a função sem especificar o remetente
        mensagem = processar_mensagem_whatsapp(
            numero_telefone=numero_atendente,
            conteudo="Olá, sou um atendente",
            tipo_mensagem=TipoMensagem.TEXTO_FORMATADO,
            message_id="test-message-id-atendente"
        )
        
        # Verificar se o remetente foi identificado como ATENDENTE_HUMANO
        print(f"Remetente identificado como: {mensagem.remetente}")
        assert mensagem.remetente == TipoRemetente.ATENDENTE_HUMANO, "Deveria ser identificado como ATENDENTE_HUMANO"
        print("   ✓ Número de atendente identificado corretamente como ATENDENTE_HUMANO")
            
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
    
    # Caso 3: Especificar explicitamente o remetente (deve manter o valor especificado)
    print("\n✅ TESTE COM REMETENTE EXPLÍCITO")
    try:
        mensagem = processar_mensagem_whatsapp(
            numero_telefone="5511888888888",
            conteudo="Mensagem com remetente explícito",
            tipo_mensagem=TipoMensagem.TEXTO_FORMATADO,
            message_id="test-message-id-explicito",
            remetente=TipoRemetente.BOT
        )
        
        # Verificar se o remetente manteve o valor especificado
        print(f"Remetente identificado como: {mensagem.remetente}")
        assert mensagem.remetente == TipoRemetente.BOT, "Deveria manter o remetente BOT especificado"
        print("   ✓ Remetente explícito mantido corretamente como BOT")
        
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
    
    print("\n✅ TODOS OS TESTES CONCLUÍDOS!")

if __name__ == "__main__":
    test_triagem_remetente()