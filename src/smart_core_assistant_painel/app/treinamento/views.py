"""Views para o aplicativo Treinamento."""

import json
from typing import Any

from django.contrib import messages
from django.db import router, transaction
from django.db.utils import ProgrammingError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from loguru import logger

from smart_core_assistant_painel.modules.ai_engine import FeaturesCompose
from smart_core_assistant_painel.modules.ai_engine.utils.erros import (
    EmbeddingError,
    LlmError,
)

from .models import Documento, QueryCompose, QueryTestFeedback, Treinamento
from .services import TreinamentoService


def _get_tenant_profile(user):
    try:
        return user.tenant_profile
    except Exception:
        return None


def _has_any_module_permission(tenant_profile) -> bool:
    for perms in tenant_profile.module_permissions.values():
        if isinstance(perms, dict) and perms.get("view") is True:
            return True
    return False


def _can_view_training(user) -> bool:
    """Permite visualizar telas de treinamento (modo leitura)."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    from smart_core_assistant_painel.app.tenants.models import Tenant

    if Tenant.objects.filter(owner=user, active=True).exists():
        return True

    tenant_profile = _get_tenant_profile(user)
    if tenant_profile and tenant_profile.is_active:
        return True
    return False


def _can_edit_training(user) -> bool:
    """Permite editar/criar (ações POST) em treinamento."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    from smart_core_assistant_painel.app.tenants.models import Tenant

    if Tenant.objects.filter(owner=user, active=True).exists():
        return True

    tenant_profile = _get_tenant_profile(user)
    if tenant_profile and tenant_profile.is_active:
        return tenant_profile.has_module_permission("treinamento", "edit")
    return False


def treinar_ia(request: HttpRequest) -> HttpResponse:
    """[TRN-CON-001] View para o treinamento da IA.

    Interface para envio de arquivos ou inserção de texto livre para treinamento.
    """
    if not _can_edit_training(request.user):
        messages.error(
            request, "Você não tem permissão para acessar esta página."
        )
        return redirect("dashboard")

    if request.method == "GET":
        if request.GET.get("reset"):
            if "treinamento_edicao" in request.session:
                del request.session["treinamento_edicao"]
            return redirect("treinamento:treinar_ia")

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
                    treinamento: Treinamento = Treinamento.objects.get(
                        id=treinamento_id
                    )
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
                    messages.error(
                        request, "Treinamento não encontrado para edição."
                    )
                    return render(request, "treinamento/treinar_ia.html")
            else:
                treinamento = Treinamento.objects.create(tag=tag, grupo=grupo)
                messages.success(request, "Treinamento criado com sucesso!")

            conteudo_completo = ""

            if documento:
                documento_path = TreinamentoService.processar_arquivo_upload(
                    documento
                )
                if documento_path:
                    docs_arquivo = (
                        TreinamentoService.processar_arquivo_documento(
                            treinamento.id, documento_path, tag, grupo
                        )
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
            return redirect("treinamento:pre_processamento", id=treinamento.id)
    except Exception as e:
        logger.error(f"Erro ao processar treinamento: {e}")
        messages.error(request, "Erro interno do servidor. Tente novamente.")
        return render(request, "treinamento/treinar_ia.html")
    finally:
        TreinamentoService.limpar_arquivo_temporario(documento_path)


def pre_processamento(request: HttpRequest, id: int) -> HttpResponse:
    """[TRN-CON-002] View para o pré-processamento do treinamento.

    Fluxo de revisão e curadoria do conteúdo antes da indexação.
    """
    if not _can_edit_training(request.user):
        messages.error(
            request, "Você não tem permissão para acessar esta página."
        )
        return redirect("dashboard")
    if request.method == "GET":
        return _exibir_pre_processamento(request, id)
    if request.method == "POST":
        return _processar_pre_processamento(request, id)
    return redirect("treinamento:treinar_ia")


def _processar_pre_processamento(
    request: HttpRequest, id: int
) -> HttpResponse:
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
                return redirect(
                    "treinamento:pre_processamento", id=treinamento.id
                )
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
            logger.warning(
                f"Treinamento {id} não possui conteúdo para processar"
            )
            return

        try:
            conteudo_melhorado = FeaturesCompose.melhoria_ia_treinamento(
                conteudo_atual
            )
            treinamento.conteudo = conteudo_melhorado
            treinamento.save(update_fields=["conteudo"])
        except LlmError as e:
            # Não bloqueia o fluxo: mantém o conteúdo atual e finaliza.
            logger.warning(
                f"Falha ao melhorar treinamento {id} via LLM (aceitar): {e}"
            )
        treinamento.treinamento_finalizado = True
        treinamento.save()
        logger.info(
            f"Treinamento {id} aceito e finalizado com melhorias aplicadas"
        )
    except Exception as e:
        logger.error(f"Erro ao aceitar treinamento {id}: {e}")
        raise


def _exibir_pre_processamento(request: HttpRequest, id: int) -> HttpResponse:
    """Exibe a página de pré-processamento."""
    try:
        treinamento = Treinamento.objects.get(id=id)
        conteudo_unificado = treinamento.conteudo or ""

        if not conteudo_unificado.strip():
            logger.warning(
                f"Treinamento {id} sem conteúdo para pré-processamento"
            )
            messages.warning(
                request,
                "Treinamento sem conteúdo. Verifique se o conteúdo foi salvo corretamente.",
            )
            return redirect("treinamento:treinar_ia")

        try:
            texto_melhorado = FeaturesCompose.melhoria_ia_treinamento(
                conteudo_unificado
            )
        except LlmError as e:
            # Fallback: exibe a tela mesmo sem sugestão de melhoria.
            logger.warning(
                f"Falha ao gerar sugestão de melhoria via LLM no pré-processamento "
                f"(treinamento_id={id}): {e}"
            )
            messages.warning(
                request,
                "Não foi possível gerar a sugestão de melhoria automática agora. "
                "Você ainda pode manter ou aceitar o conteúdo atual.",
            )
            texto_melhorado = ""
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
    """[TRN-CON-003] View para verificar treinamentos vetorizados com sucesso e com erro.

    Gestão de treinamentos ativos na base de conhecimento.
    """
    if not _can_view_training(request.user):
        messages.error(
            request, "Você não tem permissão para acessar esta página."
        )
        return redirect("dashboard")

    if request.method == "POST":
        if not _can_edit_training(request.user):
            messages.error(
                request, "Você não tem permissão para editar treinamentos."
            )
            return redirect("treinamento:verificar_treinamentos_vetorizados")
        acao = request.POST.get("acao")
        treinamento_id = request.POST.get("treinamento_id")

        if not acao or not treinamento_id:
            messages.error(
                request, "Ação ou ID do treinamento não especificado."
            )
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
                messages.info(
                    request, f"Editando treinamento ID: {treinamento.id}"
                )
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

    # Observação importante:
    # O app `treinamento` é roteado pelo TenantDatabaseRouter (TENANT_APPS),
    # então este queryset pode apontar para o banco do tenant (alias `tenant_<slug>`).
    # Se o banco do tenant ainda não recebeu migrations, a tabela pode não existir.
    try:
        treinamentos_vetorizados = Treinamento.objects.filter(
            treinamento_finalizado=True, treinamento_vetorizado=True
        ).order_by("-data_criacao")

        treinamentos_com_erro = Treinamento.objects.filter(
            treinamento_finalizado=True, treinamento_vetorizado=False
        ).order_by("-data_criacao")
    except ProgrammingError as e:
        msg = str(e)
        db_alias = router.db_for_read(Treinamento)
        if "oraculo_treinamento" in msg and "does not exist" in msg:
            logger.warning(
                "Tabela ausente para Treinamento. "
                f"db_alias={db_alias} err={msg}"
            )
            messages.error(
                request,
                "O banco de dados deste tenant ainda não foi migrado para o módulo "
                "de Treinamentos (tabela ausente: oraculo_treinamento). "
                "Execute as migrações do tenant e tente novamente.",
            )
            treinamentos_vetorizados = Treinamento.objects.none()
            treinamentos_com_erro = Treinamento.objects.none()
        else:
            raise

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
    """[TRN-INT-002] Lista intents (QueryCompose) com sucesso e com erro, permite editar/excluir.

    Verificação e Ajuste de Intenções.

    - Sucesso: registros com embedding preenchido.
    - Erro: registros sem embedding ("embedding" nulo).
    - Ação "editar": popula sessão e redireciona para a página de cadastro.
    - Ação "excluir": remove o registro.
    """
    if not _can_view_training(request.user):
        messages.error(
            request, "Você não tem permissão para acessar esta página."
        )
        return redirect("dashboard")

    if request.method == "POST":
        if not _can_edit_training(request.user):
            messages.error(
                request, "Você não tem permissão para editar intents."
            )
            return redirect("treinamento:verificar_query_compose")
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
    intents_erro = QueryCompose.objects.filter(
        embedding__isnull=True
    ).order_by("-created_at")

    return render(
        request,
        "treinamento/verificar_query_compose.html",
        {"intents_ok": intents_ok, "intents_erro": intents_erro},
    )


def cadastrar_query_compose(request: HttpRequest) -> HttpResponse:
    """[TRN-INT-001] View para cadastrar um intent (QueryCompose).

    Cadastro de Intenções.

    - Exibe formulário para inserir tag, grupo, description e comportamento.
    - Ao enviar (POST), persiste o registro; o embedding será gerado de forma
      assíncrona pelo signal post_save (sem bloqueio no request).
    - Suporta modo de edição quando há dados salvos em sessão.
    """
    if not _can_edit_training(request.user):
        messages.error(
            request, "Você não tem permissão para acessar esta página."
        )
        return redirect("dashboard")

    if request.method == "GET":
        if request.GET.get("reset"):
            if "query_compose_edicao" in request.session:
                del request.session["query_compose_edicao"]
            return redirect("treinamento:cadastrar_query_compose")

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
        return render(
            request, "treinamento/cadastrar_query_compose.html", context
        )

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

        if (
            not tag
            or not grupo
            or not descricao
            or not exemplo
            or not comportamento
        ):
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
                    if (descricao_antiga or "").strip() != (
                        descricao or ""
                    ).strip():
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
            messages.error(
                request, "Erro interno do servidor. Tente novamente."
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

    # Fallback
    return render(request, "treinamento/cadastrar_query_compose.html")


def testar_query_page(request: HttpRequest) -> HttpResponse:
    """[TRN-TEST-001] Página de teste de respostas do bot.

    Exibe interface de chat interativo para testar análise de mensagens.
    """
    if not _can_view_training(request.user):
        messages.error(
            request, "Você não tem permissão para acessar esta página."
        )
        return redirect("dashboard")

    return render(request, "treinamento/testar_query.html")


def _build_test_intent_prompt(
    intents: list[dict[str, str]],
) -> tuple[str, str]:
    """Constrói prompt de intents para teste, replicando _build_intent_prompt.

    Segue a mesma lógica do attendance_orchestrator._build_intent_prompt(),
    usando PROMPT_INTENT_SYSTEM + comportamentos do QueryCompose +
    PROMPT_INTENT_FOOTER.

    Args:
        intents: Lista de intents detectados (ex: [{"saudacao": "oi"}]).

    Returns:
        Tupla (prompt_completo, tag_match) onde tag_match é a primeira
        tag de QueryCompose encontrada (para exibição no painel).
    """
    from smart_core_assistant_painel.modules.services import SERVICEHUB

    prompt_intent_system = SERVICEHUB.PROMPT_INTENT_SYSTEM
    if not prompt_intent_system:
        prompt_intent_system = (
            "INSTRUÇÕES DO SISTEMA - CONTEXTO PARA RESPOSTA\n"
            "Siga estritamente as orientações abaixo, em "
            "português claro e objetivo.\n"
            "Adapte a resposta ao contexto do atendimento atual."
        )

    prompt_lines: list[str] = [
        prompt_intent_system,
        "Intenções detectadas e orientações:",
    ]

    seen_tags: set[str] = set()
    first_match: str = ""
    index = 0

    for intent in intents:
        if not isinstance(intent, dict):
            continue

        tag: str = list(intent.keys())[0] if intent else ""
        if not tag or tag in seen_tags:
            continue

        seen_tags.add(tag)
        index += 1

        # Busca comportamento exato (mesmo que orchestrator)
        qc = QueryCompose.objects.filter(tag=tag).first()

        if qc:
            if not first_match:
                first_match = tag
            behavior: str = " ".join(str(qc.comportamento).split()).strip()
            prompt_lines.append(f"{index}. [{tag}] {behavior}")
        else:
            # Busca comportamento similar por embedding do intent
            try:
                intent_text = f"{tag}: {intent.get(tag, '')}"
                intent_vector: list[float] = (
                    FeaturesCompose.generate_embeddings(intent_text)
                )
                comportamento: str | None = (
                    QueryCompose.buscar_comportamento_similar(intent_vector)
                )
                if comportamento:
                    prompt_lines.append(f"{index}. [{tag}] {comportamento}")
            except Exception:
                logger.debug(f"Embedding para intent '{tag}' indisponível.")

    prompt_intent_footer = SERVICEHUB.PROMPT_INTENT_FOOTER
    if not prompt_intent_footer:
        prompt_intent_footer = (
            "Se houver múltiplas intenções, processe as instruções de "
            "CADA UMA delas. Em seguida, combine as respostas em um "
            "texto organizado."
        )
    prompt_lines.append(prompt_intent_footer)

    return "\n".join(prompt_lines), first_match


@require_POST
def testar_resposta_query(request: HttpRequest) -> JsonResponse:
    """[TRN-TEST-001] Endpoint AJAX para testar resposta do bot.

    Recebe mensagem simulada e retorna análise completa com
    resposta, confiabilidade, entidades e intents.
    """
    if not _can_view_training(request.user):
        return JsonResponse({"error": "Sem permissão"}, status=403)

    try:
        body: dict[str, Any] = json.loads(request.body)
        mensagem: str = body.get("mensagem", "").strip()
        chat_history_in: list[dict[str, Any]] = (
            body.get("chat_history", []) or []
        )
        context_state_in: dict[str, Any] = body.get("context_state", {}) or {}
    except (json.JSONDecodeError, AttributeError):
        mensagem = request.POST.get("mensagem", "").strip()
        chat_history_in = []
        context_state_in = {}

    if not mensagem:
        return JsonResponse({"error": "Mensagem é obrigatória."}, status=400)

    try:
        from langchain_core.messages import AIMessage, HumanMessage

        def _to_lc_messages(
            items: list[dict[str, Any]],
        ) -> list[HumanMessage | AIMessage]:
            msgs: list[HumanMessage | AIMessage] = []
            for it in items:
                if not isinstance(it, dict):
                    continue
                role = str(it.get("role", "")).strip().lower()
                content = str(it.get("content", "")).strip()
                if not content:
                    continue
                if role in {"user", "human", "cliente"}:
                    msgs.append(HumanMessage(content=content))
                elif role in {"assistant", "ai", "bot"}:
                    msgs.append(AIMessage(content=content))
            return msgs

        def _dedupe_dict_list(
            items: list[dict[str, Any]],
        ) -> list[dict[str, Any]]:
            seen: set[str] = set()
            out: list[dict[str, Any]] = []
            for it in items:
                if not isinstance(it, dict):
                    continue
                key = json.dumps(it, sort_keys=True, ensure_ascii=False)
                if key in seen:
                    continue
                seen.add(key)
                out.append(it)
            return out

        lc_chat_history = _to_lc_messages(chat_history_in)

        # Historico "legivel" para AnalisePrevia (ele nao usa BaseMessage diretamente).
        conteudo_mensagens: list[str] = []
        for it in chat_history_in:
            if isinstance(it, dict) and str(it.get("content", "")).strip():
                conteudo_mensagens.append(str(it.get("content", "")).strip())

        prev_entidades: list[dict[str, Any]] = []
        if isinstance(context_state_in.get("entidades_extraidas"), list):
            prev_entidades = context_state_in.get("entidades_extraidas", [])
        prev_intents: list[dict[str, Any]] = []
        if isinstance(context_state_in.get("intents_detectados"), list):
            prev_intents = context_state_in.get("intents_detectados", [])

        # 1. Análise prévia: extrair entidades e intents (mesmo que
        #    MessageAnalyzer.analyze_message_content no fluxo real)
        intent_types_config = QueryCompose.build_intent_types_config()
        apm_result = FeaturesCompose.analise_previa_mensagem(
            historico_atendimento={
                "conteudo_mensagens": conteudo_mensagens,
                "entidades_extraidas": prev_entidades,
                "intents_detectados": prev_intents,
                "historico_atendimentos": [],
            },
            context=mensagem,
            valid_intent_types=intent_types_config,
        )
        entidades_novas = apm_result.entity_types
        intents_novas = apm_result.intent_types

        entidades = _dedupe_dict_list(
            [*(prev_entidades or []), *(entidades_novas or [])]
        )
        intents = _dedupe_dict_list(
            [*(prev_intents or []), *(intents_novas or [])]
        )

        # 2. Construir prompt de intents (mesmo que
        #    _build_intent_prompt no attendance_orchestrator)
        prompt_human, query_compose_match = _build_test_intent_prompt(intents)

        # 3. Gerar embedding da mensagem para busca RAG
        vector_mensagem = FeaturesCompose.generate_embeddings(mensagem)

        # 4. Buscar documentos similares (RAG)
        dados_treinamento, doc_ids = Documento.buscar_documentos_similares(
            query_vec=vector_mensagem
        )

        # 5. Análise de mensagem principal (mesmo que
        #    _call_ai_and_register no attendance_orchestrator)
        am_result = FeaturesCompose.analise_mensage(
            fluxos_disponiveis={},
            context=mensagem,
            historico_atendimento={
                "chat_history": lc_chat_history,
                "entidades_extraidas": entidades,
                "intents_detectados": intents,
                "historico_atendimentos": [],
            },
            prompt_human=prompt_human,
            dados_treinamento=dados_treinamento,
        )

        return JsonResponse(
            {
                "resposta_bot": am_result.resposta_bot,
                "confiabilidade": round(am_result.confiabilidade, 4),
                "transferir_atendimento": am_result.transferir_atendimento,
                "fluxo_transferencia": am_result.fluxo_transferencia,
                "entidades_extraidas": entidades,
                "intents_detectados": intents,
                "documentos_utilizados": doc_ids,
                "query_compose_match": query_compose_match or "",
            }
        )

    except EmbeddingError as e:
        logger.error(f"Erro de embeddings ao testar resposta: {e}")
        return JsonResponse(
            {
                "error": (
                    "Erro no serviço de embeddings. "
                    "Verifique se as API keys e o modelo de "
                    "embeddings estão configurados corretamente."
                ),
                "detail": str(e),
            },
            status=500,
        )

    except LlmError as e:
        logger.error(f"Erro de LLM ao testar resposta: {e}")
        return JsonResponse(
            {
                "error": (
                    "Erro no serviço de IA. "
                    "Verifique se o LLM está configurado."
                ),
                "detail": str(e),
            },
            status=500,
        )

    except Exception as e:
        logger.error(f"Erro ao testar resposta: {e}")
        return JsonResponse({"error": f"Erro ao processar: {e!s}"}, status=500)


@require_POST
def feedback_resposta_query(request: HttpRequest) -> JsonResponse:
    """[TRN-TEST-002] Registra feedback sobre a resposta do bot."""
    if not _can_edit_training(request.user):
        return JsonResponse({"error": "Sem permissão"}, status=403)

    try:
        body: dict[str, Any] = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "Dados inválidos."}, status=400)

    mensagem_original = body.get("mensagem_original", "").strip()
    resposta_bot = body.get("resposta_bot", "").strip()
    avaliacao = body.get("avaliacao", "").strip()
    resposta_corrigida = body.get("resposta_corrigida", "").strip()
    confiabilidade = body.get("confiabilidade", 0.0)
    entidades_json = body.get("entidades_json", {})
    intents_json = body.get("intents_json", {})
    documentos_ids = body.get("documentos_ids", [])

    if not mensagem_original or not resposta_bot or not avaliacao:
        return JsonResponse(
            {"error": "Campos obrigatórios faltando."}, status=400
        )

    if avaliacao not in ("bom", "ruim"):
        return JsonResponse(
            {"error": "Avaliação deve ser 'bom' ou 'ruim'."}, status=400
        )

    feedback = QueryTestFeedback.objects.create(
        mensagem_original=mensagem_original,
        resposta_bot=resposta_bot,
        resposta_corrigida=resposta_corrigida or None,
        avaliacao=avaliacao,
        confiabilidade=confiabilidade,
        entidades_json=entidades_json,
        intents_json=intents_json,
        documentos_ids=documentos_ids,
    )

    return JsonResponse(
        {
            "success": True,
            "feedback_id": feedback.id,
            "message": "Feedback registrado com sucesso.",
        }
    )
