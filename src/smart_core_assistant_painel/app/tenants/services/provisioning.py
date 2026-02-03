from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..models import Tenant, TenantConfig, TenantUser, Subscription, Plan

User = get_user_model()


class TenantProvisioningService:
    @staticmethod
    @transaction.atomic
    @staticmethod
    @transaction.atomic
    def create_and_activate_tenant(
        onboarding_data: dict,
        plan_id: int,
        config_data: dict,
    ) -> str:
        """
        Fluxo completo: Finaliza a configuração e ativa o tenant.
        Agora suporta retomada de tenant pré-criado no Step 1.
        """
        required_fields = [
            "company_name",
            "slug",
            "admin_name",
            "admin_email",
        ]
        # remove admin_password pois o usuario ja pode existir

        missing = [
            field
            for field in required_fields
            if not onboarding_data.get(field)
        ]
        if missing:
            raise ValueError(
                f"Dados incompletos do onboarding: {', '.join(missing)}"
            )

        email = onboarding_data["admin_email"]
        slug = onboarding_data["slug"]

        # 1. Recuperar Usuário Existente ou Criar
        user = User.objects.filter(email=email).first()
        if not user:
            # Só valida password se for criar
            if not onboarding_data.get("admin_password"):
                raise ValueError("Senha é obrigatória para novos usuários.")

            user = User.objects.create_user(
                username=email,
                email=email,
                password=onboarding_data["admin_password"],
                first_name=onboarding_data["admin_name"].split()[0],
                is_active=False,
            )

        # 2. Recuperar Tenant Existente ou Criar
        tenant = Tenant.objects.filter(slug=slug).first()
        if not tenant:
            tenant = Tenant.objects.create(
                name=onboarding_data["company_name"],
                slug=slug,
                owner=user,
                email=email,
                phone=onboarding_data.get("admin_phone", ""),
                active=False,
                setup_completed=False,
                onboarding_step=4,
            )
        else:
            # Atualiza dados finais
            tenant.onboarding_step = 4
            tenant.save()

        # 3. Garantir Assinatura e Configuração
        subscription, _ = Subscription.objects.get_or_create(
            tenant=tenant,
            defaults={"status": Subscription.Status.PENDING_PAYMENT},
        )
        plan = Plan.objects.get(id=plan_id)
        subscription.plan = plan
        subscription.status = Subscription.Status.PENDING_PAYMENT
        subscription.save()

        config, _ = TenantConfig.objects.get_or_create(tenant=tenant)
        config.brand_name = config_data.get("brand_name", "")
        config.primary_color = config_data.get("primary_color", "#0d6efd")
        config.secondary_color = config_data.get("secondary_color", "#6c757d")
        config.timezone = config_data.get("timezone", "America/Sao_Paulo")
        config.language_code = config_data.get("language_code", "pt-br")
        config.save()

        return TenantProvisioningService.activate_tenant(tenant)

    @staticmethod
    @transaction.atomic
    def create_initial_tenant(data: dict) -> Tenant:
        """
        Etapa 1: Cria dados iniciais do Tenant e Usuário.
        Retorna o objeto Tenant criado (inativo).

        Logica de Resiliência:
        - Se tenant/usuário já existe e está pendente (setup_completed=False),
          retorna o ID existente para retomar o fluxo.
        """
        email = data["admin_email"]
        slug = data["slug"]

        # Verificar existência prévia
        existing_user = User.objects.filter(email=email).first()
        existing_tenant = Tenant.objects.filter(slug=slug).first()

        # Cenário 1: Tenant já concluído (Impedir duplicidade real)
        if existing_tenant and existing_tenant.setup_completed:
            raise ValueError(
                "Este domínio já está em uso por uma conta ativa."
            )

        if existing_user:
            # Se usuário existe, verifica se tem tenant associado
            user_tenant = Tenant.objects.filter(owner=existing_user).first()
            if user_tenant and user_tenant.setup_completed:
                raise ValueError("Já existe uma conta ativa para este e-mail.")

            # Se existe mas está pendente, vamos reusar (Resumption)
            # Se usuário existe mas tenant não (estado inconsistente?), criamos o tenant

        # 1. Recuperar ou criar Usuário (Dono)
        if not existing_user:
            # Cria usuário inativo aguardando ativação final
            user = User.objects.create_user(
                username=email,
                email=email,
                password=data["admin_password"],
                first_name=data["admin_name"].split()[0],
                is_active=False,
            )
        else:
            user = existing_user

        # 2. Criar ou Recuperar Tenant
        if existing_tenant:
            tenant = existing_tenant
            # Atualiza campos básicos caso o usuário tenha corrigido algo no form (opcional)
            tenant.name = data["company_name"]
            if tenant.owner != user:
                # Edge case: slug existe mas dono é outro (conflito de slug real)
                # Mas como filtramos por slug lá, cima, aqui assumimos que é o mesmo contexto
                # Se e-mail for diferente, seria um problema.
                # Simplificação: Se slug existe e owner é diferente, erro.
                raise ValueError("Este domínio (slug) já está reservado.")
            tenant.save()
        else:
            # Verifica se usuário já tem outro tenant pendente
            user_pending_tenant = Tenant.objects.filter(
                owner=user, setup_completed=False
            ).first()
            if user_pending_tenant:
                # Usuário tentou mudar o slug? Vamos atualizar o slug do existente
                tenant = user_pending_tenant
                tenant.slug = slug
                tenant.name = data["company_name"]
                tenant.save()
            else:
                tenant = Tenant.objects.create(
                    name=data["company_name"],
                    slug=data["slug"],
                    owner=user,
                    active=False,  # Inativo até finalização
                    setup_completed=False,
                    onboarding_step=2,  # Próximo passo: Pagamento
                )

        # 3. Garantir Assinatura e Configuração
        # O signal create_tenant_subscription já cria, mas garantimos com get_or_create
        subscription, _ = Subscription.objects.get_or_create(
            tenant=tenant,
            defaults={
                "status": Subscription.Status.PENDING_PAYMENT,
                "plan": None,
            },
        )

        TenantConfig.objects.get_or_create(tenant=tenant)

        return tenant.id

    @staticmethod
    def update_plan(tenant: Tenant, plan_id: int) -> None:
        """
        Etapa 2: Atualiza o plano escolhido na assinatura.
        """
        plan = Plan.objects.get(id=plan_id)
        subscription = tenant.subscription
        subscription.plan = plan
        subscription.save()

        tenant.onboarding_step = 3
        tenant.save()

    @staticmethod
    def update_config(tenant: Tenant, data: dict) -> None:
        """
        Etapa 3: Salva configurações iniciais (branding, regional).
        """
        config = tenant.config
        config.brand_name = data.get("brand_name", "")
        config.primary_color = data.get("primary_color", "#0d6efd")
        config.secondary_color = data.get("secondary_color", "#6c757d")
        config.timezone = data.get("timezone", "America/Sao_Paulo")
        config.language_code = data.get("language_code", "pt-br")
        config.save()

        tenant.onboarding_step = 4
        tenant.save()

    @staticmethod
    @transaction.atomic
    def activate_tenant(tenant: Tenant) -> str:
        """
        Etapa 4: Finalização e Ativação.
        - Ativa Tenant, User e Subscription.
        - Cria TenantUser admin.
        - Retorna URL de redirecionamento.
        """
        from django.conf import settings

        # 1. Ativação
        tenant.active = True
        tenant.setup_completed = True  # Processo concluído
        tenant.onboarding_step = 4
        tenant.save()

        tenant.subscription.status = Subscription.Status.ACTIVE
        tenant.subscription.current_period_start = timezone.now()
        tenant.subscription.save()

        user = tenant.owner
        user.is_active = True
        user.save()

        # 2. Permissão de Admin no Tenant
        if not TenantUser.objects.filter(tenant=tenant, user=user).exists():
            TenantUser.objects.create(
                user=user,
                tenant=tenant,
                role="admin",
                # Atribuir permissão explícita para todos os módulos disponíveis
                module_permissions={
                    "all": True,  # Mantem compatibilidade
                    "clientes": {"view": True, "edit": True, "delete": True},
                    "operacional": {
                        "view": True,
                        "edit": True,
                        "delete": True,
                    },
                    "treinamento": {
                        "view": True,
                        "edit": True,
                        "delete": True,
                    },
                    "atendimentos": {
                        "view": True,
                        "edit": True,
                        "delete": True,
                    },
                    "configuracoes": {
                        "view": True,
                        "edit": True,
                        "delete": True,
                    },
                },
            )

        # 3. Gerar URL de Redirecionamento para Login
        domain = getattr(
            settings, "TENANT_BASE_DOMAIN", "smartcoreassistant.com.br"
        )
        protocol = "https" if not settings.DEBUG else "http"

        # Redireciona para login no subdomínio do tenant
        return f"{protocol}://{tenant.slug}.{domain}/usuarios/login/"
