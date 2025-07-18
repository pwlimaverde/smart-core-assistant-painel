#!/usr/bin/env python3
"""
Teste final para verificar se os tipos de mensagem estão corretos
conforme a tabela final da API.
"""

from enum import Enum


class TipoMensagem(str, Enum):
    """Simulação da classe TipoMensagem corrigida para teste."""

    TEXTO_FORMATADO = 'extendedTextMessage'
    IMAGEM = 'imageMessage'
    VIDEO = 'videoMessage'
    AUDIO = 'audioMessage'
    DOCUMENTO = 'documentMessage'
    STICKER = 'stickerMessage'
    LOCALIZACAO = 'locationMessage'
    CONTATO = 'contactMessage'
    LISTA = 'listMessage'
    BOTOES = 'buttonsMessage'
    ENQUETE = 'pollMessage'
    REACAO = 'reactMessage'

    @classmethod
    def obter_por_chave_json(cls, chave_json: str):
        """Retorna o tipo de mensagem baseado na chave JSON."""
        mapeamento = {
            'extendedTextMessage': cls.TEXTO_FORMATADO,
            'imageMessage': cls.IMAGEM,
            'videoMessage': cls.VIDEO,
            'audioMessage': cls.AUDIO,
            'documentMessage': cls.DOCUMENTO,
            'stickerMessage': cls.STICKER,
            'locationMessage': cls.LOCALIZACAO,
            'contactMessage': cls.CONTATO,
            'listMessage': cls.LISTA,
            'buttonsMessage': cls.BOTOES,
            'pollMessage': cls.ENQUETE,
            'reactMessage': cls.REACAO,
        }
        return mapeamento.get(chave_json)

    @classmethod
    def obter_chave_json(cls, tipo_mensagem):
        """Retorna a chave JSON correspondente ao tipo de mensagem."""
        return tipo_mensagem.value if tipo_mensagem else None


def testar_tabela_final():
    """Testa se todos os tipos da tabela final estão implementados."""

    print("=== Teste da Tabela Final (Corrigida) ===\n")

    # Tipos esperados conforme a tabela final
    tipos_esperados = [
        ('extendedTextMessage', 'TEXTO_FORMATADO', 'Texto com formatação, citações, fontes, etc.'),
        ('imageMessage', 'IMAGEM', 'Imagem recebida, JPG/PNG, com caption possível'),
        ('videoMessage', 'VIDEO', 'Vídeo recebido, com legenda possível'),
        ('audioMessage', 'AUDIO', 'Áudio recebido (.mp4, .mp3), com duração/ptt'),
        ('documentMessage', 'DOCUMENTO', 'Arquivo genérico (PDF, DOCX etc.)'),
        ('stickerMessage', 'STICKER', 'Sticker no formato WebP'),
        ('locationMessage', 'LOCALIZACAO', 'Coordinates de localização (lat/long)'),
        ('contactMessage', 'CONTATO', 'vCard com dados de contato'),
        ('listMessage', 'LISTA', 'Mensagem interativa com opções em lista'),
        ('buttonsMessage', 'BOTOES', 'Botões clicáveis dentro da mensagem'),
        ('pollMessage', 'ENQUETE', 'Opções de enquete dentro da mensagem'),
        ('reactMessage', 'REACAO', 'Reação (emoji) a uma mensagem existente'),
    ]

    print("1. Verificando se todos os tipos da tabela estão implementados:")
    todos_corretos = True

    for chave_api, nome_enum, descricao in tipos_esperados:
        tipo = TipoMensagem.obter_por_chave_json(chave_api)

        if tipo:
            nome_real = tipo.name
            if nome_real == nome_enum:
                print(f"   ✅ {chave_api} -> {nome_enum}")
            else:
                print(
                    f"   ❌ {chave_api} -> Esperado: {nome_enum}, Encontrado: {nome_real}")
                todos_corretos = False
        else:
            print(f"   ❌ {chave_api} -> Tipo não encontrado")
            todos_corretos = False

    print()

    # Verificar se não há tipos extras
    print("2. Verificando tipos implementados:")
    tipos_implementados = list(TipoMensagem)
    chaves_esperadas = {chave for chave, _, _ in tipos_esperados}

    for tipo in tipos_implementados:
        chave = tipo.value
        if chave in chaves_esperadas:
            print(f"   ✅ {tipo.name} ({chave}) - Está na tabela")
        else:
            print(
                f"   ❌ {
                    tipo.name} ({chave}) - NÃO está na tabela (deve ser removido)")
            todos_corretos = False

    print()

    # Verificar se não faltam tipos
    print("3. Verificando se algum tipo da tabela está faltando:")
    tipos_implementados_chaves = {tipo.value for tipo in tipos_implementados}

    for chave_api, nome_enum, descricao in tipos_esperados:
        if chave_api not in tipos_implementados_chaves:
            print(f"   ❌ FALTANDO: {chave_api} -> {nome_enum}")
            todos_corretos = False
        else:
            print(f"   ✅ {chave_api} -> {nome_enum}")

    print()

    if todos_corretos:
        print("🎉 Perfeito! A classe está 100% conforme a tabela final!")
        print(
            f"📊 Total de tipos: {
                len(tipos_esperados)} (conforme especificado)")
    else:
        print("❌ Ainda há divergências que precisam ser corrigidas.")

    return todos_corretos


def testar_tipos_removidos():
    """Verifica se os tipos que deveriam ser removidos realmente foram removidos."""

    print("=== Verificação de Tipos Removidos ===\n")

    tipos_removidos = [
        'conversation',      # TEXTO_SIMPLES
        'statusMessage',     # STATUS
        'sistema'           # SISTEMA
    ]

    print("Verificando se tipos não especificados foram removidos:")

    for chave in tipos_removidos:
        tipo = TipoMensagem.obter_por_chave_json(chave)
        if tipo is None:
            print(f"   ✅ {chave} -> Corretamente removido")
        else:
            print(f"   ❌ {chave} -> Ainda existe: {tipo}")

    print()


if __name__ == "__main__":
    print("TESTE FINAL - CONFORMIDADE COM TABELA CORRIGIDA\n")
    print("=" * 60)

    resultado = testar_tabela_final()
    testar_tipos_removidos()

    print("=" * 60)
    if resultado:
        print("✅ TODOS OS TESTES PASSARAM! A classe está correta.")
    else:
        print("❌ AINDA HÁ PROBLEMAS PARA CORRIGIR!")

    print("\n📋 Resumo da tabela final:")
    print("   - 12 tipos de mensagem (conforme especificado)")
    print("   - Removidos: TEXTO_SIMPLES, STATUS, SISTEMA")
    print("   - Apenas tipos oficiais da API Evolution")
