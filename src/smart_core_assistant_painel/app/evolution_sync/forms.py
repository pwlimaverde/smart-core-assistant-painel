"""Forms para o app evolution_sync."""

from typing import Any

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import WhiteList


class WhiteListAdminForm(forms.ModelForm[WhiteList]):
    """Form do admin para WhiteList com preenchimento automático via contato.

    Quando um contato é selecionado, os campos ``name`` e ``phone_number``
    são opcionais: se deixados em branco, são preenchidos automaticamente
    com os dados do contato (``nome_contato`` e ``telefone``).
    """

    name = forms.CharField(
        max_length=100,
        required=False,
        label=_("Name"),
        help_text=_(
            "Deixe em branco para preencher automaticamente do contato."
        ),
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        label=_("Phone number"),
        help_text=_(
            "Deixe em branco para preencher automaticamente do contato."
        ),
    )

    class Meta:
        model = WhiteList
        fields = "__all__"

    class Media:
        js = ("js/whitelist_contact_autofill.js",)

    def clean(self) -> dict[str, Any]:
        """Valida e auto-popula name/phone_number a partir do contato.

        Se name ou phone_number estiverem vazios e um contato foi
        selecionado, os valores são preenchidos com os dados do contato.
        Caso contrário, os erros de validação são reportados normalmente.
        """
        cleaned_data: dict[str, Any] = super().clean() or {}
        contact = cleaned_data.get("contact")
        name = (cleaned_data.get("name") or "").strip()
        phone_number = (cleaned_data.get("phone_number") or "").strip()

        # Auto-preencher name do contato
        if not name:
            if contact and contact.nome_contato:
                cleaned_data["name"] = contact.nome_contato
            else:
                self.add_error("name", _("This field is required."))

        # Auto-preencher phone_number do contato
        if not phone_number:
            if contact and contact.telefone:
                cleaned_data["phone_number"] = contact.telefone
            else:
                self.add_error("phone_number", _("This field is required."))

        return cleaned_data
