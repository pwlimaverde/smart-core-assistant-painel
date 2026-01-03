from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings as django_settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password

from ..models import TenantUser, TenantInvite, Tenant
from ..permissions import TenantModule

User = get_user_model()


@login_required
def list_users(request):
    """Lista funcionários e convites pendentes."""
    tenant = getattr(request, "tenant", None)
    if not tenant:
        return redirect("admin:index")

    # Validação de permissão (apenas owner ou admin do tenant)
    # Se for owner, ok. Se for tenant_user, verificar role.
    if request.user != tenant.owner:
        t_user = getattr(request, "tenant_user", None)
        if not t_user or t_user.role != "admin":
            messages.error(
                request,
                "Acesso negado. Apenas administradores podem gerenciar usuários.",
            )
            return redirect("admin:index")

    users = TenantUser.objects.filter(tenant=tenant).select_related("user")
    invites = TenantInvite.objects.filter(tenant=tenant, used=False)

    return render(
        request,
        "tenants/users/list.html",
        {
            "users": users,
            "invites": invites,
            "tenant": tenant,
            "is_owner": request.user == tenant.owner,
        },
    )


@login_required
def invite_user(request):
    """Owner envia convite para novo funcionário."""
    tenant = getattr(request, "tenant", None)
    if not tenant:
        return redirect("admin:index")

    # Validação de permissão
    if request.user != tenant.owner:
        t_user = getattr(request, "tenant_user", None)
        if not t_user or t_user.role != "admin":
            messages.error(request, "Acesso negado.")
            return redirect("tenants:user_list")

    if request.method == "POST":
        email = request.POST.get("email")
        name = request.POST.get("name")
        role = request.POST.get("role", "staff")
        modules = request.POST.getlist("modules")

        # Validações Básicas
        if not email or not name:
            messages.error(request, "Nome e Email são obrigatórios.")
            return redirect("tenants:user_invite")

        if TenantInvite.objects.filter(
            tenant=tenant, email=email, used=False
        ).exists():
            messages.error(
                request, "Já existe um convite pendente para este email."
            )
            return redirect("tenants:user_invite")

        if User.objects.filter(email=email).exists():
            messages.error(
                request, "Já existe um usuário cadastrado com este email."
            )
            return redirect("tenants:user_invite")

        # Montar permissões: {modulo: {view, edit, delete}}
        # Simplificação: Se selecionou módulo, dá permissão view+edit básico
        module_perms = {}
        for mod in modules:
            module_perms[mod] = {"view": True, "edit": True, "delete": False}

        # Criar convite
        invite = TenantInvite.objects.create(
            tenant=tenant,
            email=email,
            name=name,
            role=role,
            module_permissions=module_perms,
            created_by=request.user,
        )

        # Enviar email
        try:
            activation_url = request.build_absolute_uri(
                reverse("tenants:activate_account", args=[invite.token])
            )
            send_mail(
                subject=f"Convite para acessar {tenant.name}",
                message=f"""
Olá {name},

Você foi convidado para acessar o painel de {tenant.name} como {role}.

Clique no link abaixo para criar sua senha e ativar sua conta:
{activation_url}

Este link expira em 7 dias.
                """,
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, f"Convite enviado para {email}!")
        except Exception as e:
            messages.error(request, f"Erro ao enviar email: {e}")
            # Opcional: delete invite if email failed

        return redirect("tenants:user_list")

    modules = TenantModule.choices()
    roles = [
        ("staff", "Funcionário"),
        ("manager", "Gerente"),
        ("admin", "Administrador"),
        ("viewer", "Visualizador"),
    ]
    return render(
        request,
        "tenants/users/invite.html",
        {"modules": modules, "roles": roles, "tenant": tenant},
    )


def activate_account(request, token):
    """View pública para funcionário definir senha e ativar conta."""
    invite = get_object_or_404(TenantInvite, token=token)

    if not invite.is_valid():
        return render(request, "tenants/users/invite_expired.html")

    if request.method == "POST":
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")

        if password != password_confirm:
            messages.error(request, "As senhas não conferem.")
            return render(
                request, "tenants/users/activate.html", {"invite": invite}
            )

        if len(password) < 8:
            messages.error(request, "A senha deve ter no mínimo 8 caracteres.")
            return render(
                request, "tenants/users/activate.html", {"invite": invite}
            )

        try:
            # Criar User Django
            name_parts = invite.name.split()
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            # Garantir username único (email)
            if User.objects.filter(username=invite.email).exists():
                messages.error(request, "Este email já está cadastrado.")
                return render(
                    request, "tenants/users/activate.html", {"invite": invite}
                )

            user = User.objects.create(
                username=invite.email,
                email=invite.email,
                first_name=first_name,
                last_name=last_name,
                password=make_password(password),
                is_staff=True,  # Necessário para acessar o admin site
                is_active=True,
            )

            # Criar TenantUser
            TenantUser.objects.create(
                user=user,
                tenant=invite.tenant,
                role=invite.role,
                module_permissions=invite.module_permissions,
                created_by=invite.created_by,
            )

            # Marcar convite como usado
            invite.used = True
            invite.save()

            messages.success(
                request,
                "Conta ativada com sucesso! Faça login para continuar.",
            )
            return redirect("admin:login")

        except Exception as e:
            messages.error(request, f"Erro ao ativar conta: {e}")
            return render(
                request, "tenants/users/activate.html", {"invite": invite}
            )

    return render(
        request,
        "tenants/users/activate.html",
        {"invite": invite, "tenant": invite.tenant},
    )
