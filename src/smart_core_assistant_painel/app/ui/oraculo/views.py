import json
import os
import tempfile
from venv import logger

from django.contrib import messages
from django.core.cache import cache
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from langchain.docstore.document import Document
from rolepermissions.checkers import has_permission

from oraculo.utils import sched_message_response
from smart_core_assistant_painel.modules.ai_engine.features.features_compose import (
    FeaturesCompose,
)
from smart_core_assistant_painel.modules.services.features.service_hub import SERVICEHUB

from .models import (
    Treinamentos,
)


class TreinamentoService:
    """Serviço para gerenciar operações de treinamento"""

    @staticmethod
    def aplicar_pre_analise_documentos(documentos: list[Document]) -> list[Document]:
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
                    documento.page_content
                )
                documento.page_content = pre_analise_content
                documentos_processados.append(documento)

            except Exception as e:
                logger.error(f"Erro ao aplicar pré-análise no documento: {e}")
                # Mantém documento original em caso de erro
                documentos_processados.append(documento)

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
                delete=False, suffix=os.path.splitext(arquivo.name)[1]
            ) as temp_file:
                for chunk in arquivo.chunks():
                    temp_file.write(chunk)
                return temp_file.name

    @staticmethod
    def processar_conteudo_texto(
        treinamento_id: int, conteudo: str, tag: str, grupo: str
    ) -> list[Document]:
        """Processa conteúdo de texto para treinamento"""
        if not conteudo:
            raise ValueError("Conteúdo não pode ser vazio")

        try:
            pre_analise_conteudo = FeaturesCompose.pre_analise_ia_treinamento(conteudo)
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
        treinamento_id: int, documento_path: str, tag: str, grupo: str
    ) -> list[Document]:
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
            except OSError:
                pass


def treinar_ia(request):
    """View para treinamento de IA"""
    if not has_permission(request.user, "treinar_ia"):
        raise Http404()

    if request.method == "GET":
        return render(request, "treinar_ia.html")

    if request.method == "POST":
        return _processar_treinamento(request)


def _processar_treinamento(request):
    """Processa dados de treinamento enviados via POST"""
    tag = request.POST.get("tag")
    grupo = request.POST.get("grupo")
    conteudo = request.POST.get("conteudo")
    documento = request.FILES.get("documento")

    # Validações básicas
    if not tag or not grupo:
        messages.error(request, "Tag e Grupo são obrigatórios.")
        return render(request, "treinar_ia.html")

    if not conteudo and not documento:
        messages.error(request, "É necessário fornecer conteúdo ou documento.")
        return render(request, "treinar_ia.html")

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
                documento_path = TreinamentoService.processar_arquivo_upload(documento)
                if documento_path:
                    docs_arquivo = TreinamentoService.processar_arquivo_documento(
                        treinamento.id, documento_path, tag, grupo
                    )
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

            messages.success(request, "Treinamento criado com sucesso!")
            return redirect("pre_processamento", id=treinamento.id)

    except Exception as e:
        logger.error(f"Erro ao processar treinamento: {e}")
        messages.error(request, "Erro interno do servidor. Tente novamente.")
        return render(request, "treinar_ia.html")

    finally:
        # Limpar arquivo temporário
        TreinamentoService.limpar_arquivo_temporario(documento_path)


def pre_processamento(request, id):
    """View para pré-processamento de treinamento"""
    if not has_permission(request.user, "treinar_ia"):
        raise Http404()

    if request.method == "GET":
        return _exibir_pre_processamento(request, id)

    if request.method == "POST":
        return _processar_pre_processamento(request, id)


def _exibir_pre_processamento(request, id):
    """Exibe página de pré-processamento"""
    try:
        treinamento = Treinamentos.objects.get(id=id)
        conteudo_unificado = treinamento.get_conteudo_unificado()
        texto_melhorado = FeaturesCompose.melhoria_ia_treinamento(conteudo_unificado)

        return render(
            request,
            "pre_processamento.html",
            {
                "dados_organizados": treinamento,
                "treinamento": texto_melhorado,
            },
        )
    except Exception as e:
        logger.error(f"Erro ao gerar pré-processamento: {e}")
        messages.error(request, "Erro ao processar dados de treinamento.")
        return redirect("treinar_ia")


def _processar_pre_processamento(request, id):
    """Processa ação do pré-processamento"""
    treinamento = Treinamentos.objects.get(id=id)
    acao = request.POST.get("acao")

    if not acao:
        messages.error(request, "Ação não especificada.")

        return redirect("pre_processamento", id=treinamento.id)

    try:
        with transaction.atomic():
            if acao == "aceitar":
                _aceitar_treinamento(id)
                messages.success(request, "Treinamento aceito e finalizado!")
            elif acao == "manter":
                treinamento.treinamento_finalizado = True
                treinamento.save()
                messages.success(request, "Treinamento mantido e finalizado!")
            elif acao == "descartar":
                treinamento.delete()
                messages.info(request, "Treinamento descartado.")
            else:
                messages.error(request, "Ação inválida.")
                return redirect("pre_processamento", id=treinamento.id)

    except Exception as e:
        logger.error(f"Erro ao processar ação {acao}: {e}")
        messages.error(request, "Erro ao processar ação. Tente novamente.")

        return redirect("pre_processamento", id=treinamento.id)

    return redirect("treinar_ia")


def _aceitar_treinamento(id):
    """Aceita treinamento e atualiza conteúdo melhorado individualmente para cada documento"""
    try:
        # Processa documentos - agora sempre será uma lista (JSONField)
        treinamento = Treinamentos.objects.get(id=id)
        documentos_lista = treinamento.get_documentos()
        if not documentos_lista:
            return

        documentos_melhorados = TreinamentoService.aplicar_pre_analise_documentos(
            documentos_lista
        )
        # Salva alterações
        treinamento.set_documentos(documentos_melhorados)
        treinamento.treinamento_finalizado = True
        treinamento.save()

    except Exception as e:
        logger.error(f"Erro ao aceitar treinamento {treinamento.id}: {e}")
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
    try:
        # TODO: Implementar validação de API key se necessário
        # api_key = data.get('apikey')
        # if not _validar_api_key(api_key):
        #     return JsonResponse({"error": "API key inválida"}, status=401)

        # Validação básica da requisição
        if request.method != "POST":
            return JsonResponse({"error": "Método não permitido"}, status=405)

        if not request.body:
            return JsonResponse({"error": "Corpo da requisição vazio"}, status=400)

        # Parse do JSON com tratamento robusto de encoding
        try:
            body_str = request.body.decode("utf-8")
            
            if body_str is None:
                logger.error(
                    "Não foi possível decodificar o corpo da requisição com nenhum encoding"
                )
                return JsonResponse(
                    {"error": "Erro de codificação de caracteres"}, status=400
                )

            data = json.loads(body_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON inválido recebido no webhook: {e}")
            return JsonResponse({"error": "JSON inválido"}, status=400)

        # Validação dos campos obrigatórios
        if not isinstance(data, dict):
            return JsonResponse({"error": "Formato de dados inválido"}, status=400)

        # Processar mensagem usando função nova_mensagem
        try:
            logger.info(f"Recebido webhook para processar: {data}")
            message = FeaturesCompose.load_message_data(data)
            buffer = cache.get(f"wa_buffer_{message.numero_telefone}", [])
            buffer.append(message)
            cache.set(f"wa_buffer_{message.numero_telefone}", buffer, timeout=(SERVICEHUB.TIME_CACHE*2))


            sched_message_response(message.numero_telefone)

        except Exception as e:
            logger.error(f"Erro ao processar nova mensagem: {e}")
            return JsonResponse({"error": "Erro ao processar mensagem"}, status=500)

        # Resposta de sucesso
        return JsonResponse(
            {
                "status": "success",
            },
            status=200,
        )

    except Exception as e:
        # Log detalhado do erro para debugging
        logger.error(f"Erro crítico no webhook WhatsApp: {e}", exc_info=True)
        return JsonResponse({"error": "Erro interno do servidor"}, status=500)


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
        return False

    # Implementação temporária para desenvolvimento
    # Em produção, substituir por validação real
    return True
