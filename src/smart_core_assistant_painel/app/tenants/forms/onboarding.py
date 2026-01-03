from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re

from ..models import Tenant, Plan, TenantConfig

User = get_user_model()


class TenantRegistrationForm(forms.Form):
    """
    Etapa 1: Dados Cadastrais e Administrador Inicial.
    """
    # Tenant
    company_name = forms.CharField(
        label=_("Nome da Empresa"),
        max_length=100,
        widget=forms.TextInput(attrs={
            "placeholder": "Ex: Minha Empresa Ltda",
            "class": "form-control"
        })
    )
    slug = forms.SlugField(
        label=_("Subdomínio Desejado"),
        help_text=_("O endereço será https://[slug].smartcoreassistant.com.br"),
        widget=forms.TextInput(attrs={
            "placeholder": "minhaempresa", 
            "class": "form-control",
            "data-slug-check-url": "/api/onboarding/check-slug/"  # Para JS
        })
    )
    
    # User Admin
    admin_name = forms.CharField(
        label=_("Seu Nome Completo"),
        max_length=150,
        widget=forms.TextInput(attrs={
            "placeholder": "Ex: João Silva",
            "class": "form-control"
        })
    )
    admin_email = forms.EmailField(
        label=_("Seu E-mail Corporativo"),
        widget=forms.EmailInput(attrs={
            "placeholder": "joao@empresa.com",
            "class": "form-control"
        })
    )
    admin_password = forms.CharField(
        label=_("Crie sua Senha"),
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        help_text=_("Mínimo de 8 caracteres.")
    )
    admin_phone = forms.CharField(
        label=_("Telefone/WhatsApp"),
        max_length=20,
        widget=forms.TextInput(attrs={
            "placeholder": "(11) 99999-9999",
            "class": "form-control phone-mask"
        })
    )

    def clean_slug(self):
        slug = self.cleaned_data["slug"].lower()
        if not re.match(r'^[a-z0-9-]+$', slug):
            raise ValidationError(_(
                "O slug deve conter apenas letras minúsculas, números e hífens."
            ))
        
        # Validar palavras reservadas
        reserved = [
            'admin', 'api', 'www', 'app', 'painel', 'dashboard',
            'public', 'static', 'media', 'tenant', 'setup'
        ]
        if slug in reserved:
            raise ValidationError(_("Este subdomínio não pode ser utilizado."))

        if Tenant.objects.filter(slug=slug).exists():
            raise ValidationError(_("Este subdomínio já está em uso."))
        return slug

    def clean_admin_email(self):
        email = self.cleaned_data["admin_email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("Este e-mail já está cadastrado no sistema."))
        return email


class PlanSelectionForm(forms.Form):
    """
    Etapa 2: Seleção de Plano.
    """
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(active=True),
        widget=forms.RadioSelect(attrs={"class": "plan-selector"}),
        empty_label=None,
        label=_("Escolha seu Plano")
    )


class TenantConfigForm(forms.ModelForm):
    """
    Etapa 3: Configuração Inicial.
    """
    primary_color = forms.CharField(
        label=_("Cor Primária"),
        widget=forms.TextInput(attrs={
            "type": "color",
            "class": "form-control form-control-color"
        }),
        initial="#0d6efd"
    )
    secondary_color = forms.CharField(
        label=_("Cor Secundária"),
        widget=forms.TextInput(attrs={
            "type": "color",
            "class": "form-control form-control-color"
        }),
        initial="#6c757d"
    )

    class Meta:
        model = TenantConfig
        fields = ["brand_name", "language_code", "timezone"]
        widgets = {
            "brand_name": forms.TextInput(attrs={"class": "form-control"}),
            "language_code": forms.Select(attrs={"class": "form-select"}),
            "timezone": forms.Select(attrs={"class": "form-select"}),
        }
