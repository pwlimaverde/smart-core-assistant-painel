"""

Views para o aplicativo Treinamento.

"""

from django.contrib import messages
from django.db import transaction
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from loguru import logger
from rolepermissions.checkers import has_permission

from smart_core_assistant_painel.modules.ai_engine import FeaturesCompose

from .models import Documento, Treinamento
from .services import TreinamentoService


def treinar_ia(request: HttpRequest) -> HttpResponse:
    """View para o treinamento da IA."""
    if not has_permission(request.user, "treinar_ia"):
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("treinamento:treinar_ia")

    if request.method == "GET":
        dados_edicao = request.session.get("treinamento_edicao")

        if dados_edicao:
            context = {
                "modo_edicao": True,
                "treinamento_id": dados_edicao["id"],
                "tag_inicial": dados_edicao["tag"],
                "grupo_inicial": dados_edicao["grupo"],
                "conteudo_inicial": dados_edicao["conteudo"],
            }
        else:
            context = {
                "modo_edicao": False,
                "treinamento_id": None,
                "tag_inicial": "",
                "grupo_inicial": "",
                "conteudo_inicial": "",
            }

        return render(request, "treinamento/treinar_ia.html", context)

    if request.method == "POST":
        return _processar_treinamento(request)

    return render(request, "treinamento/treinar_ia.html")

def _processar_treinamento(request: HttpRequest) -> HttpResponse:
    """Processa os dados de treinamento enviados via POST."""
    tag = request.POST.get("tag")
    grupo = request.POST.get("grupo")
    conteudo = request.POST.get("conteudo")
    documento = request.FILES.get("documento")
    treinamento_id = request.POST.get("treinamento_id")

    if not treinamento_id:
        dados_edicao = request.session.get("treinamento_edicao")
        if dados_edicao:
            treinamento_id = dados_edicao["id"]

    if not tag or not grupo:
        messages.error(request, "Tag e Grupo são obrigatórios.")
        return render(request, "treinamento/treinar_ia.html")
    if not conteudo and not documento:
        messages.error(request, "É necessário fornecer conteúdo ou documento.")
        return render(request, "treinamento/treinar_ia.html")

    documento_path = None
    try:
        with transaction.atomic():
            if treinamento_id:
                try:
                    treinamento: Treinamento = Treinamento.objects.get(id=treinamento_id)
                    treinamento.tag = tag
                    treinamento.grupo = grupo
                    Documento.limpar_documentos_por_treinamento(treinamento.id)
                    messages.success(
                        request,
                        f"Treinamento ID {treinamento_id} editado com sucesso!",
                    )
                except Treinamento.DoesNotExist:
                    messages.error(request, "Treinamento não encontrado para edição.")
                    return render(request, "treinamento/treinar_ia.html")
            else:
                treinamento = Treinamento.objects.create(tag=tag, grupo=grupo)
                messages.success(request, "Treinamento criado com sucesso!")

            conteudo_completo = ""

            if documento:
                documento_path = TreinamentoService.processar_arquivo_upload(documento)
                if documento_path:
                    docs_arquivo = TreinamentoService.processar_arquivo_documento(
                        treinamento.id, documento_path, tag, grupo
                    )
                    conteudo_completo += "\n\n".join(
                        [doc.page_content for doc in docs_arquivo]
                    )

            if conteudo:
                if conteudo_completo:
                    conteudo_completo += "\n\n" + conteudo
                else:
                    conteudo_completo = conteudo

            if conteudo_completo:
                treinamento.conteudo = conteudo_completo

            treinamento.save()

            if "treinamento_edicao" in request.session:
                del request.session["treinamento_edicao"]

            messages.success(request, "Treinamento criado com sucesso!")
            return redirect("treinamento:pre_processamento", id=treinamento.id)
    except Exception as e:
        logger.error(f"Erro ao processar treinamento: {e}")
        messages.error(request, "Erro interno do servidor. Tente novamente.")
        return render(request, "treinamento/treinar_ia.html")
    finally:
        TreinamentoService.limpar_arquivo_temporario(documento_path)

def pre_processamento(request: HttpRequest, id: int) -> HttpResponse:
    """View para o pré-processamento do treinamento."""
    if not has_permission(request.user, "treinar_ia"):
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("treinamento:treinar_ia")
    if request.method == "GET":
        return _exibir_pre_processamento(request, id)
    if request.method == "POST":
        return _processar_pre_processamento(request, id)
    return redirect("treinamento:treinar_ia")

def _processar_pre_processamento(request: HttpRequest, id: int) -> HttpResponse:
    """Processa a ação do pré-processamento."""
    try:
        treinamento = Treinamento.objects.get(id=id)
    except Treinamento.DoesNotExist:
        messages.error(request, "Treinamento não encontrado.")
        return redirect("treinamento:treinar_ia")

    acao = request.POST.get("acao")
    if not acao:
        messages.error(request, "Ação não especificada.")
        return redirect("treinamento:pre_processamento", id=treinamento.id)
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
                return redirect("treinamento:pre_processamento", id=treinamento.id)
    except Exception as e:
        logger.error(f"Erro ao processar ação {acao}: {e}")
        messages.error(request, "Erro ao processar ação. Tente novamente.")
        return redirect("treinamento:pre_processamento", id=treinamento.id)
    return redirect("treinamento:treinar_ia")

def _aceitar_treinamento(id: int) -> None:
    """Aceita o treinamento aplicando melhorias de IA e finalizando."""
    try:
        treinamento = Treinamento.objects.get(id=id)
        conteudo_atual = treinamento.conteudo or ""
        if not conteudo_atual.strip():
            logger.warning(f"Treinamento {id} não possui conteúdo para processar")
            return

        conteudo_melhorado = FeaturesCompose.melhoria_ia_treinamento(conteudo_atual)
        treinamento.conteudo = conteudo_melhorado
        treinamento.save(update_fields=["conteudo"])
        treinamento.treinamento_finalizado = True
        treinamento.save()
        logger.info(f"Treinamento {id} aceito e finalizado com melhorias aplicadas")
    except Exception as e:
        logger.error(f"Erro ao aceitar treinamento {id}: {e}")
        raise

def _exibir_pre_processamento(request: HttpRequest, id: int) -> HttpResponse:
    """Exibe a página de pré-processamento."""
    try:
        treinamento = Treinamento.objects.get(id=id)
        conteudo_unificado = treinamento.conteudo or ""

        if not conteudo_unificado.strip():
            logger.warning(f"Treinamento {id} sem conteúdo para pré-processamento")
            messages.warning(
                request,
                "Treinamento sem conteúdo. Verifique se o conteúdo foi salvo corretamente.",
            )
            return redirect("treinamento:treinar_ia")

        texto_melhorado = FeaturesCompose.melhoria_ia_treinamento(conteudo_unificado)
        return render(
            request,
            "treinamento/pre_processamento.html",
            {
                "treinamento": treinamento,
                "conteudo_unificado": conteudo_unificado,
                "texto_melhorado": texto_melhorado,
            },
        )
    except Treinamento.DoesNotExist:
        messages.error(request, "Treinamento não encontrado.")
        return redirect("treinamento:treinar_ia")
    except Exception as e:
        logger.error(f"Erro ao exibir pré-processamento: {e}")
        messages.error(request, "Erro interno do servidor. Tente novamente.")
        return redirect("treinamento:treinar_ia")

def verificar_treinamentos_vetorizados(request: HttpRequest) -> HttpResponse:
    """View para verificar treinamentos vetorizados com sucesso e com erro."""
    if not has_permission(request.user, "treinar_ia"):
        raise Http404()

    if request.method == "POST":
        acao = request.POST.get("acao")
        treinamento_id = request.POST.get("treinamento_id")

        if not acao or not treinamento_id:
            messages.error(request, "Ação ou ID do treinamento não especificado.")
            return redirect("treinamento:verificar_treinamentos_vetorizados")

        try:
            treinamento = Treinamento.objects.get(id=treinamento_id)

            if acao == "excluir":
                treinamento.delete()
                messages.success(request, "Treinamento excluído com sucesso!")
            elif acao == "editar":
                conteudo_atual = treinamento.conteudo or ""
                request.session["treinamento_edicao"] = {
                    "id": treinamento.id,
                    "tag": treinamento.tag,
                    "grupo": treinamento.grupo,
                    "conteudo": conteudo_atual,
                }
                messages.info(request, f"Editando treinamento ID: {treinamento.id}")
                return redirect("treinamento:treinar_ia")
            else:
                messages.error(request, "Ação inválida.")
        except Treinamento.DoesNotExist:
            messages.error(request, "Treinamento não encontrado.")
        except Exception as e:
            logger.error(
                f"Erro ao processar ação {acao} no treinamento {treinamento_id}: {e}"
            )
            messages.error(request, "Erro ao processar ação. Tente novamente.")

        return redirect("treinamento:verificar_treinamentos_vetorizados")

    treinamentos_vetorizados = Treinamento.objects.filter(
        treinamento_finalizado=True, treinamento_vetorizado=True
    ).order_by("-data_criacao")

    treinamentos_com_erro = Treinamento.objects.filter(
        treinamento_finalizado=True, treinamento_vetorizado=False
    ).order_by("-data_criacao")

    return render(
        request,
        "treinamento/verificar_treinamentos.html",
        {
            "treinamentos_vetorizados": treinamentos_vetorizados,
            "treinamentos_com_erro": treinamentos_com_erro,
        },
    )