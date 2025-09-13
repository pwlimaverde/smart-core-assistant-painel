#!/usr/bin/env python
"""
Script para verificar a estrutura dos dados da mensagem ID 5 e o problema no loop.
"""

import os
import sys
import django
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar Django para usar o banco de produção
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_core_assistant_painel.app.ui.core.settings")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
django.setup()

from smart_core_assistant_painel.app.ui.atendimentos.models import Mensagem

def check_message_and_query_compose():
    """Verifica a mensagem ID 5 e o modelo QueryCompose."""
    try:
        mensagem = Mensagem.objects.get(id=5)
        
        print(f"=== Análise da Mensagem ID 5 ===")
        print(f"ID: {mensagem.id}")
        print(f"Conteúdo: {mensagem.conteudo}")
        print(f"Intent detectado: {mensagem.intent_detectado}")
        print(f"Tipo: {type(mensagem.intent_detectado)}")
        print(f"Comprimento: {len(mensagem.intent_detectado) if mensagem.intent_detectado else 0}")
        
        # Verificar se QueryCompose existe
        try:
            from smart_core_assistant_painel.app.ui.treinamento.models import QueryCompose
            print("\n=== Verificação do Modelo QueryCompose ===")
            
            # Listar todas as tags disponíveis
            all_qc = QueryCompose.objects.all()
            print(f"Total de QueryCompose registros: {all_qc.count()}")
            
            if all_qc.exists():
                print("\nTags disponíveis:")
                for qc in all_qc:
                    print(f"  - Tag: '{qc.tag}' | Comportamento: '{qc.comportamento[:50]}...'")
            else:
                print("❌ PROBLEMA: Nenhum registro QueryCompose encontrado!")
                
        except ImportError:
            print("❌ PROBLEMA: Modelo QueryCompose não encontrado!")
            return
            
        # Simular o loop original exatamente como no código
        print("\n=== Simulação Exata do Loop Original ===")
        prompt_intent = ""
        
        for index, intent in enumerate(mensagem.intent_detectado, start=1):
            print(f"\nLoop iteração {index}:")
            print(f"  Intent: {intent}")
            print(f"  Tipo do intent: {type(intent)}")
            
            try:
                # Código exato do utils.py linha 72
                tag = list(intent.keys())[0]
                print(f"  Tag extraída: '{tag}'")
                
                # Código exato do utils.py linha 73-75
                qc = QueryCompose.objects.filter(tag=tag).first()
                print(f"  QueryCompose encontrado: {qc}")
                
                if qc:
                    comportamento_text = f"{index} - {qc.comportamento}\n"
                    prompt_intent += comportamento_text
                    print(f"  ✅ Adicionado ao prompt: '{comportamento_text.strip()}'")
                else:
                    print(f"  ❌ PROBLEMA: Nenhum QueryCompose encontrado para tag '{tag}'")
                    
            except Exception as e:
                print(f"  ❌ ERRO no processamento do intent: {e}")
                print(f"  Tipo do erro: {type(e)}")
        
        print(f"\n=== Resultado Final ===")
        print(f"Prompt intent gerado: '{prompt_intent}'")
        print(f"Comprimento do prompt: {len(prompt_intent)}")
        
        if not prompt_intent.strip():
            print("\n❌ PROBLEMA IDENTIFICADO: prompt_intent está vazio!")
            print("Possíveis causas:")
            print("1. Não existem registros QueryCompose para as tags dos intents")
            print("2. As tags nos intents não correspondem às tags no QueryCompose")
            print("3. Erro na estrutura dos dados dos intents")
        else:
            print("\n✅ Prompt intent gerado com sucesso!")
        
    except Mensagem.DoesNotExist:
        print("❌ Mensagem com ID 5 não encontrada")
    except Exception as e:
        print(f"❌ Erro: {e}")
        print(f"Tipo do erro: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_message_and_query_compose()