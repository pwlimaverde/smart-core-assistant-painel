from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re

from ..models import Tenant, Plan, TenantConfig

INPUT_BASE_CLASS = (
    "block w-full rounded-xl border-0 bg-stone-900/50 py-3.5 px-4 "
    "text-white ring-1 ring-inset ring-white/10 "
    "placeholder:text-stone-600 focus:ring-2 focus:ring-inset "
    "focus:ring-[#a98f71] sm:text-sm sm:leading-6 transition-all shadow-inner"
)
COLOR_INPUT_CLASS = (
    "h-11 w-14 rounded-lg border border-white/10 bg-stone-900/60 "
    "p-1 text-white"
)

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
            "class": INPUT_BASE_CLASS,
        })
    )
    slug = forms.SlugField(
        label=_("Subdomínio Desejado"),
        help_text=_("O endereço será https://[slug].smartcoreassistant.com.br"),
        widget=forms.TextInput(attrs={
            "placeholder": "minhaempresa",
            "class": INPUT_BASE_CLASS,
            "data-slug-check-url": "/tenants/api/onboarding/check-slug/"  # Para JS
        })
    )
    
    # User Admin
    admin_name = forms.CharField(
        label=_("Seu Nome Completo"),
        max_length=150,
        widget=forms.TextInput(attrs={
            "placeholder": "Ex: João Silva",
            "class": INPUT_BASE_CLASS,
        })
    )
    admin_email = forms.EmailField(
        label=_("Seu E-mail Corporativo"),
        widget=forms.EmailInput(attrs={
            "placeholder": "joao@empresa.com",
            "class": INPUT_BASE_CLASS,
        })
    )
    admin_password = forms.CharField(
        label=_("Crie sua Senha"),
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": INPUT_BASE_CLASS}),
        help_text=_("Mínimo de 8 caracteres.")
    )
    admin_phone = forms.CharField(
        label=_("Telefone/WhatsApp"),
        max_length=20,
        widget=forms.TextInput(attrs={
            "placeholder": "(11) 99999-9999",
            "class": f"{INPUT_BASE_CLASS} phone-mask",
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


class OnboardingConfigForm(forms.ModelForm):
    """
    Etapa 3: Configuração Inicial (usado apenas no Onboarding Wizard).
    """
    primary_color = forms.CharField(
        label=_("Cor Primária"),
        widget=forms.TextInput(attrs={
            "type": "color",
            "class": COLOR_INPUT_CLASS,
        }),
        initial="#0d6efd"
    )
    secondary_color = forms.CharField(
        label=_("Cor Secundária"),
        widget=forms.TextInput(attrs={
            "type": "color",
            "class": COLOR_INPUT_CLASS,
        }),
        initial="#6c757d"
    )

    class Meta:
        model = TenantConfig
        fields = ["brand_name", "language_code", "timezone"]
        widgets = {
            "brand_name": forms.TextInput(attrs={"class": INPUT_BASE_CLASS}),
            "language_code": forms.HiddenInput(),
            "timezone": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Defaults
        self.fields["language_code"].initial = "pt-br"
        self.fields["timezone"].initial = "America/Fortaleza"

