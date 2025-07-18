#!/usr/bin/env python3
"""
Exemplo de uso da classe TipoMensagem atualizada.

Este arquivo demonstra como usar os novos métodos para converter entre
chaves JSON e tipos de mensagem.
"""

from smart_core_assistant_painel.app.ui.oraculo.models import TipoMensagem
import os
import sys

# Adiciona o diretório do projeto ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def exemplo_uso_tipo_mensagem():
    """Demonstra o uso dos métodos da classe TipoMensagem."""

    print("=== Exemplo de Uso da Classe TipoMensagem ===\n")

    # Exemplo 1: Obter tipo por chave JSON
    print("1. Obtendo tipo por chave JSON:")
    chaves_exemplo = [
        'extendedTextMessage',
        'audioMessage',
        'imageMessage',
        'buttonsMessage',
        'pollCreationMessage',
        'chave_inexistente'
    ]

    for chave in chaves_exemplo:
        tipo = TipoMensagem.obter_por_chave_json(chave)
        if tipo:
            print(f"   {chave} -> {tipo} ({tipo.label})")
        else:
            print(f"   {chave} -> Tipo não encontrado")

    print()

    # Exemplo 2: Obter chave JSON por tipo
    print("2. Obtendo chave JSON por tipo:")
    tipos_exemplo = [
        TipoMensagem.TEXTO,
        TipoMensagem.AUDIO,
        TipoMensagem.IMAGEM,
        TipoMensagem.INTERATIVA_BOTOES,
        TipoMensagem.ENQUETE,
        TipoMensagem.SISTEMA
    ]

    for tipo in tipos_exemplo:
        chave = TipoMensagem.obter_chave_json(tipo)
        print(f"   {tipo} -> {chave}")

    print()

    # Exemplo 3: Listando todos os tipos disponíveis
    print("3. Todos os tipos de mensagem disponíveis:")
    for tipo in TipoMensagem:
        chave = TipoMensagem.obter_chave_json(tipo)
        print(f"   {tipo.name}: {tipo.value} -> JSON: {chave}")
        print(f"      Descrição: {tipo.label}")
        print()


if __name__ == "__main__":
    exemplo_uso_tipo_mensagem()
