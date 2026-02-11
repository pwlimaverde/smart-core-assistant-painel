"""Formulários para o módulo de configurações."""

import re

from django import forms
from django.db.models import Q

from smart_core_assistant_painel.app.clientes.models import Contato
from smart_core_assistant_painel.app.evolution_sync.models import WhiteList


class WhiteListForm(forms.ModelForm[WhiteList]):
    """Formulário para cadastro e edição de números na whitelist."""

    class Meta:
        model = WhiteList
        fields = ["contact", "name", "phone_number", "active"]
        widgets = {
            "contact": forms.HiddenInput(),
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Nome do contato",
                    "class": "w-full",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "placeholder": "5588999999999",
                    "class": "w-full",
                }
            ),
            "active": forms.CheckboxInput(),
        }
        labels = {
            "contact": "Contato",
            "name": "Nome",
            "phone_number": "Telefone",
            "active": "Ativo",
        }
        help_texts = {
            "phone_number": "Formato: código do país + DDD + número (ex: 5588999141275)",
        }

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        contact_field = self.fields.get("contact")
        if isinstance(contact_field, forms.ModelChoiceField):
            contact_field.queryset = (
                Contato.objects.filter(telefone__isnull=False)
                .exclude(telefone="")
                .order_by("nome_contato", "telefone")
            )

    def clean_name(self) -> str:
        """Garante um nome válido, preferindo o nome do contato vinculado."""
        raw_name = str(self.cleaned_data.get("name", "") or "").strip()
        if raw_name:
            return raw_name

        contact = self._resolve_selected_contact()
        if contact:
            return self._resolve_contact_label(contact)

        raise forms.ValidationError("Nome é obrigatório.")

    def clean_phone_number(self) -> str:
        """Normaliza e valida o número de telefone."""
        contact = self._resolve_selected_contact()
        raw_phone: str = str(self.cleaned_data.get("phone_number", "") or "")

        if contact and contact.telefone:
            raw_phone = str(contact.telefone)

        # Remove caracteres não-numéricos
        phone = re.sub(r"\D", "", raw_phone)

        if not phone:
            raise forms.ValidationError("Número de telefone é obrigatório.")

        if len(phone) < 10 or len(phone) > 15:
            raise forms.ValidationError(
                "Número de telefone deve ter entre 10 e 15 dígitos."
            )

        # Validação básica de formato brasileiro
        if phone.startswith("55") and len(phone) not in [12, 13]:
            raise forms.ValidationError(
                "Número brasileiro deve ter 12 ou 13 dígitos "
                "(55 + DDD + número)."
            )

        # Verifica variações do número (com/sem 9º dígito)
        variations = self._get_phone_variations(phone)
        query = Q()
        for var in variations:
            query |= Q(phone_number=var)
        if self.instance and self.instance.pk:
            qs_var = WhiteList.objects.filter(query).exclude(
                pk=self.instance.pk
            )
        else:
            qs_var = WhiteList.objects.filter(query)

        if qs_var.exists():
            raise forms.ValidationError(
                "Este número (ou variação) já está cadastrado."
            )

        return phone

    def clean(self) -> dict[str, object]:
        """Sincroniza os dados quando houver contato vinculado."""
        cleaned_data = super().clean()
        contact = cleaned_data.get("contact")
        if isinstance(contact, Contato):
            if not str(cleaned_data.get("name", "") or "").strip():
                cleaned_data["name"] = self._resolve_contact_label(contact)
        return cleaned_data

    def _resolve_selected_contact(self) -> Contato | None:
        """Retorna o contato selecionado no formulário, quando existir."""
        contact = self.cleaned_data.get("contact")
        if isinstance(contact, Contato):
            return contact
        return None

    def _resolve_contact_label(self, contact: Contato) -> str:
        """Retorna um nome amigável para exibição/salvamento."""
        return (
            str(contact.nome_contato or "").strip()
            or str(contact.nome_perfil_whatsapp or "").strip()
            or str(contact.telefone or "").strip()
            or "Contato sem nome"
        )

    def _get_phone_variations(self, phone: str) -> list[str]:
        """Gera variações de telefone (com e sem 9 dígito)."""
        variations = [phone]
        if phone.startswith("55") and len(phone) in [12, 13]:
            if len(phone) == 13 and phone[4] == "9":
                variations.append(phone[:4] + phone[5:])
            elif len(phone) == 12:
                variations.append(phone[:4] + "9" + phone[4:])
        return variations
