"""Migration E.2: Campos Personalizados.

Cria tabelas `atu_campo_personalizado` e `atu_valor_campo`.
ZERO alteração em tabelas legadas.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento_unificado", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CampoPersonalizado",
            fields=[
                (
                    "id",
                    models.BigAutoField(primary_key=True, serialize=False),
                ),
                (
                    "slug",
                    models.SlugField(
                        max_length=64,
                        help_text="Identificador URL-friendly (ex: 'cnpj_cliente').",
                    ),
                ),
                ("nome", models.CharField(max_length=120)),
                (
                    "descricao",
                    models.TextField(
                        blank=True,
                        help_text="Descrição do campo — também usado como hint de extração.",
                    ),
                ),
                (
                    "escopo",
                    models.CharField(
                        choices=[
                            ("GLOBAL", "Global (todos os fluxos)"),
                            ("FLUXO", "Por Fluxo"),
                        ],
                        default="GLOBAL",
                        max_length=10,
                    ),
                ),
                (
                    "fluxo_id",
                    models.BigIntegerField(
                        blank=True,
                        null=True,
                        help_text="ID lógico de operacional.FluxoAtendimento (null se GLOBAL).",
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("texto", "Texto"),
                            ("numero", "Número"),
                            ("data", "Data"),
                            ("escolha", "Escolha única"),
                            ("multipla_escolha", "Múltipla escolha"),
                            ("booleano", "Booleano"),
                        ],
                        default="texto",
                        max_length=20,
                    ),
                ),
                (
                    "opcoes",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="Opções válidas para tipos escolha/multipla_escolha.",
                    ),
                ),
                ("obrigatorio", models.BooleanField(default=False)),
                (
                    "extrair_automaticamente",
                    models.BooleanField(
                        default=True,
                        help_text="Se True, o bot tenta extrair este campo da conversa.",
                    ),
                ),
                (
                    "extrair_hint",
                    models.CharField(
                        blank=True,
                        max_length=500,
                        help_text="Dica para a IA sobre como reconhecer este campo.",
                    ),
                ),
                (
                    "mostrar_no_card",
                    models.BooleanField(
                        default=True,
                        help_text="Exibir valor como badge no card do Kanban.",
                    ),
                ),
                ("ordem", models.PositiveSmallIntegerField(default=0)),
                ("ativo", models.BooleanField(default=True)),
                ("data_criacao", models.DateTimeField(auto_now_add=True)),
                ("data_atualizacao", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Campo Personalizado",
                "verbose_name_plural": "Campos Personalizados",
                "db_table": "atu_campo_personalizado",
                "ordering": ["ordem", "nome"],
                "unique_together": {("slug", "escopo", "fluxo_id")},
            },
        ),
        migrations.AddIndex(
            model_name="campopersonalizado",
            index=models.Index(
                fields=["escopo", "fluxo_id", "ativo"],
                name="atu_campo_escopo_fluxo_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="campopersonalizado",
            index=models.Index(
                fields=["extrair_automaticamente", "ativo"],
                name="atu_campo_extrair_idx",
            ),
        ),
        migrations.CreateModel(
            name="ValorCampoAtendimento",
            fields=[
                (
                    "id",
                    models.BigAutoField(primary_key=True, serialize=False),
                ),
                (
                    "atendimento_id",
                    models.BigIntegerField(
                        help_text="ID lógico de atendimentos.Atendimento (sem FK cruzada).",
                    ),
                ),
                (
                    "campo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="valores",
                        to="atendimento_unificado.campopersonalizado",
                    ),
                ),
                (
                    "valor",
                    models.JSONField(
                        help_text="Valor do campo (string, número, lista, bool, etc.).",
                    ),
                ),
                (
                    "origem",
                    models.CharField(
                        choices=[
                            ("MANUAL", "Manual (atendente)"),
                            ("BOT", "Bot (extração IA)"),
                            ("IMPORT", "Importado"),
                        ],
                        default="MANUAL",
                        max_length=10,
                    ),
                ),
                (
                    "confianca",
                    models.FloatField(
                        blank=True,
                        null=True,
                        help_text="Score de confiança da extração (apenas quando origem=BOT).",
                    ),
                ),
                (
                    "mensagem_origem_id",
                    models.BigIntegerField(
                        blank=True,
                        null=True,
                        help_text="ID lógico da Mensagem que originou a extração (BOT).",
                    ),
                ),
                (
                    "editado_por_id",
                    models.BigIntegerField(
                        blank=True,
                        null=True,
                        help_text="ID lógico do Atendente que editou manualmente.",
                    ),
                ),
                ("data_atualizacao", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Valor de Campo",
                "verbose_name_plural": "Valores de Campos",
                "db_table": "atu_valor_campo",
                "unique_together": {("atendimento_id", "campo")},
            },
        ),
        migrations.AddIndex(
            model_name="valorcampoatendimento",
            index=models.Index(
                fields=["atendimento_id", "campo"],
                name="atu_valor_atend_campo_idx",
            ),
        ),
    ]
