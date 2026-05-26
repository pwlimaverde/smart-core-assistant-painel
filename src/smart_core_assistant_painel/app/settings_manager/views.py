"""Views para o módulo de configurações do dashboard."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from smart_core_assistant_painel.app.clientes.models import Contato
from smart_core_assistant_painel.app.evolution_sync.models import WhiteList

from .forms import WhiteListForm


def _can_manage_settings(user: object) -> bool:
    """Verifica se o usuário pode gerenciar configurações."""
    if not hasattr(user, "is_authenticated") or not user.is_authenticated:
        return False
    if hasattr(user, "is_superuser") and user.is_superuser:
        return True

    from smart_core_assistant_painel.app.tenants.models import Tenant

    if Tenant.objects.filter(owner=user, active=True).exists():
        return True

    try:
        tenant_profile = user.tenant_profile  # type: ignore[union-attr]
        if tenant_profile and tenant_profile.is_active:
            return tenant_profile.has_module_permission(
                "configuracoes", "edit"
            )
    except Exception:
        pass
    return False


@login_required
def configuracoes_index(request: HttpRequest) -> HttpResponse:
    """Página principal de configurações do tenant."""
    if not _can_manage_settings(request.user):
        messages.error(
            request, "Você não tem permissão para acessar configurações."
        )
        return redirect("dashboard")

    whitelist_count = WhiteList.objects.count()
    whitelist_active = WhiteList.objects.filter(active=True).count()

    context = {
        "whitelist_count": whitelist_count,
        "whitelist_active": whitelist_active,
    }
    return render(request, "apps/settings_manager/configuracoes/index.html", context)


@login_required
def configuracoes_whitelist(request: HttpRequest) -> HttpResponse:
    """Lista de números na whitelist."""
    if not _can_manage_settings(request.user):
        messages.error(
            request, "Você não tem permissão para acessar configurações."
        )
        return redirect("dashboard")

    search = request.GET.get("q", "").strip()
    whitelist = WhiteList.objects.select_related("contact").all()
    if search:
        whitelist = whitelist.filter(
            Q(name__icontains=search)
            | Q(phone_number__icontains=search)
            | Q(contact__nome_contato__icontains=search)
            | Q(contact__telefone__icontains=search)
        )

    context = {
        "whitelist": whitelist,
        "search": search,
    }
    return render(request, "apps/settings_manager/configuracoes/whitelist.html", context)


@login_required
def whitelist_contact_search(request: HttpRequest) -> JsonResponse:
    """Busca contatos por nome/telefone para seleção no formulário."""
    if not _can_manage_settings(request.user):
        return JsonResponse({"error": "Sem permissão"}, status=403)

    if request.method != "GET":
        return JsonResponse({"error": "Método não permitido"}, status=405)

    term = str(request.GET.get("q", "") or "").strip()
    if len(term) < 2:
        return JsonResponse({"results": []})

    contacts = (
        Contato.objects.filter(telefone__isnull=False, ativo=True)
        .exclude(telefone="")
        .filter(
            Q(nome_contato__icontains=term)
            | Q(nome_perfil_whatsapp__icontains=term)
            | Q(telefone__icontains=term)
        )
        .order_by("nome_contato", "telefone")[:20]
    )

    results: list[dict[str, object]] = []
    for contact in contacts:
        phone = str(contact.telefone or "")
        name = (
            str(contact.nome_contato or "").strip()
            or str(contact.nome_perfil_whatsapp or "").strip()
            or phone
        )
        results.append(
            {
                "id": contact.id,
                "name": name,
                "phone_number": phone,
                "label": f"{name} ({phone})",
            }
        )

    return JsonResponse({"results": results})


@login_required
def whitelist_adicionar(request: HttpRequest) -> HttpResponse:
    """Formulário para adicionar número à whitelist."""
    if not _can_manage_settings(request.user):
        messages.error(
            request, "Você não tem permissão para acessar configurações."
        )
        return redirect("dashboard")

    if request.method == "POST":
        form = WhiteListForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Número adicionado à whitelist.")
            return redirect("configuracoes:whitelist")
    else:
        form = WhiteListForm()

    context = {
        "form": form,
        "titulo": "Adicionar à Whitelist",
        "acao": "Adicionar",
    }
    return render(request, "apps/settings_manager/configuracoes/whitelist_form.html", context)


@login_required
def whitelist_editar(request: HttpRequest, pk: int) -> HttpResponse:
    """Formulário para editar número da whitelist."""
    if not _can_manage_settings(request.user):
        messages.error(
            request, "Você não tem permissão para acessar configurações."
        )
        return redirect("dashboard")

    item = get_object_or_404(WhiteList, pk=pk)

    if request.method == "POST":
        form = WhiteListForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Número atualizado com sucesso.")
            return redirect("configuracoes:whitelist")
    else:
        form = WhiteListForm(instance=item)

    context = {
        "form": form,
        "titulo": "Editar Whitelist",
        "acao": "Salvar",
        "item": item,
    }
    return render(request, "apps/settings_manager/configuracoes/whitelist_form.html", context)


@login_required
def whitelist_excluir(request: HttpRequest, pk: int) -> HttpResponse:
    """Exclui um número da whitelist."""
    if not _can_manage_settings(request.user):
        messages.error(
            request, "Você não tem permissão para acessar configurações."
        )
        return redirect("dashboard")

    item = get_object_or_404(WhiteList, pk=pk)

    if request.method == "POST":
        item.delete()
        messages.success(request, "Número removido da whitelist.")
        return redirect("configuracoes:whitelist")

    context = {"item": item}
    return render(request, "apps/settings_manager/configuracoes/whitelist_confirm.html", context)


@login_required
def whitelist_toggle(request: HttpRequest, pk: int) -> HttpResponse:
    """Alterna o status ativo/inativo de um número."""
    if not _can_manage_settings(request.user):
        return JsonResponse({"error": "Sem permissão"}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)

    item = get_object_or_404(WhiteList, pk=pk)
    item.active = not item.active
    item.save(update_fields=["active"])

    return JsonResponse(
        {
            "success": True,
            "active": item.active,
            "message": (
                "Número ativado." if item.active else "Número desativado."
            ),
        }
    )
