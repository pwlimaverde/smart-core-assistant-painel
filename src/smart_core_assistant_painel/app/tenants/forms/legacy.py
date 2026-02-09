from dateutil.relativedelta import relativedelta
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ..models import (
    PaymentRecord,
    Plan,
    Tenant,
    TenantConfig,
    TenantDatabase,
    TenantEvolution,
    TenantTrello,
)


class TenantSignupForm(forms.Form):
    """Formulário para cadastro de novo usuário e tenant."""

    # Dados do Usuário
    full_name = forms.CharField(label=_("Nome Completo"), max_length=150)
    email = forms.EmailField(label=_("E-mail"), max_length=254)
    password = forms.CharField(
        label=_("Senha"), widget=forms.PasswordInput, min_length=8
    )

    # Dados do Tenant (Empresa)
    company_name = forms.CharField(label=_("Nome da Empresa"), max_length=100)
    slug = forms.SlugField(
        label=_("Identificador (Slug)"),
        help_text=_("Usado na URL (ex: minha-empresa)"),
    )

    # Plano
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(active=True),
        label=_("Plano Desejado"),
        empty_label=None,
    )

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("Este e-mail já está em uso."))
        return email

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        if Tenant.objects.filter(slug=slug).exists():
            raise ValidationError(_("Este identificador já está em uso."))
        return slug


class TenantEvolutionForm(forms.ModelForm):
    """Formulário para configuração da Evolution API."""

    api_key = forms.CharField(
        widget=forms.PasswordInput(render_value=True), label=_("API Key")
    )

    class Meta:
        model = TenantEvolution
        fields = ["server_url", "instance_name"]
        widgets = {
            "server_url": forms.URLInput(
                attrs={"placeholder": "https://api.seuserver.com"}
            ),
            "instance_name": forms.TextInput(
                attrs={"placeholder": "atendimento"}
            ),
        }

    def save(self, commit: bool = True) -> TenantEvolution:
        instance = super().save(commit=False)
        instance.api_key = self.cleaned_data["api_key"]
        if commit:
            instance.save()
        return instance


class TenantTrelloForm(forms.ModelForm):
    """Formulário para configuração do Trello."""

    api_key = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        label=_("API Key"),
        help_text=_("Obtenha em https://trello.com/app-key"),
    )
    api_secret = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        label=_("API Secret"),
        help_text=_("Obtenha na mesma página da API Key"),
    )
    token = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        label=_("Token"),
        help_text=_("Gere clicando em 'Token' na página da API Key"),
    )

    class Meta:
        model = TenantTrello
        fields = ["workspace_id"]
        labels = {
            "workspace_id": _("Workspace ID"),
        }
        help_texts = {
            "workspace_id": _(
                "ID do Workspace do Trello. Os boards são criados "
                "automaticamente ao cadastrar fluxos."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance._api_key:
                self.fields["api_key"].initial = self.instance.api_key
            if self.instance._api_secret:
                self.fields["api_secret"].initial = self.instance.api_secret
            if self.instance._token:
                self.fields["token"].initial = self.instance.token

    def save(self, commit: bool = True) -> TenantTrello:
        instance = super().save(commit=False)
        instance.api_key = self.cleaned_data["api_key"]
        instance.api_secret = self.cleaned_data["api_secret"]
        instance.token = self.cleaned_data["token"]
        if commit:
            instance.save()
        return instance


class TenantConfigForm(forms.ModelForm):
    """Formulário para configurações de IA e prompts do cliente."""

    # Campo customizado para editar JSON como texto
    entity_types_json = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 15,
                "placeholder": '{"entity_types": {"categoria": {"campo": "descrição"}}}',
                "style": "font-family: monospace;",
            }
        ),
        required=False,
        label="Tipos de Entidade (JSON)",
        help_text=(
            "JSON com os tipos de entidade que o bot deve extrair das "
            "mensagens dos clientes. Cada categoria define campos e suas "
            "descrições para orientar a extração."
        ),
    )

    class Meta:
        model = TenantConfig
        fields = [
            "dados_empresa",
            "persona_bot",
            "msg_fallback",
            "msg_sem_info",
            "msg_transferencia",
        ]
        widgets = {
            "dados_empresa": forms.Textarea(
                attrs={
                    "rows": 10,
                    "placeholder": (
                        "Ex: A Empresa XYZ, fundada em 2010, é especializada "
                        "em soluções tecnológicas. Nossos principais produtos "
                        "incluem software de gestão, consultoria em TI..."
                    ),
                }
            ),
            "persona_bot": forms.Textarea(
                attrs={
                    "rows": 8,
                    "placeholder": (
                        "Ex: Você é o Max, assistente virtual da Empresa XYZ. "
                        "Seu tom é profissional mas amigável. Você responde "
                        "com clareza e objetividade..."
                    ),
                }
            ),
            "msg_fallback": forms.TextInput(
                attrs={
                    "placeholder": "Recebemos sua mensagem. Em breve retornaremos."
                }
            ),
            "msg_sem_info": forms.TextInput(
                attrs={
                    "placeholder": "Desculpe, não encontrei informações sobre isso."
                }
            ),
            "msg_transferencia": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Vou transferir seu atendimento para o setor responsável."
                    )
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Preencher o campo JSON com o valor atual do modelo
        if self.instance and self.instance.pk and self.instance.entity_types:
            import json

            self.fields["entity_types_json"].initial = json.dumps(
                self.instance.entity_types, ensure_ascii=False, indent=2
            )

    def clean_entity_types_json(self):
        """Valida e converte o JSON de entity_types."""
        import json

        value = self.cleaned_data.get("entity_types_json", "")
        if not value or not value.strip():
            return {}
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise forms.ValidationError(
                f"JSON inválido: {e}. Verifique a sintaxe do JSON."
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Salvar o entity_types parseado no modelo
        instance.entity_types = self.cleaned_data.get("entity_types_json", {})
        if commit:
            instance.save()
        return instance


class TenantDatabaseForm(forms.ModelForm):
    """Formulário para configuração do PostgreSQL do Tenant."""

    password = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        label=_("Senha"),
        help_text=_("Senha do banco de dados"),
        required=False,
    )

    class Meta:
        model = TenantDatabase
        fields = ["host", "port", "database_name", "username", "ssl_mode"]
        widgets = {
            "host": forms.TextInput(
                attrs={"placeholder": "192.168.1.100 ou db.exemplo.com"}
            ),
            "port": forms.NumberInput(attrs={"placeholder": "5432"}),
            "database_name": forms.TextInput(
                attrs={"placeholder": "smartcore_db"}
            ),
            "username": forms.TextInput(attrs={"placeholder": "smartcore"}),
            "ssl_mode": forms.Select(
                choices=[
                    ("disable", "Desabilitado"),
                    ("allow", "Permitir"),
                    ("prefer", "Preferir"),
                    ("require", "Requerido"),
                ]
            ),
        }
        labels = {
            "host": _("Host"),
            "port": _("Porta"),
            "database_name": _("Nome do Banco"),
            "username": _("Usuário"),
            "ssl_mode": _("Modo SSL"),
        }

    def save(self, commit: bool = True) -> TenantDatabase:
        instance = super().save(commit=False)
        if self.cleaned_data.get("password"):
            instance.password = self.cleaned_data["password"]
        if commit:
            instance.save()
        return instance


class RegisterPaymentForm(forms.ModelForm):
    months = forms.IntegerField(
        min_value=1, max_value=24, initial=1, label=_("Meses Contratados")
    )

    class Meta:
        model = PaymentRecord
        fields = ["amount", "payment_date", "payment_method", "notes"]
        widgets = {
            "payment_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "amount": _("Valor (R$)"),
            "payment_date": _("Data do Pagamento"),
            "payment_method": _("Método de Pagamento"),
            "notes": _("Observações"),
        }

    def clean(self):
        cleaned_data = super().clean()
        payment_date = cleaned_data.get("payment_date")
        months = cleaned_data.get("months")

        if payment_date and months:
            # Calculate period
            period_start = payment_date
            period_end = period_start + relativedelta(months=months)
            cleaned_data["period_start"] = period_start
            cleaned_data["period_end"] = period_end

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.period_start = self.cleaned_data["period_start"]
        instance.period_end = self.cleaned_data["period_end"]
        if commit:
            instance.save()
        return instance
