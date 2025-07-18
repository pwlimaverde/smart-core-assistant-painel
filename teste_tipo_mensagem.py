#!/usr/bin/env python3
"""
Teste simples para verificar se os métodos da classe TipoMensagem funcionam.
"""

# Simulando a classe TipoMensagem para teste sem Django
from enum import Enum


class TipoMensagem(str, Enum):
    """Simulação da classe TipoMensagem para teste."""

    TEXTO = 'extendedTextMessage'
    AUDIO = 'audioMessage'
    VIDEO = 'videoMessage'
    IMAGEM = 'imageMessage'
    DOCUMENTO = 'documentMessage'
    LOCALIZACAO = 'locationMessage'
    CONTATO = 'contactMessage'
    ADESIVO = 'stickerMessage'
    TEMPLATE = 'templateMessage'
    INTERATIVA_BOTOES = 'buttonsMessage'
    INTERATIVA_LISTA = 'listMessage'
    REACAO = 'reactionMessage'
    ENQUETE = 'pollCreationMessage'
    SISTEMA = 'sistema'

    # Mapeamento das chaves JSON para os tipos
    _CHAVE_PARA_TIPO = {
        'extendedTextMessage': 'TEXTO',
        'audioMessage': 'AUDIO',
        'videoMessage': 'VIDEO',
        'imageMessage': 'IMAGEM',
        'documentMessage': 'DOCUMENTO',
        'locationMessage': 'LOCALIZACAO',
        'contactMessage': 'CONTATO',
        'stickerMessage': 'ADESIVO',
        'templateMessage': 'TEMPLATE',
        'buttonsMessage': 'INTERATIVA_BOTOES',
        'listMessage': 'INTERATIVA_LISTA',
        'reactionMessage': 'REACAO',
        'pollCreationMessage': 'ENQUETE',
        'sistema': 'SISTEMA',
    }

    @classmethod
    def obter_por_chave_json(cls, chave_json: str):
        """Retorna o tipo de mensagem baseado na chave JSON."""
        # Acessa o dicionário de classe corretamente
        chave_para_tipo = {
            'extendedTextMessage': cls.TEXTO,
            'audioMessage': cls.AUDIO,
            'videoMessage': cls.VIDEO,
            'imageMessage': cls.IMAGEM,
            'documentMessage': cls.DOCUMENTO,
            'locationMessage': cls.LOCALIZACAO,
            'contactMessage': cls.CONTATO,
            'stickerMessage': cls.ADESIVO,
            'templateMessage': cls.TEMPLATE,
            'buttonsMessage': cls.INTERATIVA_BOTOES,
            'listMessage': cls.INTERATIVA_LISTA,
            'reactionMessage': cls.REACAO,
            'pollCreationMessage': cls.ENQUETE,
            'sistema': cls.SISTEMA,
        }
        return chave_para_tipo.get(chave_json)

    @classmethod
    def obter_chave_json(cls, tipo_mensagem):
        """Retorna a chave JSON correspondente ao tipo de mensagem."""
        return tipo_mensagem.value if tipo_mensagem else None


def testar_metodos():
    """Testa os métodos da classe TipoMensagem."""

    print("=== Teste dos Métodos TipoMensagem ===\n")

    # Teste 1: obter_por_chave_json
    print("1. Teste obter_por_chave_json:")

    testes = [
        'extendedTextMessage',
        'audioMessage',
        'imageMessage',
        'buttonsMessage',
        'pollCreationMessage',
        'chave_inexistente'
    ]

    for chave in testes:
        resultado = TipoMensagem.obter_por_chave_json(chave)
        status = "✅" if resultado else "❌"
        print(f"   {status} {chave} -> {resultado}")

    print()

    # Teste 2: obter_chave_json
    print("2. Teste obter_chave_json:")

    tipos_teste = [
        TipoMensagem.TEXTO,
        TipoMensagem.AUDIO,
        TipoMensagem.IMAGEM,
        TipoMensagem.INTERATIVA_BOTOES,
        TipoMensagem.ENQUETE
    ]

    for tipo in tipos_teste:
        chave = TipoMensagem.obter_chave_json(tipo)
        print(f"   ✅ {tipo.name} -> {chave}")

    print()

    # Teste 3: Verificação de correspondência bidirecional
    print("3. Teste de correspondência bidirecional:")

    for tipo in TipoMensagem:
        chave = TipoMensagem.obter_chave_json(tipo)
        tipo_recuperado = TipoMensagem.obter_por_chave_json(chave)

        if tipo == tipo_recuperado:
            print(f"   ✅ {tipo.name} <-> {chave}")
        else:
            print(
                f"   ❌ {
                    tipo.name} <-> {chave} (recuperado: {tipo_recuperado})")

    print("\n=== Teste Concluído ===")


if __name__ == "__main__":
    testar_metodos()
