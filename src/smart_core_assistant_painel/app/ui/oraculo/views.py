import json
import os
import tempfile

from django.contrib import messages

# from django.core.cache import cache
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from langchain.docstore.document import Document
from loguru import logger
from rolepermissions.checkers import has_permission

from smart_core_assistant_painel.modules.ai_engine import FeaturesCompose

from .models import (
    Treinamentos,
)
from .models_departamento import Departamento
from .utils import sched_message_response, set_wa_buffer


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
        logger.error(f"Erro ao aceitar treinamento {id}: {e}")
        raise


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
                "treinamento": treinamento,
                "conteudo_unificado": conteudo_unificado,
                "texto_melhorado": texto_melhorado,
            },
        )

    except Treinamentos.DoesNotExist:
        messages.error(request, "Treinamento não encontrado.")
        return redirect("treinar_ia")

    except Exception as e:
        logger.error(f"Erro ao exibir pré-processamento: {e}")
        messages.error(request, "Erro interno do servidor. Tente novamente.")
        return redirect("treinar_ia")


@csrf_exempt
def webhook_whatsapp(request):
    """
    Endpoint para receber notificações de mensagens do WhatsApp via Evolution API.

    Este endpoint recebe mensagens enviados pelo Evolution API e processa
    de forma robusta com suporte a diferentes tipos de mensagem, tratamento
    de erros e integração com o sistema de análise semântica e atendimento.

    Request sample (parcial):
        {
          "apikey": "YOUR_API_KEY",
          "instance": "instance_01",
          "data": {
             "key": {
                 "remoteJid": "553199999999@s.whatsapp.net",
                 "fromMe": false,
                 "id": "ABCD1234"
             },
             "message": {
                 "conversation": "Olá, tudo bem?"
             },
             "messageType": "conversation",
             "pushName": "João Silva",
             "broadcast": false,
             "messageTimestamp": 1700000123
          }
        }

    Response sample:
        {
          "status": "success",
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
        # Validação básica da requisição
        if request.method != "POST":
            return JsonResponse({"error": "Método não permitido"}, status=405)

        if not request.body:
            return JsonResponse({"error": "Corpo da requisição vazio"}, status=400)

        # Parse do JSON com tratamento robusto de encoding
        try:
            body_str = request.body.decode("utf-8")
        except UnicodeDecodeError:
            try:
                body_str = request.body.decode("latin-1")
                logger.warning("Decodificação UTF-8 falhou, usando latin-1")
            except UnicodeDecodeError:
                body_str = request.body.decode("utf-8", errors="ignore")
                logger.warning("Decodificação com errors='ignore' aplicada")

        if body_str is None:
            logger.error(
                "Não foi possível decodificar o corpo da requisição com nenhum encoding"
            )
            return JsonResponse(
                {"error": "Erro de codificação de caracteres"}, status=400
            )

        data = json.loads(body_str)

        # Validação da API Key
        departamento = Departamento.validar_api_key(data)
        if not departamento:
            return JsonResponse({"error": "API key inválida ou inativa"}, status=401)

        # Validação dos campos obrigatórios
        if not isinstance(data, dict):
            return JsonResponse({"error": "Formato de dados inválido"}, status=400)

        # Processar mensagem usando função nova_mensagem
        try:
            logger.info(f"Recebido webhook: {data}")
            message = FeaturesCompose.load_message_data(data)

            # Adiciona a mensagem ao buffer
            set_wa_buffer(message)

            # Agenda o processamento consolidado (usa normalização internamente)
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
