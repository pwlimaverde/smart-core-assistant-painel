from django.db import models
from django.utils.translation import gettext_lazy as _

from smart_core_assistant_painel.app.tenants.utils.encryption import (
    decrypt_value,
)


class CoreSettings(models.Model):
    """
    Armazena configurações globais do sistema (Core).
    Substitui o Firebase Remote Config.
    """

    key = models.CharField(
        _("Chave"),
        max_length=255,
        unique=True,
        help_text=_(
            "Chave identificadora da configuração (ex: OPENAI_API_KEY)."
        ),
    )
    value = models.TextField(_("Valor"), help_text=_("Valor da configuração."))
    encrypted = models.BooleanField(
        _("Criptografado"),
        default=False,
        help_text=_(
            "Se marcado, o valor será descriptografado ao ser acessado via get_value()."
        ),
    )
    description = models.TextField(
        _("Descrição"), blank=True, help_text=_("Descrição para documentação.")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Configuração Global")
        verbose_name_plural = _("Configurações Globais")
        ordering = ["key"]

    def __str__(self):
        return f"{self.key} ({'Encrypted' if self.encrypted else 'Plain'})"

    def get_value(self) -> str:
        """
        Retorna o valor da configuração.
        Se self.encrypted for True, tenta descriptografar.
        """
        if self.encrypted and self.value:
            try:
                return decrypt_value(self.value)
            except Exception:
                # Log error elsewhere?
                # For resilience, return value as is or raise?
                # Given strict requirements, maybe raise or let caller handle.
                # Here we assume decrypt_value raises if fails.
                # If we want to return raw if fail (e.g. bad key), we could catch.
                # But decrypt_value already catches and re-raises in utils.
                # Let's assume the stored value IS encrypted if flag is True.
                raise
        return self.value
