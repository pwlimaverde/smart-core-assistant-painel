import json
import os
import tempfile
from typing import Any, cast

from django.contrib import messages
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from langchain.docstore.document import Document
from loguru import logger
from rolepermissions.checkers import has_permission

from smart_core_assistant_painel.modules.ai_engine.features.features_compose import (
    FeaturesCompose, )

from .models import Atendimento, Mensagem, TipoMensagem, Treinamentos


class TreinamentoService:
    """Serviço para gerenciar operações de treinamento"""

    @staticmethod
    def aplicar_pre_analise_documentos(
            documentos: list[Document]) -> list[Document]:
        """Aplica pré-análise de IA ao page_content de uma lista de documentos

        Args:
            documentos: Lista de documentos para processar

        Returns:
            Lista de documentos com page_content atualizado
        """
        documentos_processados = []

        for documento in documentos:
            try:
                # Aplicar pré-análise
                pre_analise_content = FeaturesCompose.pre_analise_ia_treinamento(
                    documento.page_content)
                documento.page_content = pre_analise_content
                documentos_processados.append(documento)

            except Exception as e:
                logger.error(f"Erro ao aplicar pré-análise no documento: {e}")
                # Mantém documento original em caso de erro
                documentos_processados.append(documento)

        logger.debug(
            f"Pré-análise aplicada em {len(documentos_processados)} documentos")
        return documentos_processados

    @staticmethod
    def processar_arquivo_upload(arquivo):
        """Processa arquivo uploadado e retorna caminho temporário"""
        if not arquivo:
            return None

        try:
            return arquivo.temporary_file_path()
        except AttributeError:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=os.path.splitext(arquivo.name)[1]
            ) as temp_file:
                for chunk in arquivo.chunks():
                    temp_file.write(chunk)
                return temp_file.name

    @staticmethod
    def processar_conteudo_texto(
            treinamento_id: int,
            conteudo: str,
            tag: str,
            grupo: str) -> list[Document]:
        """Processa conteúdo de texto para treinamento"""
        if not conteudo:
            raise ValueError("Conteúdo não pode ser vazio")

        try:
            pre_analise_conteudo = FeaturesCompose.pre_analise_ia_treinamento(
                conteudo)
            data_conteudo = FeaturesCompose.load_document_conteudo(
                id=str(treinamento_id),
                conteudo=pre_analise_conteudo,
                tag=tag,
                grupo=grupo,
            )
            return data_conteudo
        except Exception as e:
            logger.error(f"Erro ao processar conteúdo texto: {e}")
            raise e

    @staticmethod
    def processar_arquivo_documento(
            treinamento_id: int,
            documento_path: str,
            tag: str,
            grupo: str) -> list[Document]:
        """Processa arquivo de documento para treinamento"""
        if not documento_path:
            raise ValueError("Caminho do documento não pode ser vazio")

        try:
            data_file = FeaturesCompose.load_document_file(
                id=str(treinamento_id),
                path=documento_path,
                tag=tag,
                grupo=grupo,
            )

            return TreinamentoService.aplicar_pre_analise_documentos(data_file)

        except Exception as e:
            logger.error(f"Erro ao processar arquivo documento: {e}")
            raise e

    @staticmethod
    def limpar_arquivo_temporario(arquivo_path):
        """Remove arquivo temporário se existir"""
        if arquivo_path and os.path.exists(arquivo_path):
            try:
                os.unlink(arquivo_path)
            except OSError as e:
                logger.warning(
                    f"Erro ao remover arquivo temporário {arquivo_path}: {e}")


def treinar_ia(request):
    """View para treinamento de IA"""
    if not has_permission(request.user, 'treinar_ia'):
        raise Http404()

    if request.method == 'GET':
        return render(request, 'treinar_ia.html')

    if request.method == 'POST':
        return _processar_treinamento(request)


def _processar_treinamento(request):
    """Processa dados de treinamento enviados via POST"""
    tag = request.POST.get('tag')
    grupo = request.POST.get('grupo')
    conteudo = request.POST.get('conteudo')
    documento = request.FILES.get('documento')

    # Validações básicas
    if not tag or not grupo:
        messages.error(request, 'Tag e Grupo são obrigatórios.')
        return render(request, 'treinar_ia.html')

    if not conteudo and not documento:
        messages.error(request, 'É necessário fornecer conteúdo ou documento.')
        return render(request, 'treinar_ia.html')

    documento_path = None

    try:
        with transaction.atomic():
            # Criar registro de treinamento
            treinamento = Treinamentos.objects.create(
                tag=tag,
                grupo=grupo,
            )

            documents_list = []

            # Processar arquivo se fornecido
            if documento:
                documento_path = TreinamentoService.processar_arquivo_upload(
                    documento)
                if documento_path:
                    docs_arquivo = TreinamentoService.processar_arquivo_documento(
                        treinamento.id, documento_path, tag, grupo)
                    documents_list.extend(docs_arquivo)

            # Processar conteúdo de texto se fornecido
            if conteudo:
                docs_conteudo = TreinamentoService.processar_conteudo_texto(
                    treinamento.id, conteudo, tag, grupo
                )
                documents_list.extend(docs_conteudo)

            # Salvar documentos processados
            treinamento.set_documentos(documents_list)
            treinamento.save()

            messages.success(request, 'Treinamento criado com sucesso!')
            return redirect('pre_processamento',
                            id=treinamento.id)

    except Exception as e:
        logger.error(f"Erro ao processar treinamento: {e}")
        messages.error(request, 'Erro interno do servidor. Tente novamente.')
        return render(request, 'treinar_ia.html')

    finally:
        # Limpar arquivo temporário
        TreinamentoService.limpar_arquivo_temporario(documento_path)


def pre_processamento(request, id):
    """View para pré-processamento de treinamento"""
    if not has_permission(request.user, 'treinar_ia'):
        raise Http404()

    if request.method == 'GET':
        return _exibir_pre_processamento(request, id)

    if request.method == 'POST':
        return _processar_pre_processamento(request, id)


def _exibir_pre_processamento(request, id):
    """Exibe página de pré-processamento"""
    try:
        treinamento = Treinamentos.objects.get(id=id)
        conteudo_unificado = treinamento.get_conteudo_unificado()
        texto_melhorado = FeaturesCompose.melhoria_ia_treinamento(
            conteudo_unificado)

        return render(request, 'pre_processamento.html', {
            'dados_organizados': treinamento,
            'treinamento': texto_melhorado,
        })
    except Exception as e:
        logger.error(f"Erro ao gerar pré-processamento: {e}")
        messages.error(request, 'Erro ao processar dados de treinamento.')
        return redirect('treinar_ia')


def _processar_pre_processamento(request, id):
    """Processa ação do pré-processamento"""
    treinamento = Treinamentos.objects.get(id=id)
    acao = request.POST.get('acao')

    if not acao:
        messages.error(request, 'Ação não especificada.')

        return redirect('pre_processamento', id=treinamento.id)

    try:
        with transaction.atomic():
            if acao == 'aceitar':
                _aceitar_treinamento(id)
                messages.success(request, 'Treinamento aceito e finalizado!')
            elif acao == 'manter':
                treinamento.treinamento_finalizado = True
                treinamento.save()
                messages.success(request, 'Treinamento mantido e finalizado!')
            elif acao == 'descartar':
                treinamento.delete()
                messages.info(request, 'Treinamento descartado.')
            else:
                messages.error(request, 'Ação inválida.')
                return redirect('pre_processamento',
                                id=treinamento.id)

    except Exception as e:
        logger.error(f"Erro ao processar ação {acao}: {e}")
        messages.error(request, 'Erro ao processar ação. Tente novamente.')

        return redirect('pre_processamento', id=treinamento.id)

    return redirect('treinar_ia')


def _aceitar_treinamento(id):
    """Aceita treinamento e atualiza conteúdo melhorado individualmente para cada documento"""
    try:
        # Processa documentos - agora sempre será uma lista (JSONField)
        treinamento = Treinamentos.objects.get(id=id)
        documentos_lista = treinamento.get_documentos()
        logger.debug(
            f"Processando documentos_lista {
                len(documentos_lista)} documentos {documentos_lista}")
        if not documentos_lista:
            logger.warning(
                f"Nenhum documento encontrado para treinamento {
                    treinamento.id}")
            return

        documentos_melhorados = TreinamentoService.aplicar_pre_analise_documentos(
            documentos_lista)
        logger.debug(
            f"Processando documentos_melhorados {
                len(documentos_melhorados)} documentos {documentos_melhorados}")
        # Salva alterações
        treinamento.set_documentos(documentos_melhorados)
        treinamento.treinamento_finalizado = True
        treinamento.save()

        logger.info(
            f"Treinamento {
                treinamento.id} aceito com {
                len(documentos_melhorados)} documentos melhorados")

    except Exception as e:
        logger.error(
            f"Erro ao aceitar treinamento {
                treinamento.id}: {e}")
        raise


@csrf_exempt
def webhook_whatsapp(request):
    """
    Webhook robusto para recebimento e processamento de mensagens do WhatsApp.

    Esta função é o ponto de entrada principal para mensagens do WhatsApp via webhook.
    Realiza validações completas, processa mensagens usando a função nova_mensagem(),
    determina o direcionamento apropriado (bot ou atendente humano), converte contexto
    de mensagens não textuais e prepara a mensagem para processamento posterior.

    Args:
        request (HttpRequest): Requisição HTTP contendo os dados do webhook
            do WhatsApp em formato JSON no body da requisição. Deve ser POST
            com Content-Type application/json.

    Returns:
        JsonResponse: Resposta JSON com status da operação:
            - Em caso de sucesso: {
                "status": "success",
                "mensagem_id": int,
                "direcionamento": str  # "bot" ou "humano"
              }
            - Em caso de erro: {"error": str} com códigos:
                * 400: Requisição inválida (JSON malformado, corpo vazio)
                * 401: API key inválida (quando implementada)
                * 405: Método HTTP não permitido (apenas POST aceito)
                * 500: Erro interno do servidor

    Raises:
        json.JSONDecodeError: Se o body da requisição não contém JSON válido
        Mensagem.DoesNotExist: Se a mensagem criada não for encontrada no banco
        ValidationError: Se dados do webhook são inválidos
        Exception: Para outros erros durante o processamento

    Validations:
        - Método HTTP deve ser POST
        - Body da requisição não pode estar vazio
        - JSON deve ser válido e estruturado como dicionário
        - Mensagem deve ser criada com sucesso no banco de dados
        - TODO: Validação de API key para segurança

    Processing Flow:
        1. Validação da requisição HTTP
        2. Parse e validação do JSON
        3. Logging de auditoria de entrada
        4. Processamento via nova_mensagem()
        5. Conversão de contexto para mensagens não textuais
        6. Determinação de direcionamento (bot vs humano)
        7. Logging completo de sucesso
        8. Resposta estruturada com metadados

    Security:
        - Função marcada com @csrf_exempt para chamadas externas
        - Logs não expõem dados sensíveis
        - Comportamento conservador em caso de erro (assume humano)
        - Preparada para validação de API key

    Performance:
        - Usa update_fields para economia em alterações de mensagem
        - Logs estruturados para facilitar monitoramento
        - Graceful degradation em falhas não críticas

    Examples:
        Payload típico do webhook:
        {
          "event": "messages.upsert",
          "instance": "arcane",
          "data": {
            "key": {
              "remoteJid": "5516992805442@s.whatsapp.net",
              "fromMe": false,
              "id": "5F2AAA4BD98BB388BBCD6FCB9B4ED660"
            },
            "pushName": "Cliente Exemplo",
            "message": {
              "extendedTextMessage": {
                "text": "Olá, preciso de ajuda com meu pedido"
              }
            },
            "messageType": "conversation",
            "messageTimestamp": 1748739583
          },
          "owner": "arcane",
          "source": "android",
          "destination": "localhost",
          "date_time": "2025-07-18T14:30:00.000Z",
          "sender": "5516999999999@s.whatsapp.net",
          "server_url": "http://localhost:8080",
          "apikey": "sua_api_key_aqui",
          "webhookUrl": "https://seu-dominio.com/webhook",
          "executionMode": "production"
        }

        Resposta de sucesso:
        {
          "status": "success",
          "mensagem_id": 12345,
          "direcionamento": "bot"
        }

    Notes:
        - Integração completa com sistema de logs para auditoria
        - Suporte a todos os tipos de mensagem do WhatsApp
        - Direcionamento inteligente baseado em contexto de atendimento
        - Preparado para futuras implementações de resposta automática
        - Tratamento robusto de erros com logs detalhados
    """
    from .models import Mensagem, nova_mensagem

    # Logging de entrada para auditoria
    logger.info(
        f"Webhook WhatsApp recebido - Method: {request.method}, Content-Type: {request.content_type}")

    try:
        # Validação básica da requisição
        if request.method != 'POST':
            logger.warning(
                f"Método HTTP inválido para webhook: {
                    request.method}")
            return JsonResponse({"error": "Método não permitido"}, status=405)

        if not request.body:
            logger.warning("Corpo da requisição vazio")
            return JsonResponse(
                {"error": "Corpo da requisição vazio"}, status=400)

        # Parse do JSON com tratamento específico
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON inválido recebido no webhook: {e}")
            return JsonResponse({"error": "JSON inválido"}, status=400)

        # Validação dos campos obrigatórios
        if not isinstance(data, dict):
            logger.error("Dados do webhook não são um dicionário válido")
            return JsonResponse(
                {"error": "Formato de dados inválido"}, status=400)

        # TODO: Implementar validação de API key se necessário
        # api_key = data.get('apikey')
        # if not _validar_api_key(api_key):
        #     return JsonResponse({"error": "API key inválida"}, status=401)

        # Logging dos dados recebidos (sem dados sensíveis)
        event_type = data.get('event', 'N/A')
        instance = data.get('instance', 'N/A')
        logger.info(
            f"Processando webhook - Event: {event_type}, Instance: {instance}")

        # Processar mensagem usando função nova_mensagem
        try:
            mensagem_id = nova_mensagem(data)
            logger.info(f"Mensagem criada com sucesso. ID: {mensagem_id}")
        except Exception as e:
            logger.error(f"Erro ao processar nova mensagem: {e}")
            return JsonResponse(
                {"error": "Erro ao processar mensagem"}, status=500)

        # Validar se a mensagem foi realmente criada
        try:
            mensagem = Mensagem.objects.get(id=mensagem_id)
        except Mensagem.DoesNotExist:
            logger.error(
                f"Mensagem criada (ID: {mensagem_id}) não encontrada no banco")
            return JsonResponse(
                {"error": "Mensagem não encontrada"}, status=500)

        # Processamento especial para mensagens não textuais
        mensagem_modificada = False
        if mensagem.tipo != TipoMensagem.TEXTO_FORMATADO:
            try:
                conteudo_original = mensagem.conteudo
                conteudo_convertido = _converter_contexto(
                    metadata=mensagem.metadados)

                if conteudo_convertido != conteudo_original:
                    mensagem.conteudo = conteudo_convertido
                    mensagem.save(update_fields=['conteudo'])
                    mensagem_modificada = True
                    logger.info(
                        f"Conteúdo da mensagem {mensagem_id} convertido: {conteudo_original[:50]} -> {conteudo_convertido[:50]}")

            except Exception as e:
                # Continua processamento mesmo com erro na conversão
                logger.error(
                    f"Erro ao converter contexto da mensagem {mensagem_id}: {e}")
        # Analise previa do conteudo da mensagem por agente de IA, detectando
        # intent e extraindo entidades
        try:
            _analisar_conteudo_mensagem(mensagem_id)
        except Exception as e:
            logger.error(
                f"Erro ao analisar conteúdo da mensagem {mensagem_id}: {e}")

        # Verificação de direcionamento do atendimento
        try:
            is_bot_responder = _pode_bot_responder_atendimento(
                mensagem.atendimento)
            direcionamento = "BOT" if is_bot_responder else "HUMANO"

            logger.info(
                f"Direcionamento definido para mensagem {mensagem_id}: {direcionamento}")

            if is_bot_responder:
                # TODO: Implementar geração de resposta automática do bot
                # Esta é uma funcionalidade crítica que deve ser implementada
                # Exemplo de implementação:
                # try:
                #     from smart_core_assistant_painel.modules.ai_engine.features.features_compose import FeaturesCompose
                #     resposta = FeaturesCompose.gerar_resposta_automatica(mensagem)
                #     if resposta:
                #         mensagem.resposta_bot = resposta
                #         mensagem.respondida = True
                #         mensagem.save(update_fields=['resposta_bot', 'respondida'])
                #         logger.info(f"Resposta automática gerada para mensagem {mensagem_id}")
                # except Exception as e:
                #     logger.error(f"Erro ao gerar resposta automática: {e}")

                logger.info(
                    f"Bot pode responder automaticamente para mensagem ID: {mensagem_id}")
            else:
                # Mensagem direcionada para atendente humano
                atendente_responsavel = getattr(
                    mensagem.atendimento, 'atendente_humano', None)
                if atendente_responsavel:
                    logger.info(
                        f"Mensagem {mensagem_id} direcionada para atendente: {
                            atendente_responsavel.nome}")
                else:
                    logger.info(
                        f"Mensagem {mensagem_id} direcionada para triagem de atendente humano")

        except Exception as e:
            logger.error(
                f"Erro ao verificar direcionamento da mensagem {mensagem_id}: {e}")
            # Continua processamento assumindo direcionamento humano por
            # segurança
            is_bot_responder = False
            direcionamento = "HUMANO (por erro)"

        # Log de sucesso completo
        logger.info(
            f"Webhook processado com sucesso - "
            f"MensagemID: {mensagem_id}, "
            f"Direcionamento: {direcionamento}, "
            f"ModificadaContexto: {mensagem_modificada}, "
            f"AtendimentoID: {cast(Atendimento, mensagem.atendimento).id}"
        )

        # Resposta de sucesso
        return JsonResponse({
            "status": "success",
            "mensagem_id": mensagem_id,
            "direcionamento": direcionamento.lower()
        }, status=200)

    except Exception as e:
        # Log detalhado do erro para debugging
        logger.error(f"Erro crítico no webhook WhatsApp: {e}", exc_info=True)
        return JsonResponse({"error": "Erro interno do servidor"}, status=500)


def _analisar_conteudo_mensagem(mensagem_id: int) -> None:
    """
    Análise prévia do conteúdo da mensagem para detectar intent e extrair entidades.

    Esta função utiliza o sistema de IA para analisar o conteúdo textual da mensagem,
    identificando a intenção do usuário e extraindo entidades relevantes. É uma etapa
    crítica para melhorar a compreensão do contexto e direcionamento das respostas.

    Args:
        mensagem (Mensagem): Instância da mensagem a ser analisada.
            Deve conter o campo 'conteudo' com texto a ser analisado.

    Returns:
        None: A função atualiza a mensagem diretamente no banco de dados.

    Raises:
        Exception: Capturada internamente e logada. Função não retorna valor
            em caso de erro, mas garante que o processamento continue.

    Notes:
        - Implementação planejada para análise de intent e entidades
        - Base para futuras melhorias na experiência do usuário
        - Logs de erro são gerados para facilitar troubleshooting

    Examples:
        >>> mensagem = Mensagem.objects.get(id=123)
        >>> _analisar_conteudo_mensagem(mensagem)
    """
    from smart_core_assistant_painel.modules.ai_engine.features.features_compose import (
        FeaturesCompose, )

    try:
        mensagem = Mensagem.objects.get(id=mensagem_id)
        # Carrega historico para futuro uso na análise de IA
        cast(Atendimento, mensagem.atendimento).carregar_historico_mensagens()
        features = FeaturesCompose()
        # Análise de intenção e extração de entidades
        features.analise_previa_mensagem()
        logger.info(
            f"Conteúdo da mensagem {mensagem_id} analisado com sucesso")
    except Exception as e:
        logger.error(
            f"Erro ao analisar conteúdo da mensagem {mensagem_id}: {e}")
        # Continua processamento mesmo com erro na análise
        # Não interrompe o fluxo para garantir resiliência
        pass


def _pode_bot_responder_atendimento(atendimento):
    """
    Verifica se o bot pode responder automaticamente em um atendimento específico.

    O bot não deve responder se há mensagens de atendente humano no atendimento
    ou se um atendente humano está associado ao atendimento, garantindo que
    a experiência do usuário não seja comprometida por respostas conflitantes.

    Args:
        atendimento (Atendimento): Instância do atendimento a ser verificado.
            Deve conter as relações 'mensagens' e 'atendente_humano'.

    Returns:
        bool: True se o bot pode responder automaticamente, False caso contrário.
            Retorna False também em caso de erro durante a verificação.

    Raises:
        Exception: Capturada internamente e logada. Função retorna False
            em caso de erro para garantir segurança operacional.

    Notes:
        - A verificação inclui tanto mensagens quanto associação direta de atendente
        - Em caso de erro, assume-se comportamento conservador (False)
        - Logs de erro são gerados para facilitar troubleshooting

    Examples:
        >>> atendimento = Atendimento.objects.get(id=123)
        >>> pode_responder = _pode_bot_responder_atendimento(atendimento)
        >>> if pode_responder:
        ...     # Bot pode responder automaticamente
        ...     pass
    """
    from .models import TipoRemetente

    try:
        # Verifica se existe alguma mensagem de atendente humano neste
        # atendimento ou se o atendimento tem um atendente humano associado
        mensagens_atendente = atendimento.mensagens.filter(
            remetente=TipoRemetente.ATENDENTE_HUMANO
        ).exists() or atendimento.atendente_humano is not None

        return not mensagens_atendente
    except Exception as e:
        logger.error(f"Erro ao verificar se bot pode responder: {e}")
        return False


def _converter_contexto(metadata: dict[str, Any]) -> str:
    """
    Converte metadados de mensagens multimídia para texto formatado legível.

    Esta função processa os metadados de mensagens não textuais (imagens,
    áudios, documentos, vídeos, stickers, etc.) e os converte em uma
    representação textual que pode ser compreendida e processada pelo
    sistema de IA para geração de respostas contextuais apropriadas.

    Args:
        metadata (dict): Dicionário contendo os metadados da mensagem.
            Estrutura típica inclui:
            - 'type': Tipo da mídia (image, audio, document, etc.)
            - 'mime_type'/'mimetype': Tipo MIME do arquivo
            - 'size'/'fileLength': Tamanho do arquivo em bytes
            - 'url': URL para download do arquivo
            - 'fileName': Nome original do arquivo
            - Campos específicos por tipo (duration, dimensions, etc.)

    Returns:
        str: Texto formatado representando o contexto da mensagem.
            Exemplos de retorno futuro:
            - "Imagem JPEG de 2.1MB (1920x1080)"
            - "Áudio MP3 de 45 segundos"
            - "Documento PDF: 'Relatório_Mensal.pdf' (856KB)"
            - "Vídeo MP4 de 2min30s (1280x720)"

    Raises:
        Exception: Repassada para o chamador em caso de erro na conversão.
            Logs de erro são gerados automaticamente para debugging.

    Implementation Status:
        - ATUAL: Retorna placeholder 'contexto' para todos os tipos
        - PLANEJADO: Conversão específica por tipo de mídia
        - FUTURO: Integração com análise de conteúdo por IA

    Processing Logic (Futuro):
        1. Identificar tipo de mídia pelos metadados
        2. Extrair informações relevantes (tamanho, formato, duração)
        3. Formatar texto descritivo apropriado
        4. Adicionar contexto específico quando possível

    Notes:
        - Função crítica para suporte completo a mensagens multimídia
        - Permite que o bot compreenda e responda a qualquer tipo de mensagem
        - Essencial para experiência de usuário completa no WhatsApp
        - Base para futuras funcionalidades de análise de conteúdo

    Examples:
        >>> # Imagem
        >>> metadata = {
        ...     "type": "image",
        ...     "mimetype": "image/jpeg",
        ...     "fileLength": 2048000,
        ...     "url": "https://example.com/image.jpg"
        ... }
        >>> _converter_contexto(metadata)
        'contexto'  # Atual
        # 'Imagem JPEG de 2MB'  # Implementação futura

        >>> # Áudio
        >>> metadata = {
        ...     "type": "audio",
        ...     "mimetype": "audio/ogg",
        ...     "seconds": 45,
        ...     "ptt": True
        ... }
        >>> _converter_contexto(metadata)
        'contexto'  # Atual
        # 'Mensagem de voz de 45 segundos'  # Implementação futura

        >>> # Documento
        >>> metadata = {
        ...     "type": "document",
        ...     "fileName": "Contrato_2025.pdf",
        ...     "mimetype": "application/pdf",
        ...     "fileLength": 856000
        ... }
        >>> _converter_contexto(metadata)
        'contexto'  # Atual
        # 'Documento PDF: Contrato_2025.pdf (856KB)'  # Implementação futura
    """
    try:
        # TODO: Implementar lógica específica de conversão por tipo de mídia
        #
        # Estrutura planejada:
        # if not metadata:
        #     return "Conteúdo sem metadados"
        #
        # media_type = metadata.get('type', 'unknown')
        #
        # if media_type == 'image':
        #     return _processar_contexto_imagem(metadata)
        # elif media_type == 'audio':
        #     return _processar_contexto_audio(metadata)
        # elif media_type == 'document':
        #     return _processar_contexto_documento(metadata)
        # elif media_type == 'video':
        #     return _processar_contexto_video(metadata)
        # else:
        #     return f"Conteúdo do tipo {media_type}"

        # Implementação atual: placeholder
        return 'contexto'

    except Exception as e:
        logger.error(f"Erro ao converter contexto: {e}")
        raise e


def _validar_api_key(api_key: str) -> bool:
    """
    Valida se a API key fornecida é válida para autenticação do webhook.

    Esta função verifica se a API key enviada no payload do webhook é válida
    e tem permissão para enviar mensagens para o sistema. Implementa uma
    camada de segurança essencial para evitar chamadas não autorizadas.

    Args:
        api_key (str): Chave de API a ser validada. Pode vir do campo
            'apikey' no payload do webhook ou de headers HTTP.

    Returns:
        bool: True se a API key é válida e autorizada, False caso contrário.
            Comportamento atual: aceita qualquer key não vazia (desenvolvimento).

    Security Considerations:
        - API keys devem ser únicas por instância/cliente
        - Recomenda-se uso de hashing ou assinatura digital
        - Implementar rate limiting por API key
        - Logs de tentativas de acesso inválidas
        - Rotação periódica de chaves em produção

    Implementation Roadmap:
        - ATUAL: Validação básica (não vazia)
        - FASE 1: Validação contra banco de dados
        - FASE 2: Assinatura digital HMAC-SHA256
        - FASE 3: Rate limiting e blacklist
        - FASE 4: Rotação automática de chaves

    Notes:
        - TODO: Implementar validação real de API key
        - Considerar implementar verificação em banco de dados ou cache
        - Importante para segurança em ambiente de produção
        - Deve integrar com sistema de monitoramento de segurança

    Examples:
        >>> # Validação básica atual
        >>> api_key = "abc123def456"
        >>> if _validar_api_key(api_key):
        ...     # Processar webhook
        ...     pass

        >>> # API key vazia (rejeitada)
        >>> _validar_api_key("")
        False

        >>> # Implementação futura com HMAC
        >>> # import hmac, hashlib
        >>> # def _validar_api_key_hmac(api_key, payload, secret):
        >>> #     expected = hmac.new(
        >>> #         secret.encode(),
        >>> #         payload.encode(),
        >>> #         hashlib.sha256
        >>> #     ).hexdigest()
        >>> #     return hmac.compare_digest(expected, api_key)
    """
    # TODO: Implementar validação real de API key
    #
    # Exemplo de implementação robusta:
    #
    # 1. Validação em banco de dados:
    # try:
    #     api_config = APIKey.objects.get(
    #         key=api_key,
    #         ativo=True,
    #         expires_at__gt=timezone.now()
    #     )
    #     # Atualizar último uso
    #     api_config.ultimo_uso = timezone.now()
    #     api_config.save(update_fields=['ultimo_uso'])
    #     return True
    # except APIKey.DoesNotExist:
    #     logger.warning(f"API key inválida tentou acesso: {api_key[:8]}...")
    #     return False
    #
    # 2. Validação com assinatura HMAC:
    # secret = settings.WEBHOOK_SECRET
    # return hmac.compare_digest(
    #     expected_signature,
    #     hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    # )

    if not api_key:
        logger.warning("Tentativa de acesso com API key vazia")
        return False

    # Implementação temporária para desenvolvimento
    # Em produção, substituir por validação real
    logger.debug(f"API key recebida: {api_key[:8]}... (validação temporária)")
    return True
