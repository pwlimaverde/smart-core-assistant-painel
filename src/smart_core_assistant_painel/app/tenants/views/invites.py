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

ADMIN_PANEL_MODULES = (
    TenantModule.CLIENTES.value,
    TenantModule.OPERACIONAL.value,
    TenantModule.ATENDIMENTOS.value,
)


def _available_permission_modules() -> list[tuple[str, str]]:
    return [
        (
            TenantModule.PAINEL_ADMIN.value,
            "Painel Admin (Clientes, Operacional, Atendimentos)",
        ),
        (TenantModule.TREINAMENTO.value, "Treinamento IA"),
        (TenantModule.CONFIGURACOES.value, "Configurações"),
        (TenantModule.USUARIOS.value, "Usuários"),
    ]


def _build_module_permissions(selected_modules: list[str]) -> dict:
    module_perms: dict[str, dict[str, bool]] = {}
    for mod in TenantModule.all_values():
        module_perms[mod] = {
            "view": False,
            "edit": False,
            "delete": False,
        }

    for mod in selected_modules:
        if mod in module_perms:
            module_perms[mod] = {
                "view": True,
                "edit": True,
                "delete": False,
            }

    if TenantModule.PAINEL_ADMIN.value in selected_modules:
        for mod in ADMIN_PANEL_MODULES:
            module_perms[mod] = {
                "view": True,
                "edit": True,
                "delete": False,
            }

    return module_perms


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

    # Validação de permissão (owner ou permissão de usuários)
    is_owner = request.user == tenant.owner
    if not is_owner:
        t_user = getattr(request, "tenant_user", None)
        if not t_user:
            try:
                t_user = request.user.tenant_profile
            except Exception:
                pass
        if not t_user:
            messages.error(
                request,
                "Acesso negado. Permissão insuficiente para gerenciar usuários.",
            )
            return redirect("tenants:dashboard")
        if not t_user.has_module_permission("usuarios", "view"):
            messages.error(
                request,
                "Acesso negado. Você não tem permissão para gerenciar usuários.",
            )
            return redirect("tenants:dashboard")

    users = TenantUser.objects.filter(tenant=tenant).select_related("user")
    invites = TenantInvite.objects.filter(tenant=tenant, used=False)
    can_manage_users = is_owner
    if not is_owner and "t_user" in locals() and t_user:
        can_manage_users = t_user.has_module_permission("usuarios", "edit")

    return render(
        request,
        "tenants/users/list.html",
        {
            "users": users,
            "invites": invites,
            "tenant": tenant,
            "is_owner": is_owner,
            "can_manage_users": can_manage_users,
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
        if not t_user:
            messages.error(request, "Acesso negado.")
            return redirect("tenants:user_list")
        if not t_user.has_module_permission("usuarios", "edit"):
            messages.error(request, "Acesso negado.")
            return redirect("tenants:user_list")

    if request.method == "POST":
        email = request.POST.get("email")
        name = request.POST.get("name")
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
        module_perms = _build_module_permissions(modules)

        # Criar convite
        invite = TenantInvite.objects.create(
            tenant=tenant,
            email=email,
            name=name,
            role="staff",
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

    modules = _available_permission_modules()
    return render(
        request,
        "tenants/users/invite.html",
        {"modules": modules, "tenant": tenant},
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
    from django.core.mail import get_connection, EmailMultiAlternatives
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
        # Load templates
        from django.template.loader import render_to_string
        import os

        # Get current domain for protocol/domain context
        from django.contrib.sites.shortcuts import get_current_site

        current_site = get_current_site(request)
        protocol = "https" if request.is_secure() else "http"

        asset_base_url = os.getenv(
            "PUBLIC_ASSET_BASE_URL", "https://smartcoreassistant.com.br"
        ).rstrip("/")
        logo_url = f"{asset_base_url}/static/img/logo_branca_smart_v2.png"

        context = {
            "invite": invite,
            "activation_url": activation_url,
            "protocol": protocol,
            "domain": current_site.domain,
            "logo_url": logo_url,
        }

        # Render plain text and HTML versions
        # Simplificação: Usando o corpo do texto original como fallback
        text_content = message
        html_content = render_to_string(
            "tenants/users/invite_email.html", context
        )

        email_msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            to=[invite.email],
        )
        email_msg.attach_alternative(html_content, "text/html")

        # Tentar envio padrão
        email_msg.send()
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

                # Re-criar a mensagem para usar a nova conexão
                # Precisamos recriar porque o connection é passado no init ou atribuído
                email_msg.connection = connection
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
                # Usuário de tenant não deve ter acesso ao admin global.
                is_staff=False,
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

    # Validação de permissão (owner ou permissão de usuários)
    is_owner = request.user == tenant.owner
    if not is_owner:
        t_user = getattr(request, "tenant_user", None)
        if not t_user:
            try:
                t_user = request.user.tenant_profile
            except Exception:
                pass
        if not t_user:
            messages.error(request, "Acesso negado.")
            return redirect("tenants:user_list")
        if not t_user.has_module_permission("usuarios", "edit"):
            messages.error(request, "Acesso negado.")
            return redirect("tenants:user_list")

    # Buscar o TenantUser a ser editado
    tenant_user = get_object_or_404(TenantUser, id=user_id, tenant=tenant)

    # Não pode editar o próprio owner
    if tenant_user.user == tenant.owner:
        messages.error(request, "Não é possível editar permissões do owner.")
        return redirect("tenants:user_list")

    if request.method == "POST":
        modules = request.POST.getlist("modules")

        # Montar permissões: {modulo: {view, edit, delete}}
        module_perms = _build_module_permissions(modules)

        tenant_user.role = "staff"
        tenant_user.module_permissions = module_perms
        tenant_user.save()

        messages.success(
            request, f"Permissões de {tenant_user.user.email} atualizadas!"
        )
        return redirect("tenants:user_list")

    modules = _available_permission_modules()
    # Módulos atualmente permitidos
    current_modules = [
        mod
        for mod, perms in tenant_user.module_permissions.items()
        if perms.get("view", False)
    ]
    if any(mod in current_modules for mod in ADMIN_PANEL_MODULES):
        current_modules.append(TenantModule.PAINEL_ADMIN.value)
    current_set = {
        mod for mod in current_modules if mod not in ADMIN_PANEL_MODULES
    }
    current_modules = [
        mod_value for mod_value, _label in modules if mod_value in current_set
    ]

    return render(
        request,
        "tenants/users/edit_permissions.html",
        {
            "tenant_user": tenant_user,
            "modules": modules,
            "current_modules": current_modules,
            "tenant": tenant,
        },
    )
