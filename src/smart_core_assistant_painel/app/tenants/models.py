import uuid
from typing import Any
import secrets
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import models
from django.utils import timezone

from .utils.encryption import decrypt_value, encrypt_value


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=100)
    api_key = models.CharField(
        max_length=100, unique=True, blank=True
    )  # Gerado auto

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenants",
    )

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    active = models.BooleanField(default=True)
    setup_completed = models.BooleanField(default=False)
    onboarding_step = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.api_key:
            self.api_key = str(uuid.uuid4().hex)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"


class TenantDatabase(models.Model):
    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="database_config"
    )

    host = models.CharField(max_length=255)
    port = models.IntegerField(default=5432)
    database_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255)

    # Armazena criptografado
    _password = models.CharField(db_column="password", max_length=500)

    ssl_mode = models.CharField(max_length=50, default="disable")

    connection_valid = models.BooleanField(default=False)
    last_check = models.DateTimeField(null=True, blank=True)
    schema_version = models.CharField(max_length=50, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    @property
    def password(self) -> str:
        return decrypt_value(self._password)

    @password.setter
    def password(self, value: str) -> None:
        self._password = encrypt_value(value)

    def get_connection_string(self) -> str:
        """Retorna connection URI para uso interno (SQLAlchemy/psycopg)."""
        pwd = self.password
        return f"postgresql://{self.username}:{pwd}@{self.host}:{self.port}/{self.database_name}"

    def __str__(self) -> str:
        return f"DB Config for {self.tenant.slug}"


class TenantEvolution(models.Model):
    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="evolution_config"
    )

    server_url = models.URLField()
    _api_key = models.CharField(db_column="api_key", max_length=500)

    instance_name = models.CharField(max_length=100, default="atendimento")
    connection_valid = models.BooleanField(default=False)
    last_check = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    @property
    def api_key(self) -> str:
        return decrypt_value(self._api_key)

    @api_key.setter
    def api_key(self, value: str) -> None:
        self._api_key = encrypt_value(value)

    def __str__(self) -> str:
        return f"Evolution Config for {self.tenant.slug}"


class TenantTrello(models.Model):
    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="trello_config"
    )

    # Credenciais criptografadas
    _api_key = models.CharField(db_column="api_key", max_length=500)
    _api_secret = models.CharField(db_column="api_secret", max_length=500)
    _token = models.CharField(db_column="token", max_length=500)

    # Workspace onde os boards serão criados
    workspace_id = models.CharField(max_length=100)

    # Webhook (gerenciado automaticamente)
    webhook_id = models.CharField(max_length=100, blank=True)
    webhook_callback_url = models.URLField(blank=True)

    connection_valid = models.BooleanField(default=False)
    last_check = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    @property
    def api_key(self) -> str:
        return decrypt_value(self._api_key)

    @api_key.setter
    def api_key(self, value: str) -> None:
        self._api_key = encrypt_value(value)

    @property
    def api_secret(self) -> str:
        return decrypt_value(self._api_secret)

    @api_secret.setter
    def api_secret(self, value: str) -> None:
        self._api_secret = encrypt_value(value)

    @property
    def token(self) -> str:
        return decrypt_value(self._token)

    @token.setter
    def token(self, value: str) -> None:
        self._token = encrypt_value(value)

    def __str__(self) -> str:
        return f"Trello Config for {self.tenant.slug}"


class TenantConfig(models.Model):
    """Configurações de IA e prompts do Tenant."""

    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="config"
    )

    # ===== PROMPTS EDITÁVEIS PELO CLIENTE =====

    # Dados da empresa
    dados_empresa = models.TextField(
        blank=True,
        default="",
        verbose_name="Dados da Empresa",
        help_text=(
            "Descreva sua empresa: nome, localização, produtos, serviços, "
            "missão, visão e valores. Essas informações serão usadas "
            "pelo bot para responder perguntas sobre a empresa."
        ),
    )

    # Persona do bot
    persona_bot = models.TextField(
        blank=True,
        default="",
        verbose_name="Persona do Bot",
        help_text=(
            "Defina a identidade do bot: nome, tom de voz, estilo de "
            "comunicação e como ele deve se apresentar aos clientes. "
            "Ex: 'Você é o Smart, assistente da Gráfica Ecoprint...'"
        ),
    )

    # ===== MENSAGENS AUTOMÁTICAS =====

    msg_fallback = models.CharField(
        max_length=500,
        blank=True,
        default="Recebemos sua mensagem. Em breve retornaremos.",
        verbose_name="Mensagem Fallback",
        help_text=(
            "Mensagem enviada quando o bot não consegue processar a "
            "mensagem do cliente."
        ),
    )

    msg_sem_info = models.CharField(
        max_length=500,
        blank=True,
        default="Desculpe, não encontrei informações sobre isso.",
        verbose_name="Mensagem Sem Informação",
        help_text=(
            "Mensagem enviada quando não há dados no treinamento "
            "para responder a pergunta do cliente."
        ),
    )

    msg_transferencia = models.CharField(
        max_length=500,
        blank=True,
        default="Vou transferir seu atendimento para o setor responsável.",
        verbose_name="Mensagem de Transferência",
        help_text=(
            "Mensagem enviada ao cliente quando o atendimento é "
            "transferido para um atendente humano."
        ),
    )

    # ===== EXTRAÇÃO DE ENTIDADES =====

    entity_types = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Tipos de Entidade",
        help_text=(
            "JSON com os tipos de entidade que o bot deve extrair das "
            "mensagens. Cada categoria define campos e descrições. "
            "Ex: produtos_servicos, dados_financeiros, etc."
        ),
    )

    # ===== CONFIGURAÇÕES AVANÇADAS (Admin apenas) =====

    # Configurações de LLM personalizadas por tenant
    # Se preenchido, tem prioridade sobre o CoreSettings
    llm_class = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Classe LLM",
        help_text=(
            "Classe do LLM a usar: ChatGroq, ChatOpenAI, ChatOllama. "
            "Se vazio, usa a configuração global."
        ),
    )

    model = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Modelo LLM",
        help_text=(
            "Modelo específico a usar, ex: llama-3.1-70b-versatile, "
            "gpt-4o, openai/gpt-4o-mini. Se vazio, usa a configuração global."
        ),
    )

    # API Keys do tenant (sobrescrevem CoreSettings se preenchidas)
    api_keys = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="API Keys do Tenant",
        help_text=(
            "API Keys específicas do tenant. Chaves válidas: "
            "groq_api_key, openai_api_key, huggingface_api_key. "
            "Se preenchido, sobrescreve as API Keys globais."
        ),
    )

    updated_at = models.DateTimeField(auto_now=True)

    # Branding e Configuração Regional
    brand_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nome da Marca",
        help_text="Nome exibido no painel (pode ser diferente da Razão Social)."
    )
    primary_color = models.CharField(max_length=7, default="#0d6efd", verbose_name="Cor Primária")
    secondary_color = models.CharField(max_length=7, default="#6c757d", verbose_name="Cor Secundária")
    timezone = models.CharField(max_length=50, default="America/Sao_Paulo", verbose_name="Fuso Horário")
    language_code = models.CharField(max_length=10, default="pt-br", verbose_name="Idioma")

    def __str__(self) -> str:
        return f"Config for {self.tenant.slug}"

    def set_api_key(self, service: str, key: str) -> None:
        """Helper para salvar API Key criptografada no JSON."""
        if not self.api_keys:
            self.api_keys = {}
        self.api_keys[service] = encrypt_value(key)

    def get_api_key(self, service: str) -> str:
        """Helper para recuperar API Key descriptografada do JSON."""
        if not self.api_keys:
            return ""
        encrypted = self.api_keys.get(service)
        return decrypt_value(encrypted) if encrypted else ""


class Plan(models.Model):
    """Planos comerciais do SaaS."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Limites
    max_instances = models.IntegerField(
        default=1,
        help_text="Máximo de instâncias Evolution. -1 para ilimitado",
    )
    max_departments = models.IntegerField(
        default=1, help_text="Máximo de departamentos. -1 para ilimitado"
    )

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Subscription(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "PENDING_PAYMENT", "Aguardando Pagamento"
        PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED", "Pagamento Confirmado"
        ACTIVE = "ACTIVE", "Active"
        PAST_DUE = "PAST_DUE", "Past Due"
        SUSPENDED = "SUSPENDED", "Suspended"
        CANCELLED = "CANCELLED", "Cancelled"

    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="subscription"
    )

    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )

    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)

    payment_gateway = models.CharField(
        max_length=50, blank=True, help_text="Ex: asaas, stripe"
    )
    external_customer_id = models.CharField(max_length=100, blank=True)
    external_subscription_id = models.CharField(max_length=100, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def is_active(self) -> bool:
        if self.status in (self.Status.ACTIVE, self.Status.PAST_DUE):
            if not self.current_period_end:
                return True
            return self.current_period_end > timezone.now()
        return False

    def extend_period(self, months: int) -> None:
        """Estende o período da assinatura por X meses."""
        base_date = self.current_period_end or timezone.now()
        if base_date < timezone.now():
            base_date = timezone.now()

        self.current_period_end = base_date + relativedelta(months=months)
        if not self.current_period_start:
            self.current_period_start = timezone.now()

        self.status = self.Status.ACTIVE
        self.save()

    def set_manual_period(self, start_date, end_date) -> None:
        """Define um período manual para a assinatura."""
        self.current_period_start = start_date
        self.current_period_end = end_date
        self.status = self.Status.ACTIVE
        self.save()

    def __str__(self) -> str:
        return (
            f"Subscription {self.plan} ({self.status}) for {self.tenant.slug}"
        )


class PaymentRecord(models.Model):
    class PaymentMethod(models.TextChoices):
        PIX = "PIX", "Pix"
        TRANSFER = "TRANSFER", "Transferência"
        CASH = "CASH", "Dinheiro"
        BOLETO = "BOLETO", "Boleto"
        OTHER = "OTHER", "Outro"

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(
        max_length=20, choices=PaymentMethod.choices
    )

    # Período coberto por este pagamento
    period_start = models.DateField()
    period_end = models.DateField()

    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return (
            f"Payment {self.id} - {self.tenant.name} - "
            f"{self.amount} ({self.payment_date})"
        )


class TenantInvite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="invites"
    )

    # Dados do funcionário
    email = models.EmailField()
    name = models.CharField(max_length=100)

    # Permissões pré-definidas
    role = models.CharField(
        max_length=20,
        choices=[
            ("admin", "Administrador"),
            ("manager", "Gerente"),
            ("staff", "Funcionário"),
            ("viewer", "Visualizador"),
        ],
        default="staff",
    )
    module_permissions = models.JSONField(default=dict, blank=True)

    # Token único para ativação
    token = models.CharField(max_length=64, unique=True, editable=False)

    # Controle de validade
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.token:
            self.token = secrets.token_urlsafe(48)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_valid(self) -> bool:
        return not self.used and self.expires_at > timezone.now()

    class Meta:
        verbose_name = "Convite de Tenant"
        verbose_name_plural = "Convites de Tenant"

    def __str__(self) -> str:
        return f"Convite para {self.email} @ {self.tenant.slug}"


class TenantUser(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_profile",
    )
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="members"
    )

    role = models.CharField(
        max_length=20,
        choices=[
            ("admin", "Administrador"),
            ("manager", "Gerente"),
            ("staff", "Funcionário"),
            ("viewer", "Visualizador"),
        ],
        default="staff",
    )

    module_permissions = models.JSONField(
        default=dict,
        blank=True,
        help_text="{modulo: {view: bool, edit: bool, delete: bool}}",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tenant_users",
    )

    class Meta:
        verbose_name = "Funcionário do Tenant"
        verbose_name_plural = "Funcionários do Tenant"

    def __str__(self) -> str:
        return f"{self.user.email} @ {self.tenant.slug} ({self.role})"

    def has_module_permission(self, module: str, action: str = "view") -> bool:
        if self.role == "admin":
            return True
        # Suporte para permissão universal
        if self.module_permissions.get("all") is True:
            return True
        perms = self.module_permissions.get(module, {})
        return perms.get(action, False)
