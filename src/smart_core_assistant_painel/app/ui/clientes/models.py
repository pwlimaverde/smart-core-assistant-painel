import re
from datetime import datetime
from typing import Any, override

from django.core.exceptions import ValidationError
from django.db import models


def validate_telefone(value: str) -> None:
    """
    Valida se o número de telefone está no formato correto.
    """
    telefone_limpo: str = re.sub(r"\D", "", value)
    if len(telefone_limpo) < 10 or len(telefone_limpo) > 15:
        raise ValidationError("Número de telefone deve ter entre 10 e 15 dígitos.")
    if not telefone_limpo.isdigit():
        raise ValidationError("Número de telefone deve conter apenas números.")


def validate_cnpj(value: str) -> None:
    """
    Valida se o CNPJ está no formato correto.
    """
    if not value:
        return
    cnpj_limpo: str = re.sub(r"\D", "", value)
    if len(cnpj_limpo) != 14:
        raise ValidationError("CNPJ deve ter exatamente 14 dígitos.")
    if not cnpj_limpo.isdigit():
        raise ValidationError("CNPJ deve conter apenas números.")
    if cnpj_limpo == "00000000000000":
        raise ValidationError("CNPJ inválido.")


def validate_cpf(value: str) -> None:
    """
    Valida se o CPF está no formato correto.
    """
    if not value:
        return
    cpf_limpo = re.sub(r"\D", "", value)
    if len(cpf_limpo) != 11:
        raise ValidationError("CPF deve ter exatamente 11 dígitos.")
    if not cpf_limpo.isdigit():
        raise ValidationError("CPF deve conter apenas números.")
    if cpf_limpo == "00000000000":
        raise ValidationError("CPF inválido.")


def validate_cep(value: str) -> None:
    """
    Valida se o CEP está no formato correto.
    """
    if not value:
        return
    cep_limpo: str = re.sub(r"\D", "", value)
    if len(cep_limpo) != 8:
        raise ValidationError("CEP deve ter exatamente 8 dígitos.")
    if not cep_limpo.isdigit():
        raise ValidationError("CEP deve conter apenas números.")


class Contato(models.Model):
    id: models.AutoField = models.AutoField(
        primary_key=True, help_text="Chave primária do registro"
    )
    telefone: models.CharField[str] = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_telefone],
        help_text="Número de telefone do contato (formato: 5511999999999)",
    )
    nome_contato: models.CharField[str | None] = models.CharField(
        max_length=100, blank=True, null=True, help_text="Nome do contato"
    )
    email: models.EmailField[str | None] = models.EmailField(
        max_length=254,
        blank=True,
        null=True,
        help_text="E-mail do contato",
    )
    nome_perfil_whatsapp: models.CharField[str | None] = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Nome do perfil cadastrado no WhatsApp do contato",
    )
    data_cadastro: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True, help_text="Data de cadastro do contato"
    )
    ultima_interacao: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True, help_text="Data da última interação"
    )
    ativo: models.BooleanField[bool] = models.BooleanField(
        default=True, help_text="Status de atividade do contato"
    )
    metadados: models.JSONField[dict[str, Any] | None] = models.JSONField(
        default=dict, blank=True, help_text="Informações adicionais do contato"
    )

    class Meta:
        verbose_name = "Contato"
        verbose_name_plural = "Contatos"
        ordering = ["-ultima_interacao"]
        db_table = "oraculo_contato"

    @override
    def __str__(self) -> str:
        return f"{self.nome_contato or 'Contato'} ({self.telefone})"

    @override
    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.telefone:
            telefone_limpo = re.sub(r"\D", "", self.telefone)
            if not telefone_limpo.startswith("55"):
                telefone_limpo = "55" + telefone_limpo
            self.telefone = telefone_limpo
        super().save(*args, **kwargs)


class Cliente(models.Model):
    id: models.AutoField = models.AutoField(
        primary_key=True, help_text="Chave primária do registro"
    )
    nome_fantasia: models.CharField[str] = models.CharField(
        max_length=200,
        blank=False,
        null=False,
        help_text="Nome comum do cliente (obrigatório)",
    )
    razao_social: models.CharField[str | None] = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Nome legal/oficial do cliente",
    )
    tipo: models.CharField[str | None] = models.CharField(
        max_length=20,
        choices=[("fisica", "Pessoa Física"), ("juridica", "Pessoa Jurídica")],
        blank=True,
        null=True,
        help_text="Tipo de pessoa (física ou jurídica)",
    )
    cnpj: models.CharField[str | None] = models.CharField(
        max_length=18,
        blank=True,
        null=True,
        validators=[validate_cnpj],
        help_text="CNPJ do cliente (formato: 12.345.678/0001-99)",
    )
    cpf: models.CharField[str | None] = models.CharField(
        max_length=14,
        blank=True,
        null=True,
        validators=[validate_cpf],
        help_text="CPF do cliente informado durante a conversa (formato: 123.456.789-00)",
    )
    telefone: models.CharField[str | None] = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[validate_telefone],
        help_text="Telefone fixo ou corporativo do cliente",
    )
    site: models.URLField[str | None] = models.URLField(
        blank=True, null=True, help_text="Website do cliente"
    )
    ramo_atividade: models.CharField[str | None] = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Área de atuação do cliente",
    )
    observacoes: models.TextField[str | None] = models.TextField(
        blank=True,
        null=True,
        help_text="Informações adicionais sobre o cliente",
    )
    cep: models.CharField[str | None] = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[validate_cep],
        help_text="CEP do endereço (formato: 12345-678)",
    )
    logradouro: models.CharField[str | None] = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Rua, avenida ou logradouro",
    )
    numero: models.CharField[str | None] = models.CharField(
        max_length=10, blank=True, null=True, help_text="Número do endereço"
    )
    complemento: models.CharField[str | None] = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Complemento do endereço (sala, andar, etc.)",
    )
    bairro: models.CharField[str | None] = models.CharField(
        max_length=100, blank=True, null=True, help_text="Bairro do cliente"
    )
    cidade: models.CharField[str | None] = models.CharField(
        max_length=100, blank=True, null=True, help_text="Cidade do cliente"
    )
    uf: models.CharField[str | None] = models.CharField(
        max_length=2, blank=True, null=True, help_text="Estado (UF) do cliente"
    )
    pais: models.CharField[str | None] = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default="Brasil",
        help_text="País do cliente",
    )
    contatos: models.ManyToManyField["Contato", "Contato"] = models.ManyToManyField(
        "Contato",
        blank=True,
        related_name="clientes",
        help_text="Contatos vinculados ao cliente",
    )
    data_cadastro: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True, help_text="Data de cadastro do cliente"
    )
    ultima_atualizacao: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True, help_text="Data da última atualização"
    )
    ativo: models.BooleanField[bool] = models.BooleanField(
        default=True, help_text="Status de atividade do cliente"
    )
    metadados: models.JSONField[dict[str, Any] | None] = models.JSONField(
        default=dict, blank=True, help_text="Informações adicionais do cliente"
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nome_fantasia"]
        db_table = "oraculo_cliente"

    @override
    def __str__(self) -> str:
        return self.nome_fantasia

    @override
    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.cnpj:
            cnpj_limpo = re.sub(r"\D", "", self.cnpj)
            if len(cnpj_limpo) == 14:
                self.cnpj = f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:14]}"
        if self.cpf:
            cpf_limpo = re.sub(r"\D", "", self.cpf)
            if len(cpf_limpo) == 11:
                self.cpf = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:11]}"
        if self.cep:
            cep_limpo = re.sub(r"\D", "", self.cep)
            if len(cep_limpo) == 8:
                self.cep = f"{cep_limpo[:5]}-{cep_limpo[5:]}"
        if self.telefone:
            telefone_limpo = re.sub(r"\D", "", self.telefone)
            if len(telefone_limpo) >= 10:
                if not self.telefone.startswith("+"):
                    self.telefone = f"({telefone_limpo[:2]}) {telefone_limpo[2:6]}-{telefone_limpo[6:]}"
        if self.uf:
            self.uf = self.uf.upper()
        super().save(*args, **kwargs)

    @override
    def clean(self) -> None:
        super().clean()
        if not self.nome_fantasia or not self.nome_fantasia.strip():
            raise ValidationError({"nome_fantasia": "Nome fantasia é obrigatório."})

    def get_endereco_completo(self) -> str:
        partes_endereco: list[str] = []
        if self.logradouro:
            endereco_linha: str = self.logradouro
            if self.numero:
                endereco_linha += f", {self.numero}"
            if self.complemento:
                endereco_linha += f", {self.complemento}"
            partes_endereco.append(endereco_linha)
        if self.bairro:
            partes_endereco.append(self.bairro)
        if self.cidade and self.uf:
            partes_endereco.append(f"{self.cidade} - {self.uf}")
        elif self.cidade:
            partes_endereco.append(self.cidade)
        if self.cep:
            partes_endereco.append(f"CEP: {self.cep}")
        if self.pais and self.pais != "Brasil":
            partes_endereco.append(self.pais)
        return ", ".join(partes_endereco) if partes_endereco else ""

    def adicionar_contato(self, contato: "Contato") -> None:
        self.contatos.add(contato)

    def remover_contato(self, contato: "Contato") -> None:
        self.contatos.remove(contato)

    def atualizar_metadados(self, chave: str, valor: Any) -> None:
        if not self.metadados:
            self.metadados = {}
        self.metadados[chave] = valor
        self.save()

    def get_metadados(self, chave: str, padrao: Any = None) -> Any:
        if not self.metadados:
            return padrao
        return self.metadados.get(chave, padrao)