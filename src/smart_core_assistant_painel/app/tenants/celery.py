from celery import Task
from loguru import logger


class TenantTask(Task):
    """Base class para tasks que operam em dados de tenant.

    Esta classe garante que o contexto do tenant (configurado via threading.local
    no middleware) seja replicado na execução do worker do Celery.

    Além do contexto do tenant, também carrega o RuntimeConfig (via ConfigLoader)
    para que as configurações de prompts, LLM e API keys estejam disponíveis.

    Requisitos:
    1. A task deve ser decorada com @shared_task(base=TenantTask)
    2. A task DEVE receber 'tenant_slug' como PRIMEIRO argumento.
    """

    def __call__(self, *args, **kwargs):
        # Lazy imports para evitar ciclo circular no carregamento
        from .middleware import clear_current_tenant, set_current_tenant
        from .models import Tenant
        from .services.config_loader import ConfigLoader

        # Tenta extrair tenant_slug dos argumentos
        tenant_slug = None

        # 1. Tenta pegar do primeiro argumento posicional
        if args:
            potential_slug = args[0]
            if isinstance(potential_slug, str):
                tenant_slug = potential_slug

        # 2. Se não achou, tenta pegar dos kwargs
        if not tenant_slug:
            tenant_slug = kwargs.get("tenant_slug")

        # Configura o contexto se houver slug
        context_set = False
        tenant = None
        try:
            if tenant_slug and isinstance(tenant_slug, str):
                try:
                    tenant = Tenant.objects.filter(slug=tenant_slug).first()
                    if tenant:
                        set_current_tenant(tenant)
                        context_set = True
                        logger.debug(
                            f"Celery: Tenant '{tenant_slug}' configurado "
                            f"para task {self.name}"
                        )
                    else:
                        logger.warning(
                            f"Celery: Tenant '{tenant_slug}' não encontrado "
                            f"ao executar task {self.name}"
                        )
                except Exception as e:
                    logger.error(
                        f"Celery: Erro ao configurar tenant '{tenant_slug}': {e}"
                    )

            # Carrega o RuntimeConfig (Core + Tenant) no ContextVar
            # Isso é equivalente ao que o TenantConfigMiddleware faz para requests
            try:
                ConfigLoader.load_for_request(tenant)
                logger.debug(
                    f"Celery: RuntimeConfig carregado para task {self.name}"
                )
            except Exception as e:
                logger.error(
                    f"Celery: Erro ao carregar RuntimeConfig para task "
                    f"{self.name}: {e}"
                )

            # Executa a task original
            return super().__call__(*args, **kwargs)

        finally:
            # Limpeza garantida do contexto
            if context_set:
                clear_current_tenant()
