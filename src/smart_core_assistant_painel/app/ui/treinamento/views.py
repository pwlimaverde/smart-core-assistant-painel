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

from .models import Documento, QueryCompose, Treinamento
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
                    treinamento.treinamento_finalizado = False
                    treinamento.treinamento_vetorizado = False
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


# NOVO: View para verificar e editar QueryCompose (intents)
def verificar_query_compose(request: HttpRequest) -> HttpResponse:
    """Lista intents (QueryCompose) com sucesso e com erro, permite editar/excluir.

    - Sucesso: registros com embedding preenchido.
    - Erro: registros sem embedding ("embedding" nulo).
    - Ação "editar": popula sessão e redireciona para a página de cadastro.
    - Ação "excluir": remove o registro.
    """
    if not has_permission(request.user, "treinar_ia"):
        raise Http404()

    if request.method == "POST":
        acao = request.POST.get("acao")
        qc_id = request.POST.get("query_compose_id")

        if not acao or not qc_id:
            messages.error(request, "Ação ou ID do intent não especificado.")
            return redirect("treinamento:verificar_query_compose")

        try:
            qc = QueryCompose.objects.get(id=qc_id)

            if acao == "excluir":
                qc.delete()
                messages.success(request, "Intent excluída com sucesso!")
            elif acao == "editar":
                request.session["query_compose_edicao"] = {
                    "id": qc.id,
                    "tag": qc.tag,
                    "grupo": qc.grupo,
                    "descricao": qc.descricao,
                    "exemplo": qc.exemplo,
                    "comportamento": qc.comportamento,
                }
                messages.info(request, f"Editando intent ID: {qc.id}")
                return redirect("treinamento:cadastrar_query_compose")
            else:
                messages.error(request, "Ação inválida.")
        except QueryCompose.DoesNotExist:
            messages.error(request, "Intent não encontrada.")
        except Exception as e:
            logger.error(
                f"Erro ao processar ação {acao} no QueryCompose {qc_id}: {e}"
            )
            messages.error(request, "Erro ao processar ação. Tente novamente.")

        return redirect("treinamento:verificar_query_compose")

    intents_ok = QueryCompose.objects.filter(embedding__isnull=False).order_by(
        "-created_at"
    )
    intents_erro = QueryCompose.objects.filter(embedding__isnull=True).order_by(
        "-created_at"
    )

    return render(
        request,
        "treinamento/verificar_query_compose.html",
        {"intents_ok": intents_ok, "intents_erro": intents_erro},
    )


def cadastrar_query_compose(request: HttpRequest) -> HttpResponse:
    """View para cadastrar um intent (QueryCompose).

    - Exibe formulário para inserir tag, grupo, description e comportamento.
    - Ao enviar (POST), persiste o registro; o embedding será gerado de forma
      assíncrona pelo signal post_save (sem bloqueio no request).
    - Suporta modo de edição quando há dados salvos em sessão.
    """
    if not has_permission(request.user, "treinar_ia"):
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("home")

    if request.method == "GET":
        dados_edicao = request.session.get("query_compose_edicao")
        if dados_edicao:
            context = {
                "modo_edicao": True,
                "query_compose_id": dados_edicao["id"],
                "tag_inicial": dados_edicao.get("tag", ""),
                "grupo_inicial": dados_edicao.get("grupo", ""),
                "descricao_inicial": dados_edicao.get("descricao", ""),
                "exemplo_inicial": dados_edicao.get("exemplo", ""),
                "comportamento_inicial": dados_edicao.get("comportamento", ""),
            }
        else:
            context = {
                "modo_edicao": False,
                "query_compose_id": None,
                "tag_inicial": "",
                "grupo_inicial": "",
                "descricao_inicial": "",
                "exemplo_inicial": "",
                "comportamento_inicial": "",
            }
        return render(request, "treinamento/cadastrar_query_compose.html", context)

    if request.method == "POST":
        tag = request.POST.get("tag")
        grupo = request.POST.get("grupo")
        descricao = request.POST.get("descricao")
        exemplo = request.POST.get("exemplo")
        comportamento = request.POST.get("comportamento")
        query_compose_id = request.POST.get("query_compose_id")

        # Fallback para sessão caso o hidden não venha
        if not query_compose_id:
            dados_edicao = request.session.get("query_compose_edicao")
            if dados_edicao:
                query_compose_id = str(dados_edicao.get("id"))

        if not tag or not grupo or not descricao or not exemplo or not comportamento:
            messages.error(
                request,
                "Tag, Grupo, Descrição, Exemplo e Comportamento são obrigatórios.",
            )
            return render(
                request,
                "treinamento/cadastrar_query_compose.html",
                {
                    "modo_edicao": bool(query_compose_id),
                    "query_compose_id": query_compose_id,
                    "tag_inicial": tag or "",
                    "grupo_inicial": grupo or "",
                    "descricao_inicial": descricao or "",
                    "exemplo_inicial": exemplo or "",
                    "comportamento_inicial": comportamento or "",
                },
            )

        try:
            with transaction.atomic():
                if query_compose_id:
                    # Edição
                    qc = QueryCompose.objects.get(id=query_compose_id)
                    descricao_antiga = qc.descricao or ""
                    qc.tag = tag
                    qc.grupo = grupo
                    qc.descricao = descricao
                    qc.exemplo = exemplo
                    qc.comportamento = comportamento
                    # Se a descrição mudou, forçar reprocessamento do embedding
                    if (descricao_antiga or "").strip() != (descricao or "").strip():
                        qc.embedding = None
                    qc.save()
                    if "query_compose_edicao" in request.session:
                        del request.session["query_compose_edicao"]
                    messages.success(request, "Intent editada com sucesso!")
                else:
                    # Criação; embedding será gerado via signal post_save
                    QueryCompose.objects.create(
                        tag=tag,
                        grupo=grupo,
                        descricao=descricao,
                        exemplo=exemplo,
                        comportamento=comportamento,
                    )
                    messages.success(request, "Intent cadastrada com sucesso!")

                return redirect("treinamento:cadastrar_query_compose")
        except QueryCompose.DoesNotExist:
            messages.error(request, "Intent não encontrada para edição.")
            return redirect("treinamento:verificar_query_compose")
        except Exception as e:
            logger.error(f"Erro ao cadastrar/editar QueryCompose: {e}")
            messages.error(request, "Erro interno do servidor. Tente novamente.")
            return render(
                request,
                "treinamento/cadastrar_query_compose.html",
                {
                    "modo_edicao": bool(query_compose_id),
                    "query_compose_id": query_compose_id,
                    "tag_inicial": tag or "",
                    "grupo_inicial": grupo or "",
                    "descricao_inicial": descricao or "",
                    "exemplo_inicial": exemplo or "",
                    "comportamento_inicial": comportamento or "",
                },
            )

    # Fallback
    return render(request, "treinamento/cadastrar_query_compose.html")