import re
from typing import Any, List, Optional

from django.core.exceptions import ValidationError
from django.db import models
from loguru import logger

from .models_departamento import Departamento


def validate_identificador(value: str) -> None:
    """Valida se o identificador está em formato válido.

    O identificador deve estar em minúsculo, sem espaços, com no máximo 40 caracteres
    e conter apenas letras minúsculas, números e underscore.

    Args:
        value (str): Valor do identificador a ser validado

    Raises:
        ValidationError: Se o identificador não atender aos critérios de validação

    Examples:
        >>> validate_identificador("minha_tag_123")  # válida
        >>> validate_identificador("MinhaTag")       # inválida - maiúsculas
        >>> validate_identificador("minha tag")      # inválida - espaço
    """
    if len(value) > 40:
        raise ValidationError("Identificador deve ter no máximo 40 caracteres.")

    if " " in value:
        raise ValidationError("Identificador não deve conter espaços.")

    if not value.islower():
        raise ValidationError("Identificador deve conter apenas letras minúsculas.")

    # Validar se contém apenas letras, números e underscore
    if not re.match(r"^[a-z0-9_]+$", value):
        raise ValidationError(
            "Identificador deve conter apenas letras minúsculas, números e underscore."
        )


class Treinamento(models.Model):
    """Modelo para armazenar informações de treinamento de IA.

    Este modelo gerencia treinamentos organizados por tags e grupos.
    O conteúdo completo é armazenado aqui, sendo a operações de documentos
    delegadas ao modelo Documento através de relacionamento 1:N.

    Attributes:
        id: Chave primária do registro
        tag: Identificador único do treinamento
        grupo: Grupo ao qual o treinamento pertence
        conteudo: Conteúdo completo do treinamento (antes da divisão em chunks)
        treinamento_finalizado: Status de finalização do treinamento
        treinamento_vetorizado: Status de vetorização do treinamento
        data_criacao: Data de criação automática do treinamento
        data_atualizacao: Data da última atualização
    """

    id: models.AutoField = models.AutoField(
        primary_key=True, help_text="Chave primária do registro"
    )
    tag: models.CharField = models.CharField(
        max_length=40,
        validators=[validate_identificador],
        blank=False,
        null=False,
        help_text="Campo obrigatório para identificar o treinamento",
    )
    grupo: models.CharField = models.CharField(
        max_length=40,
        validators=[validate_identificador],
        blank=False,
        null=False,
        help_text="Campo obrigatório para identificar o grupo do treinamento",
    )
    conteudo: models.TextField = models.TextField(
        blank=True,
        null=True,
        help_text="Conteúdo completo do treinamento (antes da divisão em chunks)",
    )
    treinamento_finalizado: models.BooleanField = models.BooleanField(
        default=False,
        help_text="Indica se o treinamento foi finalizado",
    )
    treinamento_vetorizado: models.BooleanField = models.BooleanField(
        default=False,
        help_text="Indica se o treinamento foi vetorizado com sucesso",
    )
    data_criacao: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criação do treinamento",
    )
    data_atualizacao: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        help_text="Data da última atualização do treinamento",
    )

    class Meta:
        verbose_name = "Treinamento"
        verbose_name_plural = "Treinamentos"
        ordering = ["-data_criacao"]
        indexes = [
            models.Index(fields=["tag", "grupo"]),
            models.Index(fields=["data_criacao"]),
            models.Index(fields=["treinamento_finalizado", "treinamento_vetorizado"]),
        ]

    def clean(self):
        """Validação personalizada do modelo.

        Valida que a tag não seja igual ao grupo e executa outras
        validações customizadas do modelo.

        Raises:
            ValidationError: Se houver violação das regras de validação
        """
        super().clean()

        # Validação customizada: tag não pode ser igual ao grupo
        if self.tag and self.grupo and self.tag == self.grupo:
            raise ValidationError({"grupo": "O grupo não pode ser igual à tag."})

    def __str__(self):
        """Retorna representação string do objeto.

        Returns:
            str: Tag do treinamento ou identificador padrão
        """
        return str(self.tag) if self.tag else f"Treinamento {self.id}"

    def finalizar(self) -> None:
        """Marca o treinamento como finalizado e persiste no banco.
        
        Este é o único método mantido no modelo Treinamento pois altera
        diretamente o status do próprio treinamento.
        """
        self.treinamento_finalizado = True
        self.save(update_fields=["treinamento_finalizado"])
        logger.info(f"Treinamento {self.pk} finalizado")

    def clear_all_data(self) -> None:
        """Limpa completamente todos os dados do treinamento para reutilização.
        
        Este método é especialmente útil durante edição de treinamentos,
        garantindo que não haja conflitos ou problemas de ambiguidade.
        """
        self.conteudo = ""
        self.treinamento_finalizado = False
        self.treinamento_vetorizado = False
        
        # Delega a limpeza de documentos para o modelo Documento
        if self.pk:
            from .models_documento import Documento
            Documento.limpar_documentos_por_treinamento(self.pk)
            
        logger.info(f"Dados do treinamento {self.pk or 'novo'} limpos completamente")
