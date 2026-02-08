"""Formulários para o módulo de configurações."""

import re

from django import forms
from django.db.models import Q

from smart_core_assistant_painel.app.evolution_sync.models import WhiteList


class WhiteListForm(forms.ModelForm[WhiteList]):
    """Formulário para cadastro e edição de números na whitelist."""

    class Meta:
        model = WhiteList
        fields = ["name", "phone_number", "active"]
        widgets = {
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
            "name": "Nome",
            "phone_number": "Telefone",
            "active": "Ativo",
        }
        help_texts = {
            "phone_number": "Formato: código do país + DDD + número (ex: 5588999141275)",
        }

    def clean_phone_number(self) -> str:
        """Normaliza e valida o número de telefone."""
        phone: str = self.cleaned_data.get("phone_number", "")
        # Remove caracteres não-numéricos
        phone = re.sub(r"\D", "", phone)

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

        # Verifica duplicata (exceto no caso de edição do mesmo registro)
        qs = WhiteList.objects.filter(phone_number=phone)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

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

    def _get_phone_variations(self, phone: str) -> list[str]:
        """Gera variações de telefone (com e sem 9 dígito)."""
        variations = [phone]
        if phone.startswith("55") and len(phone) in [12, 13]:
            if len(phone) == 13 and phone[4] == "9":
                variations.append(phone[:4] + phone[5:])
            elif len(phone) == 12:
                variations.append(phone[:4] + "9" + phone[4:])
        return variations
