"""Views para o aplicativo de usuários.

Este módulo contém as views para o gerenciamento de usuários, incluindo
cadastro, login e atribuição de permissões.
"""

from django.contrib import auth, messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib.messages import constants
from django.db.models import Count
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from rolepermissions.checkers import has_permission
from rolepermissions.roles import assign_role
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    StatusAtendimento,
)
from smart_core_assistant_painel.app.ui.operacional.models import (
    Atendente,
)
from smart_core_assistant_painel.app.tenants.models import TenantUser


def cadastro(request: HttpRequest) -> HttpResponse:
    """[ADM-USR-001] Realiza o cadastro de um novo usuário.

    Permite o registro de novos usuários com validação de credenciais.

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
    """[ADM-USR-002] Realiza o login de um usuário.

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

            # Verificar se há um parâmetro 'next'
            next_url = request.POST.get("next")
            if next_url:
                return redirect(next_url)

            # [NOVO] Redirecionamento por Papel (Role-Based Redirect)

            # 1. Superusuário -> Admin do Django
            if user.is_superuser:
                return redirect("/admin/")

            # 2. Usuário de Tenant -> Dashboard do Tenant
            # Verifica se o usuário tem vínculo ativo com algum tenant
            if hasattr(user, "tenant_users"):
                # Busca qualquer vínculo ativo, priorizando owners se houver lógica, mas aqui pegamos o primeiro
                tenant_link = user.tenant_users.filter(is_active=True).first()
                if tenant_link:
                    return redirect("tenants:dashboard")

            # 3. Lógica legado (Atendente) - Mantida como fallback
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

            # Fallback final: redireciona para a home (que vai redirecionar para dashboard/login novamente se necessário)
            # Mas para garantir loop infinito, vamos mandar para tenants:dashboard se autenticado
            return redirect("tenants:dashboard")
        messages.add_message(
            request, constants.ERROR, "Nome de usuário ou senha inválidos."
        )
        return redirect("login")
    return redirect("login")


def logout_view(request: HttpRequest) -> HttpResponse:
    """[ADM-USR-005] Realiza o logout do usuário.

    Redireciona para a página inicial após o logout.
    """
    auth.logout(request)
    return redirect("/")


@user_passes_test(lambda u: u.is_superuser)
def permissoes(request: HttpRequest) -> HttpResponse:
    """[ADM-USR-003] Exibe a página de gerenciamento de permissões.

    Apenas superusuários podem acessar esta página.
    """
    users = User.objects.filter(is_superuser=False)
    return render(request, "permissoes.html", {"users": users})


def tornar_gerente(request: HttpRequest, id: int) -> HttpResponseRedirect:
    """[ADM-USR-003] Atribui a função de gerente a um usuário.

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
    """[ADM-USR-004] Exibe o dashboard para gerentes com métricas de atendimentos.

    Painel exclusivo para gerentes com métricas consolidadas.

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
