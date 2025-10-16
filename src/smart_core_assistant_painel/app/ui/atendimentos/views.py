"""Views for the Atendimentos app."""

import json
from typing import Any, Optional

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from loguru import logger
from django.utils.html import escape
from django.middleware.csrf import get_token
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from rolepermissions.checkers import has_permission
from smart_core_assistant_painel.app.ui.operacional.models import (
    AtendenteHumano,
    Departamento,
)
from smart_core_assistant_painel.modules.ai_engine import FeaturesCompose

from .models import Atendimento, StatusAtendimento, Mensagem, TipoRemetente, TipoMensagem
from .utils import sched_message_response, set_wa_buffer


def _get_user_departamentos(request: HttpRequest):
    """Retorna os departamentos ativos aos quais o usuário pertence.

    Um usuário pertence a um departamento se existir um AtendenteHumano
    vinculado ao seu `usuario_sistema` com `departamento` correspondente.
    """
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return Departamento.objects.none()
    username: str = getattr(request.user, "username", "")
    if not username:
        return Departamento.objects.none()
    return (
        Departamento.objects.filter(ativo=True, atendentes__usuario_sistema=username)
        .distinct()
        .order_by("nome")
    )

@csrf_exempt
def webhook_whatsapp(request: HttpRequest) -> JsonResponse:
    """Endpoint to receive WhatsApp message notifications."""
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)
        if not request.body:
            return JsonResponse({"error": "Empty request body"}, status=400)
        try:
            body_str = request.body.decode("utf-8")
        except UnicodeDecodeError:
            body_str = request.body.decode("utf-8", errors="ignore")
            logger.warning("Decoding with errors='ignore' applied")

        data: dict[str, Any] = json.loads(body_str)
        departamento = Departamento.validar_api_key(data)
        if not departamento:
            return JsonResponse(
                {"error": "Invalid or inactive API key"}, status=401
            )

        logger.info(f"Received webhook: {data}")
        message = FeaturesCompose.load_message_data(data)
        set_wa_buffer(message)
        sched_message_response(message.numero_telefone)

        return JsonResponse({"status": "success"}, status=200)
    except Exception as e:
        logger.error(f"Critical error in WhatsApp webhook: {e}", exc_info=True)
        return JsonResponse({"error": "Internal server error"}, status=500)


def _get_current_agent(request: HttpRequest) -> Optional[AtendenteHumano]:
    """Obtém o atendente humano vinculado ao usuário logado.

    Comentário: Para mapear a coluna "Meus", relacionamos o usuário
    autenticado com o AtendenteHumano via campo `usuario_sistema`.
    """
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return None
    username: str = getattr(request.user, "username", "")
    if not username:
        return None
    return (
        AtendenteHumano.objects.filter(usuario_sistema=username)
        .select_related("departamento")
        .first()
    )


@login_required(login_url="/usuarios/login/")
def kanban_departamento(
    request: HttpRequest, departamento_id: int
) -> HttpResponse:
    """Renderiza o Kanban de atendimentos por departamento e processa ações.

    - Colunas: Fila (aguardando atendente), Meus (atribuídos ao agente),
      Aguardando Cliente, Finalizados.
    - Ações via POST: assign_next, unassign, transfer, change_status.
    """
    # Autenticação obrigatória: redireciona para login se necessário
    if not request.user.is_authenticated:
        return redirect("login")

    departamento = get_object_or_404(Departamento, id=departamento_id)

    # Detecta se o usuário possui permissão de gerente (política atual: "treinar_ia")
    is_manager: bool = has_permission(request.user, "treinar_ia")

    # Lista de departamentos permitidos ao usuário (se não gerente)
    allowed_departamentos_qs = (
        Departamento.objects.filter(ativo=True).order_by("nome")
        if is_manager
        else _get_user_departamentos(request)
    )
    allowed_departamentos_ids = set(allowed_departamentos_qs.values_list("id", flat=True))

    # Bloquear acesso ao departamento se usuário não fizer parte
    if not is_manager and departamento.id not in allowed_departamentos_ids:
        return HttpResponse("Acesso negado ao departamento.", status=403)

    # Redirecionamento por GET para mudança de departamento
    if request.method == "GET":
        target_dep_str: str = request.GET.get("target_department_id", "")
        if target_dep_str:
            try:
                target_dep_id = int(target_dep_str)
            except ValueError:
                target_dep_id = 0
            if (
                target_dep_id > 0
                and Departamento.objects.filter(id=target_dep_id, ativo=True).exists()
                and (is_manager or target_dep_id in allowed_departamentos_ids)
            ):
                return redirect(
                    "atendimentos:kanban_departamento", departamento_id=target_dep_id
                )

    # Suporte a resposta parcial (detalhes do atendimento) para modal
    # Quando ?partial=1 e atendimento_id são informados, retorna um HTML compacto
    # com informações principais do atendimento sem re-renderizar toda a página.
    if request.method == "GET" and request.GET.get("partial") == "1":
        atendimento_id_str: str = request.GET.get("atendimento_id", "0")
        try:
            atendimento_id = int(atendimento_id_str)
        except ValueError:
            atendimento_id = 0
        if atendimento_id <= 0:
            return HttpResponse("<p>Atendimento inválido.</p>", content_type="text/html", status=400)

        atendimento = get_object_or_404(
            Atendimento.objects.select_related("contato", "atendente_humano", "departamento"),
            id=atendimento_id,
        )

        # Escapar campos potencialmente controlados pelo usuário para evitar XSS
        contato_nome = escape(getattr(atendimento.contato, "nome_contato", "") or "")
        contato_tel = escape(getattr(atendimento.contato, "telefone", "") or "")
        agente_nome = escape(getattr(getattr(atendimento, "atendente_humano", None), "nome", "") or "-")
        dep_nome = escape(getattr(atendimento.departamento, "nome", "") or "-")
        status_value = escape(str(atendimento.status))
        data_inicio = escape(str(getattr(atendimento, "data_inicio", "") or "-"))
        data_ultima = escape(str(getattr(atendimento, "data_ultima_mensagem", "") or "-"))
        data_fim = escape(str(getattr(atendimento, "data_fim", "") or "-"))

        csrf_token = get_token(request)
        csrf_hidden = f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">'  # nosec - token gerado pelo Django

        html = f"""
        <div class=\"space-y-2\">
          <div class=\"flex items-center justify-between\">
            <h3 class=\"text-lg font-semibold\">Atendimento #{atendimento.id}</h3>
            <span class=\"text-sm text-gray-500\">Departamento: {dep_nome}</span>
          </div>
          <div class=\"grid grid-cols-2 gap-4\">
            <div>
              <div class=\"text-xs text-gray-500\">Contato</div>
              <div class=\"text-sm\">{contato_nome or '-'}<span class=\"text-gray-400\"> • </span>{contato_tel or '-'}</div>
            </div>
            <div>
              <div class=\"text-xs text-gray-500\">Status</div>
              <div class=\"text-sm\">{status_value}</div>
            </div>
            <div>
              <div class=\"text-xs text-gray-500\">Atendente</div>
              <div class=\"text-sm\">{agente_nome}</div>
            </div>
            <div>
              <div class=\"text-xs text-gray-500\">Datas</div>
              <div class=\"text-sm\">Início: {data_inicio}</div>
              <div class=\"text-sm\">Última: {data_ultima}</div>
              <div class=\"text-sm\">Fim: {data_fim}</div>
            </div>
          </div>
          <div class=\"pt-2 border-t mt-2\">
            <div class=\"text-xs text-gray-500 mb-1\">Ações rápidas</div>
            <div class=\"flex flex-wrap gap-2\">
              <form method=\"post\" class=\"inline\">
                {csrf_hidden}
                <input type=\"hidden\" name=\"atendimento_id\" value=\"{atendimento.id}\">
                <input type=\"hidden\" name=\"action\" value=\"unassign\">
                <button class=\"px-2 py-1 bg-yellow-600 text-white rounded text-sm\">Desatribuir</button>
              </form>
              <form method=\"post\" class=\"inline\">
                {csrf_hidden}
                <input type=\"hidden\" name=\"atendimento_id\" value=\"{atendimento.id}\">
                <input type=\"hidden\" name=\"action\" value=\"change_status\">
                <input type=\"hidden\" name=\"status\" value=\"resolvido\">
                <button class=\"px-2 py-1 bg-green-600 text-white rounded text-sm\">Marcar como Resolvido</button>
              </form>
            </div>
          </div>
          <div class=\"pt-4 mt-4 border-t\">
            <div class=\"text-xs text-gray-500 mb-2\">Mensagens</div>
            <div class=\"space-y-2 max-h-64 overflow-y-auto\">
        """
        # Renderizar mensagens do atendimento
        for m in atendimento.mensagens.select_related().order_by("timestamp"):
            remetente_label = escape(dict(TipoRemetente.choices).get(m.remetente, m.remetente))
            conteudo_msg = escape(m.conteudo or "")
            ts = escape(m.timestamp.strftime("%d/%m/%Y %H:%M"))
            html += (
                f"<div class=\"p-2 rounded bg-gray-50\"><div class=\"text-xs text-gray-500\">"
                f"{ts} • {remetente_label}</div><div class=\"text-sm\">{conteudo_msg}</div></div>"
            )
        html += f"""
            </div>
            <form method=\"post\" class=\"mt-3 space-y-2\">
              {csrf_hidden}
              <input type=\"hidden\" name=\"atendimento_id\" value=\"{atendimento.id}\">
              <input type=\"hidden\" name=\"action\" value=\"send_message\">
              <label class=\"text-xs text-gray-500\">Enviar nova mensagem</label>
              <textarea name=\"message\" rows=\"3\" class=\"w-full border rounded p-2 text-sm\" placeholder=\"Digite sua mensagem\" required></textarea>
              <button class=\"px-3 py-1 bg-blue-600 text-white rounded text-sm\">Enviar</button>
            </form>
          </div>
          <div class=\"pt-4 mt-4 border-t\">
            <div class=\"text-xs text-gray-500 mb-2\">Editar atendimento</div>
            <form method=\"post\" class=\"space-y-2\">
              {csrf_hidden}
              <input type=\"hidden\" name=\"atendimento_id\" value=\"{atendimento.id}\">
              <input type=\"hidden\" name=\"action\" value=\"update_atendimento\">
              <div>
                <label class=\"text-xs text-gray-500\">Assunto</label>
                <input type=\"text\" name=\"assunto\" value=\"{escape(atendimento.assunto or '')}\" class=\"w-full border rounded p-1 text-sm\">
              </div>
              <div>
                <label class=\"text-xs text-gray-500\">Prioridade</label>
                <select name=\"prioridade\" class=\"w-full border rounded p-1 text-sm\">
                  <option value=\"baixa\"{(' selected' if atendimento.prioridade == 'baixa' else '')}>Baixa</option>
                  <option value=\"normal\"{(' selected' if atendimento.prioridade == 'normal' else '')}>Normal</option>
                  <option value=\"alta\"{(' selected' if atendimento.prioridade == 'alta' else '')}>Alta</option>
                  <option value=\"urgente\"{(' selected' if atendimento.prioridade == 'urgente' else '')}>Urgente</option>
                </select>
              </div>
              <div>
                <label class=\"text-xs text-gray-500\">Status</label>
                <select name=\"status\" class=\"w-full border rounded p-1 text-sm\">
        """
        for s in StatusAtendimento:
            sel = " selected" if str(atendimento.status) == s.value else ""
            html += f"<option value=\"{s.value}\"{sel}>{escape(s.label)}</option>"
        html += """
                </select>
              </div>
              <div>
                <label class=\"text-xs text-gray-500\">Departamento</label>
                <select name=\"departamento_id\" class=\"w-full border rounded p-1 text-sm\">
        """
        # Filtrar departamentos disponíveis de acordo com permissões
        for d in allowed_departamentos_qs:
            sel = " selected" if atendimento.departamento_id == d.id else ""
            html += f"<option value=\"{d.id}\"{sel}>{escape(d.nome)}</option>"
        html += """
                </select>
              </div>
              <div>
                <label class=\"text-xs text-gray-500\">Avaliação (1-5)</label>
                <input type=\"number\" min=\"1\" max=\"5\" name=\"avaliacao\" value=\"{escape(str(atendimento.avaliacao or ''))}\" class=\"w-full border rounded p-1 text-sm\">
              </div>
              <div>
                <label class=\"text-xs text-gray-500\">Feedback</label>
                <textarea name=\"feedback\" rows=\"2\" class=\"w-full border rounded p-2 text-sm\">{escape(atendimento.feedback or '')}</textarea>
              </div>
              <button class=\"px-3 py-1 bg-indigo-600 text-white rounded text-sm\">Salvar alterações</button>
            </form>
          </div>
        </div>
        """
        return HttpResponse(html, content_type="text/html")

    if request.method == "POST":
        action: str = request.POST.get("action", "")
        atendimento_id_str: str = request.POST.get("atendimento_id", "0")
        try:
            atendimento_id = int(atendimento_id_str)
        except ValueError:
            atendimento_id = 0
        if atendimento_id <= 0:
            logger.warning("atendimento_id inválido em POST")
            return redirect(
                "atendimentos:kanban_departamento",
                departamento_id=departamento.id,
            )

        atendimento = get_object_or_404(Atendimento, id=atendimento_id)

        # Suporte a AJAX (drag-and-drop): identificar e preparar resposta JSON
        is_ajax: bool = (
            request.headers.get("x-requested-with", "").lower() == "xmlhttprequest"
        )
        error_occurred: bool = False
        error_message: str = ""

        try:
            if action == "assign_next":
                # Atribuição round-robin usando método do Departamento
                agente = departamento.selecionar_proximo_atendente()
                if agente:
                    atendimento.assign_to_agent(
                        agente, observacao="Atribuição automática"
                    )
                else:
                    logger.info(
                        "Nenhum atendente disponível para atribuição automática"
                    )
            elif action == "unassign":
                atendimento.unassign_agent("Desatribuição manual")
            elif action == "transfer":
                target_id_str = request.POST.get("target_departamento_id", "0")
                try:
                    target_id = int(target_id_str)
                except ValueError:
                    target_id = 0
                if target_id > 0:
                    # Permitir apenas departamentos válidos e acessíveis ao usuário (se não gerente)
                    if is_manager or target_id in allowed_departamentos_ids:
                        target_dep = get_object_or_404(Departamento, id=target_id)
                        atendimento.transfer_to_department(target_dep)
                    else:
                        error_occurred = True
                        error_message = "Departamento alvo não permitido para este usuário."
            elif action == "change_status":
                status_value: str = request.POST.get("status", "")
                valid_values = [s.value for s in StatusAtendimento]
                if status_value in valid_values:
                    atendimento.change_status(StatusAtendimento(status_value))
            elif action == "assign_to_me":
                # Atribuir ao atendente vinculado ao usuário atual (para drop na coluna "Meus")
                agente_atual = _get_current_agent(request)
                if agente_atual is None:
                    error_occurred = True
                    error_message = (
                        "Usuário não está vinculado a um atendente humano ativo."
                    )
                else:
                    # Garantir que o atendente pertence ao departamento atual
                    if agente_atual.departamento_id == departamento.id:
                        atendimento.assign_to_agent(
                            agente_atual, observacao="Atribuição manual (drag-and-drop)"
                        )
                    else:
                        error_occurred = True
                        error_message = "Atendente não pertence ao departamento atual."
            elif action == "send_message":
                conteudo_msg: str = request.POST.get("message", "").strip()
                if not conteudo_msg:
                    error_occurred = True
                    error_message = "Mensagem não pode ser vazia."
                else:
                    Mensagem.objects.create(
                        atendimento=atendimento,
                        tipo=TipoMensagem.TEXTO_FORMATADO,
                        conteudo=conteudo_msg,
                        remetente=TipoRemetente.ATENDENTE_HUMANO,
                    )
                    atendimento.data_ultima_mensagem = timezone.now()
                    atendimento.save(update_fields=["data_ultima_mensagem"])
            elif action == "update_atendimento":
                # Atualiza parâmetros do atendimento e suporta transferência
                assunto: str | None = request.POST.get("assunto")
                prioridade: str | None = request.POST.get("prioridade")
                status_value: str | None = request.POST.get("status")
                dep_id_str: str = request.POST.get("departamento_id", "0")
                feedback: str | None = request.POST.get("feedback")
                avaliacao_str: str = request.POST.get("avaliacao", "")
                try:
                    dep_id = int(dep_id_str)
                except ValueError:
                    dep_id = 0
                avaliacao: int | None = None
                try:
                    avaliacao = int(avaliacao_str) if avaliacao_str else None
                except ValueError:
                    avaliacao = None
                # Validar prioridade
                if prioridade in {"baixa", "normal", "alta", "urgente"}:
                    atendimento.prioridade = prioridade  # type: ignore[assignment]
                if assunto is not None:
                    atendimento.assunto = assunto
                if feedback is not None:
                    atendimento.feedback = feedback
                if avaliacao is not None and 1 <= avaliacao <= 5:
                    atendimento.avaliacao = avaliacao
                if status_value and status_value in [s.value for s in StatusAtendimento]:
                    atendimento.status = StatusAtendimento(status_value)
                # Transferência de departamento, se alterado
                if dep_id > 0 and dep_id != atendimento.departamento_id:
                    # Transferência permitida apenas para departamentos acessíveis
                    if is_manager or dep_id in allowed_departamentos_ids:
                        target_dep = get_object_or_404(Departamento, id=dep_id)
                        atendimento.departamento = target_dep
                    else:
                        error_occurred = True
                        error_message = "Departamento selecionado não permitido."
                atendimento.save()
        except Exception as exc:
            # Capturar exceções de processamento de ações para evitar SyntaxError
            # e garantir resposta consistente para AJAX.
            error_occurred = True
            error_message = (
                f"Ocorreu um erro ao processar a ação: {str(exc)}"
            )
            logger.exception(
                "Erro ao processar ação '%s' para atendimento %s",
                action,
                atendimento.id,
            )

        # Para AJAX (drag-and-drop), responder JSON e evitar redirect
        if is_ajax:
            if error_occurred:
                return JsonResponse({
                    "ok": False,
                    "error": error_message,
                    "atendimento_id": atendimento.id,
                }, status=400)
            return JsonResponse({
                "ok": True,
                "atendimento_id": atendimento.id,
                "status": atendimento.status.value,
                "assigned": atendimento.atendente_humano_id is not None,
            })

        return redirect(
            "atendimentos:kanban_departamento", departamento_id=departamento.id
        )

    # Consulta base para o departamento com otimização de relações
    base_qs = (
        Atendimento.objects.filter(departamento=departamento)
        .select_related("contato", "atendente_humano")
        .order_by("-data_ultima_mensagem", "-data_inicio")
    )

    current_agent = _get_current_agent(request)

    # Colunas do Kanban
    fila_qs = base_qs.filter(
        status=StatusAtendimento.AGUARDANDO_ATENDENTE,
        atendente_humano__isnull=True,
    )

    # Se gerente, permite visualizar atendimentos de todos os agentes do departamento
    if is_manager:
        assigned_qs = base_qs.filter(atendente_humano__isnull=False).exclude(
            status__in=[
                StatusAtendimento.RESOLVIDO,
                StatusAtendimento.CANCELADO,
            ]
        )
        aguardando_cliente_qs = base_qs.filter(
            status=StatusAtendimento.AGUARDANDO_CONTATO,
        )
        finalizados_qs = base_qs.filter(
            status__in=[
                StatusAtendimento.RESOLVIDO,
                StatusAtendimento.CANCELADO,
            ],
        )
    else:
        if current_agent:
            assigned_qs = base_qs.filter(atendente_humano=current_agent).exclude(
                status__in=[
                    StatusAtendimento.RESOLVIDO,
                    StatusAtendimento.CANCELADO,
                ]
            )
            aguardando_cliente_qs = base_qs.filter(
                atendente_humano=current_agent,
                status=StatusAtendimento.AGUARDANDO_CONTATO,
            )
            finalizados_qs = base_qs.filter(
                atendente_humano=current_agent,
                status__in=[
                    StatusAtendimento.RESOLVIDO,
                    StatusAtendimento.CANCELADO,
                ],
            )
        else:
            assigned_qs = base_qs.none()
            aguardando_cliente_qs = base_qs.none()
            finalizados_qs = base_qs.none()

    context: dict[str, Any] = {
        "departamento": departamento,
        "current_agent": current_agent,
        "is_manager": is_manager,
        "columns": {
            "fila": fila_qs,
            "meus": assigned_qs,
            "aguardando_cliente": aguardando_cliente_qs,
            "finalizados": finalizados_qs,
        },
        "statuses": list(StatusAtendimento),
        # Dropdown de departamentos limitado aos que o usuário pode acessar
        "departamentos": allowed_departamentos_qs,
    }

    return render(request, "atendimentos/kanban.html", context)
