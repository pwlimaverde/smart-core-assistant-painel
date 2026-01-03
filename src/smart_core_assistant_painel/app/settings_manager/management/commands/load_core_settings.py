import os
from django.core.management.base import BaseCommand
from smart_core_assistant_painel.app.settings_manager.models import (
    CoreSettings,
)
from smart_core_assistant_painel.modules.services.features.features_compose import (
    FeaturesCompose,
)
from smart_core_assistant_painel.app.tenants.utils.encryption import (
    encrypt_value,
)


class Command(BaseCommand):
    help = (
        "Carrega variáveis do Firebase Remote Config e salva no CoreSettings"
    )

    def handle(self, *args, **options):
        self.stdout.write("Iniciando importação do Firebase Remote Config...")

        try:
            # 1. Força o carregamento das variáveis do Firebase para o os.environ
            # Isso usa a implementação antiga para buscar os dados reais atuais
            FeaturesCompose.set_environ_remote()

            # 2. Mapeamento De/Para (Banco -> Variável de Ambiente)
            MAPPING = {
                # === API Keys ===
                "groq_api_key": "GROQ_API_KEY",
                "openai_api_key": "OPENAI_API_KEY",
                # === LLM ===
                "llm_class": "LLM_CLASS",
                "model": "MODEL",
                "llm_temperature": "LLM_TEMPERATURE",
                # === Prompts do Sistema ===
                "prompt_system_analise_mensagem": "PROMPT_SYSTEM_ANALISE_MENSAGEM",
                "prompt_system_analise_previa_mensagem": "PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM",
                "prompt_human_analise_previa_mensagem": "PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM",
                "prompt_system_analise_conteudo": "PROMPT_SYSTEM_ANALISE_CONTEUDO",
                "prompt_human_analise_conteudo": "PROMPT_HUMAN_ANALISE_CONTEUDO",
                "prompt_intent_system": "PROMPT_INTENT_SYSTEM",
                "prompt_intent_footer": "PROMPT_INTENT_FOOTER",
                "prompt_regras_resposta": "PROMPT_REGRAS_RESPOSTA",
                "prompt_regras_transferencia": "PROMPT_REGRAS_TRANSFERENCIA",
                # === Embeddings ===
                "embeddings_class": "EMBEDDINGS_CLASS",
                "embeddings_model": "EMBEDDINGS_MODEL",
                "chunk_size": "CHUNK_SIZE",
                "chunk_overlap": "CHUNK_OVERLAP",
                # === Thresholds ===
                "similarity_threshold": "SIMILARITY_THRESHOLD",
                "vector_distance_threshold": "VECTOR_DISTANCE_THRESHOLD",
                "time_cache": "TIME_CACHE",
                # === Mensagens Defaults (Fallback) ===
                "msg_fallback_sem_info": "MSG_FALLBACK_SEM_INFO",
                "msg_fallback_geral": "MSG_FALLBACK_GERAL",
                "msg_transferencia_generica": "MSG_TRANSFERENCIA_GENERICA",
            }

            count = 0
            for db_key, env_key in MAPPING.items():
                # Obtém do environ (já populado pelo FeaturesCompose)
                value = os.environ.get(env_key)

                if value is not None:
                    # Determina se deve ser criptografado
                    should_encrypt = db_key.endswith("api_key")

                    final_value = value
                    if should_encrypt and value:
                        # Criptografa antes de salvar
                        try:
                            final_value = encrypt_value(value)
                        except Exception as e:
                            self.stderr.write(
                                f"Erro ao criptografar {db_key}: {e}"
                            )
                            continue

                    obj, created = CoreSettings.objects.update_or_create(
                        key=db_key,
                        defaults={
                            "value": final_value,
                            "encrypted": should_encrypt,
                            "description": f"Importado via script ({env_key})",
                        },
                    )

                    action = "Criado" if created else "Atualizado"
                    self.stdout.write(f"{action}: {db_key}")
                    count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Ignorado (não encontrado): {env_key}"
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Processo concluído! {count} configurações importadas."
                )
            )

        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Erro crítico durante importação: {str(e)}")
            )
            # Importante: Mostrar traceback se possível em dev, ou logar
            import traceback

            traceback.print_exc()
