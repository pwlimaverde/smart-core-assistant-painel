from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import (
    AnalisePreviaMensagemLangchain, )
from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.pydantic_model_factory import (
    create_dynamic_pydantic_model, )
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnalisePreviaMensagemParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import APMData


class AnalisePreviaMensagemLangchainDatasource(APMData):

    def __call__(
            self,
            parameters: AnalisePreviaMensagemParameters) -> AnalisePreviaMensagemLangchain:

        try:
            # Criar modelo PydanticModel dinâmico baseado nos parâmetros
            PydanticModel = create_dynamic_pydantic_model(
                intent_types_json=parameters.valid_intent_types,
                entity_types_json=parameters.valid_entity_types
            )

            # Processar histórico do atendimento
            historico_formatado = self._formatar_historico_atendimento(
                parameters.historico_atendimento
            )

            # Escapar chaves JSON no prompt system para evitar conflito com
            # variáveis do template
            prompt_system_escaped = parameters.llm_parameters.prompt_system.replace(
                '{', '{{').replace('}', '}}')

            messages = ChatPromptTemplate.from_messages([
                ('system', prompt_system_escaped),
                ('user', '{historico_context}\n\n{prompt_human}: {context}')
            ])

            llm = parameters.llm_parameters.create_llm

            # Verificar se o modelo é local (baseado no nome ou em alguma propriedade)
            model_str = str(llm).lower()
            llm_class_str = llm.__class__.__name__.lower()
            
            # Detectar modelos locais por diferentes indicadores
            is_local_model = (
                "local" in model_str or 
                "llama" in model_str or 
                "ollama" in model_str or
                "ollama" in llm_class_str or
                "chatollama" in llm_class_str or
                hasattr(llm, "_is_local") or
                "127.0.0.1" in model_str or
                "localhost" in model_str
            )
            
            logger.info(f"Tipo de modelo detectado: {'LOCAL' if is_local_model else 'REMOTO/CLOUD'}")
            logger.debug(f"Classe do LLM: {llm.__class__.__name__}")
            logger.debug(f"String do modelo: {model_str}")
            
            # Aplicar structured output com método apropriado para o tipo de modelo
            try:
                if is_local_model:
                    # Para modelos locais, tentar primeiro sem method específico
                    try:
                        structured_llm = llm.with_structured_output(PydanticModel)
                        logger.info("Usando método padrão de structured_output para modelo local")
                    except Exception as local_error:
                        # Se falhar, tentar com método JSON explícito
                        logger.warning(f"Erro ao usar método padrão: {local_error}")
                        structured_llm = llm.with_structured_output(PydanticModel, method="json")
                        logger.info("Usando method=json para modelo local após falha no método padrão")
                else:
                    # Para modelos grandes como GPT-4, Claude, etc. usar function_calling
                    structured_llm = llm.with_structured_output(
                        PydanticModel, method="function_calling")
                    logger.info("Usando method=function_calling para modelo não-local")
            except Exception as struct_error:
                # Último recurso: usar o LLM diretamente com instruções explícitas no prompt
                logger.warning(f"Erro ao configurar structured_output: {struct_error}")
                logger.info("Usando LLM diretamente com instruções para formato JSON no prompt")
                
                # Adicionar instruções explícitas para retornar JSON no formato esperado
                json_instructions = """\nIMPORTANTE: Sua resposta DEVE ser um objeto JSON válido no seguinte formato:\n{\n  "intent": [{"type": "string", "value": "string"}],\n  "entities": [{"type": "string", "value": "string"}]\n}\n"""
                
                # Modificar o template para incluir instruções de formato JSON
                messages = ChatPromptTemplate.from_messages([
                    ('system', prompt_system_escaped + json_instructions),
                    ('user', '{historico_context}\n\n{prompt_human}: {context}')
                ])
                
                # Usar o LLM diretamente
                structured_llm = llm

            # Chain com LLM estruturado
            chain = messages | structured_llm

            # Preparar dados para invocação com validação
            invoke_data = {
                'prompt_human': parameters.llm_parameters.prompt_human,
                'context': parameters.llm_parameters.context,
                'historico_context': historico_formatado,
            }

            # Invocar a chain com tratamento de erro aprimorado
            try:
                response = chain.invoke(invoke_data)
            except Exception as chain_error:
                logger.error(f"Erro ao invocar a chain: {chain_error}")
                # Tentar criar uma resposta vazia como fallback
                response = PydanticModel(intent=[], entities=[])
                logger.warning("Usando resposta vazia como fallback após erro na chain")

            # Verificar se a resposta é None (pode ocorrer com modelos locais menores)
            if response is None:
                logger.warning("Resposta da chain é None, usando fallback com resposta vazia")
                response = PydanticModel(intent=[], entities=[])
            
            # Verificar se a resposta é uma string (pode ocorrer com modelos locais)
            elif isinstance(response, str):
                logger.warning(f"Resposta da chain é uma string, tentando parsear como JSON: {response[:100]}...")
                try:
                    import json
                    # Tentar parsear a string como JSON
                    json_data = json.loads(response)
                    # Criar um objeto PydanticModel a partir do JSON
                    response = PydanticModel(**json_data)
                    logger.info("String JSON convertida com sucesso para PydanticModel")
                except Exception as json_error:
                    logger.error(f"Erro ao parsear resposta como JSON: {json_error}")
                    # Fallback para resposta vazia
                    response = PydanticModel(intent=[], entities=[])

            # Verificar se a resposta é uma instância do modelo dinâmico
            if hasattr(response, 'intent') and hasattr(response, 'entities'):
                # Converter PydanticModel para AnalisePreviaMensagem
                # Extrair intent como lista de dicionários {tipo: valor}
                intent_dicts = [{str(item.type): item.value}
                                for item in response.intent]

                # Extrair entities como lista de dicionários {tipo: valor}
                entity_dicts = [{str(item.type): item.value}
                                for item in response.entities]

                # Criar instância de AnalisePreviaMensagem
                resultado = AnalisePreviaMensagemLangchain(
                    intent=intent_dicts,
                    entities=entity_dicts
                )

                return resultado
            else:
                raise ValueError(
                    f"Resposta inesperada: {
                        type(response)}. Esperado: PydanticModel dinâmico")

        except Exception as e:
            logger.error(f"Erro ao processar análise prévia: {e}")
            raise

    def _formatar_historico_atendimento(
            self, historico_atendimento: Any) -> str:
        """
        Formata o histórico do atendimento para contexto do prompt.

        Args:
            historico_atendimento: Lista de mensagens ou dados do histórico

        Returns:
            String formatada para o contexto ou mensagem indicando ausência
        """
        try:
            # Se for None, lista vazia ou falsy
            if not historico_atendimento:
                return "HISTÓRICO DO ATENDIMENTO:\nNenhum histórico de mensagens disponível."

            # Se for uma lista vazia
            if isinstance(historico_atendimento, list) and len(
                    historico_atendimento) == 0:
                return "HISTÓRICO DO ATENDIMENTO:\nNenhum histórico de mensagens disponível."

            # Se for uma lista com mensagens
            if isinstance(historico_atendimento, list):
                historico_texto = "HISTÓRICO DO ATENDIMENTO:\n"
                for i, mensagem in enumerate(
                        historico_atendimento[-10:], 1):  # Últimas 10 mensagens
                    if isinstance(mensagem, str):
                        historico_texto += f"{i}. {mensagem}\n"
                    elif isinstance(mensagem, dict):
                        conteudo = mensagem.get(
                            'conteudo', mensagem.get(
                                'texto', str(mensagem)))
                        remetente = mensagem.get('remetente', 'Usuario')
                        historico_texto += f"{i}. [{remetente}]: {conteudo}\n"
                    else:
                        historico_texto += f"{i}. {str(mensagem)}\n"
                return historico_texto.strip()

            # Se for um dicionário com estrutura específica
            if isinstance(historico_atendimento, dict):
                mensagens = historico_atendimento.get('mensagens', [])
                if mensagens:
                    return self._formatar_historico_atendimento(mensagens)
                else:
                    # Tentar outras chaves possíveis
                    conteudo = (historico_atendimento.get('conteudo_mensagens') or
                                historico_atendimento.get('historico') or
                                historico_atendimento.get('mensagens_anteriores', []))
                    if conteudo:
                        return self._formatar_historico_atendimento(conteudo)

                # Se chegou aqui, é um dicionário sem mensagens válidas
                return "HISTÓRICO DO ATENDIMENTO:\nNenhum histórico de mensagens disponível."

            # Se for uma string (histórico já formatado)
            if isinstance(historico_atendimento, str):
                if historico_atendimento.strip():
                    return f"HISTÓRICO DO ATENDIMENTO:\n{historico_atendimento}"
                else:
                    return "HISTÓRICO DO ATENDIMENTO:\nNenhum histórico de mensagens disponível."

            # Fallback: tentar converter para string
            try:
                historico_str = str(historico_atendimento)
                if historico_str and historico_str not in ['[]', '{}', 'None']:
                    return f"HISTÓRICO DO ATENDIMENTO:\n{historico_str}"
            except Exception:
                pass

            # Último recurso
            return "HISTÓRICO DO ATENDIMENTO:\nNenhum histórico de mensagens disponível."

        except Exception as format_error:
            logger.warning(
                f'Erro ao formatar histórico, usando fallback: {format_error}')
            return "HISTÓRICO DO ATENDIMENTO:\nErro ao processar histórico de mensagens."
