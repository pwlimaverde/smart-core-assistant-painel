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

# Atualizando a importação do modelo Treinamento
from .models_treinamento import Treinamento
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
        # Verifica se está em modo de edição (dados na sessão)
        dados_edicao = request.session.get('treinamento_edicao')
        
        if dados_edicao:
            context = {
                'modo_edicao': True,
                'treinamento_id': dados_edicao['id'],
                'tag_inicial': dados_edicao['tag'],
                'grupo_inicial': dados_edicao['grupo'],
                'conteudo_inicial': dados_edicao['conteudo'],
            }
        else:
            context = {
                'modo_edicao': False,
                'treinamento_id': None,
                'tag_inicial': '',
                'grupo_inicial': '',
                'conteudo_inicial': '',
            }
        
        return render(request, "treinar_ia.html", context)
    
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
    treinamento_id = request.POST.get("treinamento_id")
    
    # Se não tem ID no POST, verifica se tem dados de edição na sessão
    if not treinamento_id:
        dados_edicao = request.session.get('treinamento_edicao')
        if dados_edicao:
            treinamento_id = dados_edicao['id']

    if not tag or not grupo:
        messages.error(request, "Tag e Grupo são obrigatórios.")
        return render(request, "treinar_ia.html")
    if not conteudo and not documento:
        messages.error(request, "É necessário fornecer conteúdo ou documento.")
        return render(request, "treinar_ia.html")

    documento_path = None
    try:
        with transaction.atomic():
            # Verifica se está editando um treinamento existente
            if treinamento_id:
                try:
                    treinamento = Treinamento.objects.get(id=treinamento_id)
                    # Atualiza os campos básicos
                    treinamento.tag = tag
                    treinamento.grupo = grupo
                    # LIMPA COMPLETAMENTE TODOS OS DADOS EXISTENTES
                    treinamento.clear_all_data()
                    messages.success(request, f"Treinamento ID {treinamento_id} editado com sucesso!")
                except Treinamento.DoesNotExist:
                    messages.error(request, "Treinamento não encontrado para edição.")
                    return render(request, "treinar_ia.html")
            else:
                # Cria novo treinamento
                treinamento = Treinamento.objects.create(tag=tag, grupo=grupo)
                messages.success(request, "Treinamento criado com sucesso!")
            
            # Processa conteúdo (tanto para criação quanto edição)
            conteudo_completo = ""
            
            if documento:
                documento_path = TreinamentoService.processar_arquivo_upload(documento)
                if documento_path:
                    docs_arquivo = TreinamentoService.processar_arquivo_documento(
                        treinamento.id, documento_path, tag, grupo
                    )
                    conteudo_completo += "\n\n".join([doc.page_content for doc in docs_arquivo])
                    
            if conteudo:
                if conteudo_completo:
                    conteudo_completo += "\n\n" + conteudo
                else:
                    conteudo_completo = conteudo
            
            # Processa o conteúdo completo em chunks
            if conteudo_completo.strip():
                treinamento.processar_conteudo_para_chunks(conteudo_completo)
            
            treinamento.save()
            
            # Limpa dados de edição da sessão se existirem
            if 'treinamento_edicao' in request.session:
                del request.session['treinamento_edicao']
            
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
        treinamento = Treinamento.objects.get(id=id)
    except Treinamento.DoesNotExist:
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
                # Gera embeddings para os documentos após finalizar o treinamento
                treinamento.vetorizar_documentos()
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
    """Aceita o treinamento aplicando melhorias de IA e finalizando.

    Args:
        id (int): O ID do treinamento.
    """
    try:
        treinamento = Treinamento.objects.get(id=id)
        
        # Obtém conteúdo unificado atual
        conteudo_atual = treinamento.conteudo or ""
        
        # Verificação segura se há conteúdo
        if not conteudo_atual.strip():
            logger.warning(f"Treinamento {id} não possui conteúdo para processar")
            return
            
        # Aplica melhoria de IA ao conteúdo unificado
        conteudo_melhorado = FeaturesCompose.melhoria_ia_treinamento(conteudo_atual)
        
        # Atualiza o conteúdo do treinamento
        treinamento.conteudo = conteudo_melhorado
        treinamento.save(update_fields=['conteudo'])
        
        # Processa o conteúdo melhorado em chunks
        treinamento.processar_conteudo_para_chunks(conteudo_melhorado)
        
        # Finaliza o treinamento
        treinamento.treinamento_finalizado = True
        treinamento.save()
        
        # Gera embeddings para os documentos após finalizar o treinamento
        treinamento.vetorizar_documentos()
        
        logger.info(f"Treinamento {id} aceito e finalizado com melhorias aplicadas")
        
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
        treinamento = Treinamento.objects.get(id=id)
        conteudo_unificado = treinamento.conteudo or ""
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
    except Treinamento.DoesNotExist:
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


def verificar_treinamentos_vetorizados(request: HttpRequest) -> HttpResponse:
    """View para verificar treinamentos vetorizados com sucesso e com erro.

    Args:
        request (HttpRequest): O objeto de requisição.

    Returns:
        HttpResponse: A resposta HTTP.
    """
    if not has_permission(request.user, "treinar_ia"):
        raise Http404()
    
    if request.method == "POST":
        acao = request.POST.get("acao")
        treinamento_id = request.POST.get("treinamento_id")
        
        if not acao or not treinamento_id:
            messages.error(request, "Ação ou ID do treinamento não especificado.")
            return redirect("oraculo:verificar_treinamentos_vetorizados")
            
        try:
            treinamento = Treinamento.objects.get(id=treinamento_id)
            
            if acao == "excluir":
                treinamento.delete()
                messages.success(request, "Treinamento excluído com sucesso!")
            elif acao == "editar":
                # Armazena os dados do treinamento na sessão para edição
                conteudo_atual = treinamento.conteudo or ""
                
                # Armazena na sessão para evitar URLs extensas
                request.session['treinamento_edicao'] = {
                    'id': treinamento.id,
                    'tag': treinamento.tag,
                    'grupo': treinamento.grupo,
                    'conteudo': conteudo_atual
                }
                
                messages.info(request, f"Editando treinamento ID: {treinamento.id}")
                return redirect('oraculo:treinar_ia')
            else:
                messages.error(request, "Ação inválida.")
        except Treinamento.DoesNotExist:
            messages.error(request, "Treinamento não encontrado.")
        except Exception as e:
            logger.error(f"Erro ao processar ação {acao} no treinamento {treinamento_id}: {e}")
            messages.error(request, "Erro ao processar ação. Tente novamente.")
        
        return redirect("oraculo:verificar_treinamentos_vetorizados")
    
    # GET request - exibir lista de treinamentos
    treinamentos_vetorizados = Treinamento.objects.filter(
        treinamento_finalizado=True,
        treinamento_vetorizado=True
    ).order_by("-data_criacao")
    
    treinamentos_com_erro = Treinamento.objects.filter(
        treinamento_finalizado=True,
        treinamento_vetorizado=False
    ).order_by("-data_criacao")
    
    return render(request, "verificar_treinamentos.html", {
        "treinamentos_vetorizados": treinamentos_vetorizados,
        "treinamentos_com_erro": treinamentos_com_erro,
    })
