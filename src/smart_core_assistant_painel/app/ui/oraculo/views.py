"""Views para o aplicativo Oráculo.

Este módulo contém as views para o treinamento da IA, pré-processamento de
dados e o webhook para receber mensagens do WhatsApp.
"""

import json
import os
import tempfile

from django.contrib import messages
from django.db import transaction
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from langchain.docstore.document import Document
from loguru import logger
from rolepermissions.checkers import has_permission

from smart_core_assistant_painel.modules.ai_engine import FeaturesCompose

from .models import Treinamentos
from .models_departamento import Departamento
from .utils import sched_message_response, set_wa_buffer


class TreinamentoService:
    """Serviço para gerenciar operações de treinamento."""

    @staticmethod
    def aplicar_pre_analise_documentos(
        documentos: list[Document],
    ) -> list[Document]:
        """Aplica pré-análise de IA ao conteúdo de uma lista de documentos.

        Args:
            documentos (list[Document]): Lista de documentos a serem processados.

        Returns:
            list[Document]: Lista de documentos com o conteúdo atualizado.
        """
        documentos_processados = []
        for documento in documentos:
            try:
                pre_analise_content = FeaturesCompose.pre_analise_ia_treinamento(
                    documento.page_content
                )
                documento.page_content = pre_analise_content
                documentos_processados.append(documento)
            except Exception as e:
                logger.error(f"Erro ao aplicar pré-análise no documento: {e}")
                documentos_processados.append(documento)
        return documentos_processados

    @staticmethod
    def processar_arquivo_upload(arquivo):
        """Processa um arquivo enviado e retorna seu caminho temporário.

        Args:
            arquivo: O objeto de arquivo enviado.

        Returns:
            str | None: O caminho para o arquivo temporário ou None.
        """
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
        """Processa conteúdo de texto para treinamento.

        Args:
            treinamento_id (int): ID do registro de treinamento.
            conteudo (str): O texto a ser processado.
            tag (str): A tag para categorização.
            grupo (str): O grupo ao qual o conteúdo pertence.

        Returns:
            list[Document]: Uma lista de objetos Document.
        """
        if not conteudo:
            raise ValueError("Conteúdo não pode ser vazio")
        try:
            pre_analise_conteudo = FeaturesCompose.pre_analise_ia_treinamento(conteudo)
            return FeaturesCompose.load_document_conteudo(
                id=str(treinamento_id),
                conteudo=pre_analise_conteudo,
                tag=tag,
                grupo=grupo,
            )
        except Exception as e:
            logger.error(f"Erro ao processar conteúdo de texto: {e}")
            raise

    @staticmethod
    def processar_arquivo_documento(
        treinamento_id: int, documento_path: str, tag: str, grupo: str
    ) -> list[Document]:
        """Processa um arquivo de documento para treinamento.

        Args:
            treinamento_id (int): ID do registro de treinamento.
            documento_path (str): Caminho para o arquivo do documento.
            tag (str): A tag para categorização.
            grupo (str): O grupo ao qual o documento pertence.

        Returns:
            list[Document]: Uma lista de objetos Document.
        """
        if not documento_path:
            raise ValueError("Caminho do documento não pode ser vazio")
        try:
            data_file = FeaturesCompose.load_document_file(
                id=str(treinamento_id), path=documento_path, tag=tag, grupo=grupo
            )
            return TreinamentoService.aplicar_pre_analise_documentos(data_file)
        except Exception as e:
            logger.error(f"Erro ao processar arquivo de documento: {e}")
            raise

    @staticmethod
    def limpar_arquivo_temporario(arquivo_path):
        """Remove um arquivo temporário, se existir.

        Args:
            arquivo_path (str): O caminho para o arquivo temporário.
        """
        if arquivo_path and os.path.exists(arquivo_path):
            try:
                os.unlink(arquivo_path)
            except OSError:
                pass


def treinar_ia(request: HttpRequest) -> HttpResponse:
    """View para o treinamento da IA.

    Args:
        request (HttpRequest): O objeto de requisição.

    Returns:
        HttpResponse: A resposta HTTP.
    """
    if not has_permission(request.user, "treinar_ia"):
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("oraculo:treinar_ia")
    if request.method == "GET":
        return render(request, "treinar_ia.html")
    if request.method == "POST":
        return _processar_treinamento(request)
    return render(request, "treinar_ia.html")


def _processar_treinamento(request: HttpRequest) -> HttpResponse:
    """Processa os dados de treinamento enviados via POST.

    Args:
        request (HttpRequest): O objeto de requisição.

    Returns:
        HttpResponse: A resposta HTTP.
    """
    tag = request.POST.get("tag")
    grupo = request.POST.get("grupo")
    conteudo = request.POST.get("conteudo")
    documento = request.FILES.get("documento")

    if not tag or not grupo:
        messages.error(request, "Tag e Grupo são obrigatórios.")
        return render(request, "treinar_ia.html")
    if not conteudo and not documento:
        messages.error(request, "É necessário fornecer conteúdo ou documento.")
        return render(request, "treinar_ia.html")

    documento_path = None
    try:
        with transaction.atomic():
            treinamento = Treinamentos.objects.create(tag=tag, grupo=grupo)
            documents_list = []
            if documento:
                documento_path = TreinamentoService.processar_arquivo_upload(documento)
                if documento_path:
                    docs_arquivo = TreinamentoService.processar_arquivo_documento(
                        treinamento.id, documento_path, tag, grupo
                    )
                    documents_list.extend(docs_arquivo)
            if conteudo:
                docs_conteudo = TreinamentoService.processar_conteudo_texto(
                    treinamento.id, conteudo, tag, grupo
                )
                documents_list.extend(docs_conteudo)
            treinamento.set_documentos(documents_list)
            treinamento.save()
            messages.success(request, "Treinamento criado com sucesso!")
            return redirect("oraculo:pre_processamento", id=treinamento.id)
    except Exception as e:
        logger.error(f"Erro ao processar treinamento: {e}")
        messages.error(request, "Erro interno do servidor. Tente novamente.")
        return render(request, "treinar_ia.html")
    finally:
        TreinamentoService.limpar_arquivo_temporario(documento_path)


def pre_processamento(request: HttpRequest, id: int) -> HttpResponse:
    """View para o pré-processamento do treinamento.

    Args:
        request (HttpRequest): O objeto de requisição.
        id (int): O ID do treinamento.

    Returns:
        HttpResponse: A resposta HTTP.
    """
    if not has_permission(request.user, "treinar_ia"):
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("oraculo:treinar_ia")
    if request.method == "GET":
        return _exibir_pre_processamento(request, id)
    if request.method == "POST":
        return _processar_pre_processamento(request, id)
    return redirect("oraculo:treinar_ia")


def _processar_pre_processamento(request: HttpRequest, id: int) -> HttpResponse:
    """Processa a ação do pré-processamento.

    Args:
        request (HttpRequest): O objeto de requisição.
        id (int): O ID do treinamento.

    Returns:
        HttpResponse: A resposta HTTP.
    """
    try:
        treinamento = Treinamentos.objects.get(id=id)
    except Treinamentos.DoesNotExist:
        messages.error(request, "Treinamento não encontrado.")
        return redirect("oraculo:treinar_ia")
    
    acao = request.POST.get("acao")
    if not acao:
        messages.error(request, "Ação não especificada.")
        return redirect("oraculo:pre_processamento", id=treinamento.id)
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
                return redirect("oraculo:pre_processamento", id=treinamento.id)
    except Exception as e:
        logger.error(f"Erro ao processar ação {acao}: {e}")
        messages.error(request, "Erro ao processar ação. Tente novamente.")
        return redirect("oraculo:pre_processamento", id=treinamento.id)
    return redirect("oraculo:treinar_ia")


def _aceitar_treinamento(id: int):
    """Aceita o treinamento e atualiza o conteúdo de cada documento.

    Args:
        id (int): O ID do treinamento.
    """
    try:
        treinamento = Treinamentos.objects.get(id=id)
        documentos_lista = treinamento.get_documentos()
        if not documentos_lista:
            return
        documentos_melhorados = TreinamentoService.aplicar_pre_analise_documentos(
            documentos_lista
        )
        treinamento.set_documentos(documentos_melhorados)
        treinamento.treinamento_finalizado = True
        treinamento.save()
    except Exception as e:
        logger.error(f"Erro ao aceitar treinamento {id}: {e}")
        raise


def _exibir_pre_processamento(request: HttpRequest, id: int) -> HttpResponse:
    """Exibe a página de pré-processamento.

    Args:
        request (HttpRequest): O objeto de requisição.
        id (int): O ID do treinamento.

    Returns:
        HttpResponse: A resposta HTTP.
    """
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
        return redirect("oraculo:treinar_ia")
    except Exception as e:
        logger.error(f"Erro ao exibir pré-processamento: {e}")
        messages.error(request, "Erro interno do servidor. Tente novamente.")
        return redirect("oraculo:treinar_ia")


@csrf_exempt
def webhook_whatsapp(request: HttpRequest) -> JsonResponse:
    """Endpoint para receber notificações de mensagens do WhatsApp.

    Args:
        request (HttpRequest): O objeto de requisição.

    Returns:
        JsonResponse: A resposta JSON.
    """
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Método não permitido"}, status=405)
        if not request.body:
            return JsonResponse({"error": "Corpo da requisição vazio"}, status=400)
        try:
            body_str = request.body.decode("utf-8")
        except UnicodeDecodeError:
            body_str = request.body.decode("utf-8", errors="ignore")
            logger.warning("Decodificação com errors='ignore' aplicada")

        data = json.loads(body_str)
        departamento = Departamento.validar_api_key(data)
        if not departamento:
            return JsonResponse({"error": "API key inválida ou inativa"}, status=401)
        if not isinstance(data, dict):
            return JsonResponse({"error": "Formato de dados inválido"}, status=400)

        logger.info(f"Recebido webhook: {data}")
        message = FeaturesCompose.load_message_data(data)
        set_wa_buffer(message)
        sched_message_response(message.numero_telefone)

        return JsonResponse({"status": "success"}, status=200)
    except Exception as e:
        logger.error(f"Erro crítico no webhook WhatsApp: {e}", exc_info=True)
        return JsonResponse({"error": "Erro interno do servidor"}, status=500)
