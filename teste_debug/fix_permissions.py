import os
import sys

import django

# Setup do Django
sys.path.append(r"c:\PROJETOS\PYTHON\APPS\smart-core-assistant-painel\src")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_core_assistant_painel.app.core.settings")
django.setup()

from django.contrib.auth import get_user_model
from rolepermissions.roles import assign_role

from smart_core_assistant_painel.app.tenants.models import Tenant, TenantUser


def fix_permissions():
    """
    Script de correção de permissões:
    1. Cria TenantUser para owners que não têm.
    2. Garante module_permissions granular para todos os admins.
    """
    print("--- Iniciando Correção de Permissões ---")
    
    # Permissões completas para owners/admins
    all_perms = {
        "all": True,
        "clientes": {"view": True, "edit": True, "delete": True},
        "operacional": {"view": True, "edit": True, "delete": True},
        "treinamento": {"view": True, "edit": True, "delete": True},
        "atendimentos": {"view": True, "edit": True, "delete": True},
        "configuracoes": {"view": True, "edit": True, "delete": True},
    }
    
    tenants = Tenant.objects.filter(active=True)
    User = get_user_model()
    
    count_created = 0
    count_updated = 0
    
    for tenant in tenants:
        user = tenant.owner
        
        # 1. Garantir role Gerente (para acesso legado)
        try:
            assign_role(user, "gerente")
            print(f"[Role] Atribuído role 'gerente' para {user.email}")
        except Exception as e:
            print(f"[Role] Erro ao atribuir role para {user.email}: {e}")
            
        # 2. Criar ou Atualizar TenantUser
        tenant_user, created = TenantUser.objects.get_or_create(
            user=user,
            tenant=tenant,
            defaults={
                "role": "admin",
                "module_permissions": all_perms,
                "created_by": user
            }
        )
        
        if created:
            print(f"[TenantUser] CRIADO para {user.email} @ {tenant.slug}")
            count_created += 1
        else:
            # Atualizar permissões se estiver faltando a chave "all" ou for antigo
            if tenant_user.role == "admin":
                should_update = False
                if tenant_user.module_permissions.get("all") is not True:
                    should_update = True
                
                if should_update:
                    tenant_user.module_permissions = all_perms
                    tenant_user.save()
                    print(f"[TenantUser] ATUALIZADO permissões para {user.email} @ {tenant.slug}")
                    count_updated += 1
                else:
                    print(f"[TenantUser] OK para {user.email} @ {tenant.slug}")

    print("\n--- Concluído ---")
    print(f"Novos TenantUsers criados: {count_created}")
    print(f"TenantUsers atualizados: {count_updated}")

if __name__ == "__main__":
    fix_permissions()
