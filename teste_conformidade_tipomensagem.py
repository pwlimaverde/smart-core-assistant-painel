#!/usr/bin/env python3
"""
Teste atualizado para verificar se os tipos de mensagem estão corretos
conforme a tabela da API.
"""

from enum import Enum


class TipoMensagem(str, Enum):
    """Simulação da classe TipoMensagem atualizada para teste."""

    TEXTO_ESTENDIDO = 'extendedTextMessage'
    TEXTO_SIMPLES = 'conversation'
    IMAGEM = 'imageMessage'
    VIDEO = 'videoMessage'
    AUDIO = 'audioMessage'
    DOCUMENTO = 'documentMessage'
    STICKER = 'stickerMessage'
    LOCALIZACAO = 'locationMessage'
    CONTATO = 'contactMessage'
    LISTA = 'listMessage'
    BOTAO = 'buttonsMessage'
    ENQUETE = 'pollMessage'
    REACAO = 'reactMessage'
    STATUS = 'statusMessage'
    SISTEMA = 'sistema'

    @classmethod
    def obter_por_chave_json(cls, chave_json: str):
        """Retorna o tipo de mensagem baseado na chave JSON."""
        mapeamento = {
            'extendedTextMessage': cls.TEXTO_ESTENDIDO,
            'conversation': cls.TEXTO_SIMPLES,
            'imageMessage': cls.IMAGEM,
            'videoMessage': cls.VIDEO,
            'audioMessage': cls.AUDIO,
            'documentMessage': cls.DOCUMENTO,
            'stickerMessage': cls.STICKER,
            'locationMessage': cls.LOCALIZACAO,
            'contactMessage': cls.CONTATO,
            'listMessage': cls.LISTA,
            'buttonsMessage': cls.BOTAO,
            'pollMessage': cls.ENQUETE,
            'reactMessage': cls.REACAO,
            'statusMessage': cls.STATUS,
            'sistema': cls.SISTEMA,
        }
        return mapeamento.get(chave_json)

    @classmethod
    def obter_chave_json(cls, tipo_mensagem):
        """Retorna a chave JSON correspondente ao tipo de mensagem."""
        return tipo_mensagem.value if tipo_mensagem else None


def testar_conformidade_com_tabela():
    """Testa se todos os tipos da tabela estão implementados."""

    print("=== Teste de Conformidade com a Tabela da API ===\n")

    # Tipos esperados conforme a tabela
    tipos_esperados = [
        ('extendedTextMessage', 'TEXTO_ESTENDIDO', 'Mensagens de texto simples ou formatadas'),
        ('conversation', 'TEXTO_SIMPLES', 'Mensagens de texto sem formatação'),
        ('imageMessage', 'IMAGEM', 'Envia imagem (PNG, JPG); aceita caption opcional'),
        ('videoMessage', 'VIDEO', 'Envia vídeo; aceita legenda'),
        ('audioMessage', 'AUDIO', 'Envia arquivo de áudio (mp3, opus, etc.)'),
        ('documentMessage', 'DOCUMENTO', 'Envia qualquer tipo de arquivo (PDF, DOCX etc.)'),
        ('stickerMessage', 'STICKER', 'Envia stickers (WebP)'),
        ('locationMessage', 'LOCALIZACAO', 'Envia localização geográfica com lat/long'),
        ('contactMessage', 'CONTATO', 'Envia cartão de contato vCard'),
        ('listMessage', 'LISTA', 'Mensagem com seleção de opções em lista'),
        ('buttonsMessage', 'BOTAO', 'Mensagem com botões clicáveis'),
        ('pollMessage', 'ENQUETE', 'Envia enquete com alternativa de escolha'),
        ('reactMessage', 'REACAO', 'Envia reação (emoji) a uma mensagem existente'),
        ('statusMessage', 'STATUS', 'Envia conteúdo ao status (modo story)'),
        ('sistema', 'SISTEMA', 'Mensagem do Sistema'),
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

    # Teste bidirecional
    print("2. Teste de correspondência bidirecional:")
    for chave_api, nome_enum, descricao in tipos_esperados:
        tipo = TipoMensagem.obter_por_chave_json(chave_api)
        if tipo:
            chave_retornada = TipoMensagem.obter_chave_json(tipo)
            if chave_retornada == chave_api:
                print(f"   ✅ {nome_enum} <-> {chave_api}")
            else:
                print(
                    f"   ❌ {nome_enum} -> Esperado: {chave_api}, Retornado: {chave_retornada}")
                todos_corretos = False

    print()

    # Verificar se não há tipos extras
    print("3. Verificando tipos implementados:")
    tipos_implementados = list(TipoMensagem)
    chaves_esperadas = {chave for chave, _, _ in tipos_esperados}

    for tipo in tipos_implementados:
        chave = tipo.value
        if chave in chaves_esperadas:
            print(f"   ✅ {tipo.name} ({chave}) - Está na tabela")
        else:
            print(
                f"   ⚠️  {
                    tipo.name} ({chave}) - Não está na tabela (pode ser extra)")

    print()

    if todos_corretos:
        print("🎉 Todos os tipos estão corretos e conformes com a tabela da API!")
    else:
        print("❌ Há divergências que precisam ser corrigidas.")

    return todos_corretos


def testar_casos_uso():
    """Testa casos de uso comuns."""

    print("=== Teste de Casos de Uso ===\n")

    # Caso 1: Mensagem de texto simples
    print("1. Processando mensagem de texto simples:")
    chave = 'conversation'
    tipo = TipoMensagem.obter_por_chave_json(chave)
    if tipo == TipoMensagem.TEXTO_SIMPLES:
        print(f"   ✅ {chave} -> {tipo.name}")
    else:
        print(f"   ❌ {chave} -> {tipo}")

    # Caso 2: Mensagem de texto formatada
    print("2. Processando mensagem de texto formatada:")
    chave = 'extendedTextMessage'
    tipo = TipoMensagem.obter_por_chave_json(chave)
    if tipo == TipoMensagem.TEXTO_ESTENDIDO:
        print(f"   ✅ {chave} -> {tipo.name}")
    else:
        print(f"   ❌ {chave} -> {tipo}")

    # Caso 3: Mensagem interativa
    print("3. Processando mensagem com botões:")
    chave = 'buttonsMessage'
    tipo = TipoMensagem.obter_por_chave_json(chave)
    if tipo == TipoMensagem.BOTAO:
        print(f"   ✅ {chave} -> {tipo.name}")
    else:
        print(f"   ❌ {chave} -> {tipo}")

    # Caso 4: Novo tipo - Status
    print("4. Processando mensagem de status:")
    chave = 'statusMessage'
    tipo = TipoMensagem.obter_por_chave_json(chave)
    if tipo == TipoMensagem.STATUS:
        print(f"   ✅ {chave} -> {tipo.name}")
    else:
        print(f"   ❌ {chave} -> {tipo}")

    print()


if __name__ == "__main__":
    print("TESTE DE CONFORMIDADE DO TIPOMENSAGEM\n")
    print("=" * 50)

    resultado_conformidade = testar_conformidade_com_tabela()
    testar_casos_uso()

    print("=" * 50)
    if resultado_conformidade:
        print("✅ TODOS OS TESTES PASSARAM!")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
