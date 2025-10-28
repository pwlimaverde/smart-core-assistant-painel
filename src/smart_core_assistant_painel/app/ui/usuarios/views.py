"""Views para o aplicativo de usuários.

Este módulo contém as views para o gerenciamento de usuários, incluindo
cadastro, login e atribuição de permissões.
"""

from django.contrib import auth, messages
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.messages import constants
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from rolepermissions.roles import assign_role
from smart_core_assistant_painel.app.ui.operacional.models import (
    Atendente,
    Departamento,
)
from django.db.models import Count
from rolepermissions.checkers import has_permission
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    StatusAtendimento,
)


def cadastro(request: HttpRequest) -> HttpResponse:
    """Realiza o cadastro de um novo usuário.

    Args:
        request (HttpRequest): O objeto de requisição.

    Returns:
        HttpResponse: A resposta HTTP.
    """
    if request.method == "GET":
        return render(request, "cadastro.html")
    elif request.method == "POST":
        username = request.POST.get("username")
        senha = request.POST.get("senha")
        confirmar_senha = request.POST.get("confirmar_senha")

        # Validação de campos obrigatórios deve ocorrer antes das demais
        if not username or not senha:
            messages.add_message(
                request,
                constants.ERROR,
                "Nome de usuário e senha são obrigatórios.",
            )
            return redirect("cadastro")
        if senha != confirmar_senha:
            messages.add_message(
                request, constants.ERROR, "As senhas não coincidem."
            )
            return redirect("cadastro")
        if len(senha) < 6:
            messages.add_message(
                request,
                constants.ERROR,
                "A senha deve ter pelo menos 6 caracteres.",
            )
            return redirect("cadastro")
        if User.objects.filter(username=username).exists():
            messages.add_message(
                request, constants.ERROR, "Este nome de usuário já existe."
            )
            return redirect("cadastro")

        User.objects.create_user(username=username, password=senha)
        return redirect("login")
    return redirect("cadastro")


def login(request: HttpRequest) -> HttpResponse:
    """Realiza o login de um usuário.

    Após login bem-sucedido, redireciona para o Kanban do departamento
    associado ao atendente humano vinculado ao usuário (usuario_sistema).
    """
    if request.method == "GET":
        return render(request, "login.html")
    elif request.method == "POST":
        username = request.POST.get("username")
        senha = request.POST.get("senha")
        user = authenticate(
            request, username=username or "", password=senha or ""
        )
        if user:
            auth.login(request, user)
            # Encontrar atendente vinculado ao usuário para redirecionamento
            agente = (
                Atendente.objects.filter(usuario_sistema=user.username)
                .select_related("departamento")
                .first()
            )
            if agente and agente.departamento and agente.departamento_id:
                return redirect(
                    "atendimentos:kanban_departamento",
                    departamento_id=agente.departamento_id,
                )
            # Fallback: se não houver vínculo, redireciona para seleção/treinamento
            return redirect("treinamento:treinar_ia")
        messages.add_message(
            request, constants.ERROR, "Nome de usuário ou senha inválidos."
        )
        return redirect("login")
    return redirect("login")


def permissoes(request: HttpRequest) -> HttpResponse:
    """Exibe a página de gerenciamento de permissões.

    Args:
        request (HttpRequest): O objeto de requisição.

    Returns:
        HttpResponse: A resposta HTTP com a lista de usuários.
    """
    users = User.objects.filter(is_superuser=False)
    return render(request, "permissoes.html", {"users": users})


def tornar_gerente(request: HttpRequest, id: int) -> HttpResponseRedirect:
    """Atribui a função de gerente a um usuário.

    Args:
        request (HttpRequest): O objeto de requisição.
        id (int): O ID do usuário.

    Returns:
        HttpResponseRedirect: Redireciona para a página de permissões.
    """
    user = User.objects.get(id=id)
    assign_role(user, "gerente")
    return redirect("permissoes")


def dashboard_gerente(request: HttpRequest) -> HttpResponse:
    """Exibe o dashboard para gerentes com métricas de atendimentos.

    Requer a permissão "treinar_ia" para acesso, conforme política de
    permissões do projeto.
    """
    if not request.user.is_authenticated:
        return redirect("login")

    # Checagem de permissão seguindo o padrão do módulo de treinamento
    if not has_permission(request.user, "treinar_ia"):
        messages.add_message(
            request,
            constants.ERROR,
            "Você não tem permissão para acessar o dashboard do gerente.",
        )
        return redirect("permissoes")

    # Consulta base com otimização por relacionamento
    qs = Atendimento.objects.all().select_related("departamento")

    # Agregação por status
    by_status_qs = qs.values("status").annotate(total=Count("id")).order_by()
    status_label_map = dict(StatusAtendimento.choices)
    status_counts = [
        {
            "code": item["status"],
            "label": status_label_map.get(item["status"], item["status"]),
            "total": item["total"],
        }
        for item in by_status_qs
    ]

    # Agregação por departamento
    by_dept_qs = (
        qs.values("departamento__id", "departamento__nome")
        .annotate(total=Count("id"))
        .order_by("departamento__nome")
    )
    department_counts = [
        {
            "id": item["departamento__id"],
            "name": item["departamento__nome"] or "Sem departamento",
            "total": item["total"],
        }
        for item in by_dept_qs
    ]

    context = {
        "total_atendimentos": qs.count(),
        "status_counts": status_counts,
        "department_counts": department_counts,
        "statuses": list(StatusAtendimento),
    }
    return render(request, "dashboard_gerente.html", context)
