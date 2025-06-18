
import json
import re

from django.core.exceptions import ValidationError
from django.db import models


def validate_tag(value):
    """
    Valida se a tag está em minúsculo, sem espaços e com no máximo 40 caracteres
    """
    if len(value) > 40:
        raise ValidationError('Tag deve ter no máximo 40 caracteres.')

    if ' ' in value:
        raise ValidationError('Tag não deve conter espaços.')

    if not value.islower():
        raise ValidationError('Tag deve conter apenas letras minúsculas.')

    # Opcional: validar se contém apenas letras, números e underscore
    if not re.match(r'^[a-z0-9_]+$', value):
        raise ValidationError(
            'Tag deve conter apenas letras minúsculas, números e underscore.')


class Treinamentos(models.Model):
    tag: models.TextField = models.TextField(
        max_length=40,
        validators=[validate_tag],
        blank=False,
        null=False,
        help_text="Campo obrigatório para identificar o treinamento")
    grupo: models.TextField = models.TextField(
        max_length=40,
        validators=[validate_tag],
        blank=False,
        null=False,
        help_text="Campo obrigatório para identificar o grupo do treinamento")
    documento: models.JSONField = models.JSONField(
        default=dict, blank=True, null=True)
    treinamento_finalizado: models.BooleanField = models.BooleanField(
        default=False,)

    @property
    def conteudo(self):
        """
        Retorna o conteúdo do campo documento como dicionário
        """
        if self.documento:
            if isinstance(self.documento, str):
                try:
                    return json.loads(self.documento)
                except json.JSONDecodeError:
                    return {}
            elif isinstance(self.documento, dict):
                return self.documento
        return {}

    def save(self, *args, **kwargs):
        """
        Executa validação OBRIGATÓRIA antes de qualquer salvamento
        """
        # Valida o campo tag especificamente
        if self.tag:
            validate_tag(self.tag)

        # Executa todas as validações do modelo
        self.full_clean()

        # Só salva se passou em todas as validações
        super().save(*args, **kwargs)

    def clean(self):
        """
        Validação adicional no nível do modelo
        """
        super().clean()
        if self.tag:
            validate_tag(self.tag)

    def __str__(self):
        return str(self.tag) if self.tag else f"Treinamento {self.id}"

    class Meta:
        verbose_name = "Treinamento"
        verbose_name_plural = "Treinamentos"
