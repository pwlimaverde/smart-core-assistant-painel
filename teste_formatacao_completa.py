#!/usr/bin/env python3
"""
Script de teste para análise de consistência do retorno de _formatar_historico_atendimento
"""

import sys
import os

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource import (
    AnalisePreviaMensagemLangchainDatasource
)

def test_formatacao_completa():
    """Teste completo com log detalhado da formatação."""
    
    datasource = AnalisePreviaMensagemLangchainDatasource()
    
    # Dados simulados completos
    historico_completo = {
        "conteudo_mensagens": [
            "Cliente: Olá, preciso de ajuda com meu pedido #12345",
            "Assistente: Claro! Estou aqui para ajudar. Posso verificar o status do seu pedido #12345.",
            "Cliente: Obrigado, ele está atrasado há 3 dias"
        ],
        "intents_detectados": {"solicitacao_ajuda", "consulta_pedido", "reclamacao_atraso"},
        "entidades_extraidas": {"3 dias", "#12345", "pedido", "ajuda"},
        "atendimentos_anteriores": [
            "Atendimento #001 - Status: Resolvido - Assunto: Troca de produto",
            "Atendimento #002 - Status: Em andamento - Assunto: Reembolso",
            "Atendimento #003 - Status: Pendente - Assunto: Cancelamento"
        ]
    }
    
    print("=" * 80)
    print("TESTE DE FORMATAÇÃO COMPLETA - ANÁLISE DE CONSISTÊNCIA")
    print("=" * 80)
    
    print("\n📊 DADOS DE ENTRADA:")
    print("-" * 40)
    print(f"Conteúdo de mensagens: {len(historico_completo['conteudo_mensagens'])} mensagens")
    for i, msg in enumerate(historico_completo['conteudo_mensagens'], 1):
        print(f"  {i}. {msg}")
    
    print(f"\nIntents detectados: {len(historico_completo['intents_detectados'])} intents")
    for intent in sorted(historico_completo['intents_detectados']):
        print(f"  - {intent}")
    
    print(f"\nEntidades extraídas: {len(historico_completo['entidades_extraidas'])} entidades")
    for entidade in sorted(historico_completo['entidades_extraidas']):
        print(f"  - {entidade}")
    
    print(f"\nAtendimentos anteriores: {len(historico_completo['atendimentos_anteriores'])} registros")
    for i, atendimento in enumerate(historico_completo['atendimentos_anteriores'], 1):
        print(f"  {i}. {atendimento}")
    
    print("\n" + "=" * 80)
    print("📋 RESULTADO FORMATADO:")
    print("=" * 80)
    
    resultado = datasource._formatar_historico_atendimento(historico_completo)
    print(resultado)
    
    print("\n" + "=" * 80)
    print("🔍 ANÁLISE DE CONSISTÊNCIA:")
    print("=" * 80)
    
    # Verificar estrutura
    linhas = resultado.split('\n')
    print(f"Total de linhas: {len(linhas)}")
    
    # Identificar seções
    secoes = []
    for i, linha in enumerate(linhas):
        if linha.endswith(':') and not linha.startswith('  ') and not linha.startswith('-'):
            secoes.append((i, linha))
    
    print(f"Seções encontradas: {len(secoes)}")
    for idx, secao in secoes:
        print(f"  Linha {idx+1}: {secao}")
    
    # Verificar ordem das seções
    ordem_esperada = [
        "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:",
        "ATENDIMENTOS ANTERIORES:",
        "ELEMENTOS IDENTIFICADOS:",
        "INTENÇÕES PREVIAMENTE DETECTADAS:",
        "HISTÓRICO DA CONVERSA:"
    ]
    
    print(f"\nOrdem das seções:")
    ordem_encontrada = [secao[1] for secao in secoes]
    for esperada, encontrada in zip(ordem_esperada, ordem_encontrada):
        status = "✅" if esperada == encontrada else "❌"
        print(f"  {status} Esperado: {esperada}")
        print(f"  {status} Encontrado: {encontrada}")
    
    # Testar cenários adicionais
    print("\n" + "=" * 80)
    print("🧪 TESTES ADICIONAIS:")
    print("=" * 80)
    
    # Teste 1: Apenas mensagens
    print("\n1️⃣ TESTE - Apenas mensagens:")
    print("-" * 30)
    historico_minimo = {"conteudo_mensagens": ["Olá, tudo bem?"]}
    resultado_minimo = datasource._formatar_historico_atendimento(historico_minimo)
    print(resultado_minimo)
    
    # Teste 2: Apenas atendimentos anteriores
    print("\n2️⃣ TESTE - Apenas atendimentos anteriores:")
    print("-" * 30)
    historico_atendimentos = {"atendimentos_anteriores": ["Atendimento #001 - Teste"]}
    resultado_atendimentos = datasource._formatar_historico_atendimento(historico_atendimentos)
    print(resultado_atendimentos)
    
    # Teste 3: Vazio
    print("\n3️⃣ TESTE - Histórico vazio:")
    print("-" * 30)
    historico_vazio = {}
    resultado_vazio = datasource._formatar_historico_atendimento(historico_vazio)
    print(resultado_vazio)
    
    print("\n" + "=" * 80)
    print("✅ TESTE CONCLUÍDO")
    print("=" * 80)

if __name__ == "__main__":
    test_formatacao_completa()