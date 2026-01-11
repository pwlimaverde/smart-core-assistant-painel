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
    # Buscar tenant do request OU da associação do usuário
    tenant = getattr(request, "tenant", None)
    if not tenant:
        # Tentar via owner
        tenant = Tenant.objects.filter(owner=request.user, active=True).first()
    if not tenant:
        # Tentar via TenantUser
        try:
            tenant_profile = request.user.tenant_profile
            tenant = tenant_profile.tenant
        except Exception:
            pass
    if not tenant:
        messages.error(request, "Nenhum tenant encontrado.")
        return redirect("tenants:dashboard")

    # Validação de permissão (apenas owner ou admin do tenant)
    is_owner = request.user == tenant.owner
    if not is_owner:
        t_user = getattr(request, "tenant_user", None)
        if not t_user:
            try:
                t_user = request.user.tenant_profile
            except Exception:
                pass
        if not t_user or t_user.role != "admin":
            messages.error(
                request,
                "Acesso negado. Apenas administradores podem gerenciar usuários.",
            )
            return redirect("tenants:dashboard")

    users = TenantUser.objects.filter(tenant=tenant).select_related("user")
    invites = TenantInvite.objects.filter(tenant=tenant, used=False)

    return render(
        request,
        "tenants/users/list.html",
        {
            "users": users,
            "invites": invites,
            "tenant": tenant,
            "is_owner": is_owner,
        },
    )


@login_required
def invite_user(request):
    """Owner envia convite para novo funcionário."""
    tenant = getattr(request, "tenant", None)
    if not tenant:
        # Tentar via owner
        tenant = Tenant.objects.filter(owner=request.user, active=True).first()
    if not tenant:
        # Tentar via TenantUser
        try:
            tenant_profile = request.user.tenant_profile
            tenant = tenant_profile.tenant
        except Exception:
            pass

    if not tenant:
        return redirect("tenants:dashboard")

    # Validação de permissão
    if request.user != tenant.owner:
        t_user = getattr(request, "tenant_user", None)
        if not t_user:
            try:
                t_user = request.user.tenant_profile
            except Exception:
                pass
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

        # Call helper to send email
        if _send_invite_email(request, invite):
            messages.success(request, f"Convite enviado para {email}!")
        else:
            # If explicit failure handling is needed beyond the helper's messages
            pass

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


@login_required
def resend_invite(request, invite_id):
    """Reenvia o convite para um usuário."""
    # Buscar tenant
    tenant = getattr(request, "tenant", None)
    if not tenant:
        tenant = Tenant.objects.filter(owner=request.user, active=True).first()

    if not tenant:
        messages.error(request, "Tenant não encontrado.")
        return redirect("tenants:dashboard")

    # Validar permissão (owner ou admin)
    is_owner = request.user == tenant.owner
    if not is_owner:
        t_user = getattr(request, "tenant_user", None)
        if not t_user:
            try:
                t_user = request.user.tenant_profile
            except Exception:
                pass
        if not t_user or t_user.role != "admin":
            messages.error(request, "Acesso negado.")
            return redirect("tenants:user_list")

    invite = get_object_or_404(TenantInvite, id=invite_id, tenant=tenant)

    if invite.used:
        messages.error(request, "Este convite já foi utilizado.")
        return redirect("tenants:user_list")

    if _send_invite_email(request, invite):
        messages.success(request, f"Convite reenviado para {invite.email}!")

    return redirect("tenants:user_list")


def _send_invite_email(request, invite):
    """
    Helper para enviar email de convite.
    Tenta envio padrão e, se falhar por SSL em DEBUG, tenta sem verificação.
    Retorna True se sucesso, False caso contrário.
    """
    from django.core.mail import get_connection, EmailMessage
    import ssl

    activation_url = request.build_absolute_uri(
        reverse("tenants:activate_account", args=[invite.token])
    )

    subject = f"Convite para acessar {invite.tenant.name}"
    message = f"""
Olá {invite.name},

Você foi convidado para acessar o painel de {invite.tenant.name} como {invite.role}.

Clique no link abaixo para criar sua senha e ativar sua conta:
{activation_url}

Este link expira em 7 dias.
    """

    try:
        # Tentar envio padrão
        send_mail(
            subject=subject,
            message=message,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invite.email],
            fail_silently=False,
        )
        return True

    except Exception as e:
        error_str = str(e)
        # Se for erro de certificado SSL e estivermos em DEBUG, tentar workaround
        if "CERTIFICATE_VERIFY_FAILED" in error_str and django_settings.DEBUG:
            try:
                print(
                    f"Erro SSL detectado ({e}). Tentando envio sem verificação SSL..."
                )

                # Criar contexto SSL não verificado
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE

                # Obter conexão com o contexto customizado
                connection = get_connection()
                connection.ssl_context = context

                email_msg = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=django_settings.DEFAULT_FROM_EMAIL,
                    to=[invite.email],
                    connection=connection,
                )
                email_msg.send()
                return True

            except Exception as e2:
                messages.error(
                    request,
                    f"Erro ao reenviar email (tentativa insegura falhou): {e2}",
                )
                return False
        else:
            messages.error(request, f"Erro ao enviar email: {e}")
            return False


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
            return redirect("login")

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


@login_required
def edit_permissions(request, user_id):
    """Edita permissões de módulos para um funcionário do tenant."""
    # Buscar tenant do request OU da associação do usuário
    tenant = getattr(request, "tenant", None)
    if not tenant:
        tenant = Tenant.objects.filter(owner=request.user, active=True).first()
    if not tenant:
        try:
            tenant_profile = request.user.tenant_profile
            tenant = tenant_profile.tenant
        except Exception:
            pass
    if not tenant:
        messages.error(request, "Nenhum tenant encontrado.")
        return redirect("tenants:dashboard")

    # Validação de permissão (apenas owner ou admin do tenant)
    is_owner = request.user == tenant.owner
    if not is_owner:
        t_user = getattr(request, "tenant_user", None)
        if not t_user:
            try:
                t_user = request.user.tenant_profile
            except Exception:
                pass
        if not t_user or t_user.role != "admin":
            messages.error(request, "Acesso negado.")
            return redirect("tenants:user_list")

    # Buscar o TenantUser a ser editado
    tenant_user = get_object_or_404(TenantUser, id=user_id, tenant=tenant)

    # Não pode editar o próprio owner
    if tenant_user.user == tenant.owner:
        messages.error(request, "Não é possível editar permissões do owner.")
        return redirect("tenants:user_list")

    if request.method == "POST":
        role = request.POST.get("role", tenant_user.role)
        modules = request.POST.getlist("modules")

        # Montar permissões: {modulo: {view, edit, delete}}
        module_perms = {}
        for mod in TenantModule.all_values():
            if mod in modules:
                module_perms[mod] = {
                    "view": True,
                    "edit": True,
                    "delete": False,
                }
            else:
                module_perms[mod] = {
                    "view": False,
                    "edit": False,
                    "delete": False,
                }

        tenant_user.role = role
        tenant_user.module_permissions = module_perms
        tenant_user.save()

        messages.success(
            request, f"Permissões de {tenant_user.user.email} atualizadas!"
        )
        return redirect("tenants:user_list")

    modules = TenantModule.choices()
    roles = [
        ("staff", "Funcionário"),
        ("manager", "Gerente"),
        ("admin", "Administrador"),
        ("viewer", "Visualizador"),
    ]
    # Módulos atualmente permitidos
    current_modules = [
        mod
        for mod, perms in tenant_user.module_permissions.items()
        if perms.get("view", False)
    ]

    return render(
        request,
        "tenants/users/edit_permissions.html",
        {
            "tenant_user": tenant_user,
            "modules": modules,
            "roles": roles,
            "current_modules": current_modules,
            "tenant": tenant,
        },
    )
