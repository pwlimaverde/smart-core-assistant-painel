import json
import os
import tempfile
from typing import TYPE_CHECKING, Any, cast

from django.contrib import messages
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from langchain.docstore.document import Document
from loguru import logger
from rolepermissions.checkers import has_permission

from smart_core_assistant_painel.modules.ai_engine.features.features_compose import (
    FeaturesCompose,
)
from smart_core_assistant_painel.modules.services.features.service_hub import SERVICEHUB

from .models import (
    Atendimento,
    Contato,
    Mensagem,
    TipoMensagem,
    TipoRemetente,
    Treinamentos,
    nova_mensagem,
)

if TYPE_CHECKING:
    pass


class TreinamentoService:
    """Serviço para gerenciar operações de treinamento"""

    @staticmethod
    def aplicar_pre_analise_documentos(documentos: list[Document]) -> list[Document]:
        """Aplica pré-análise de IA ao page_content de uma lista de documentos

        Args:
            documentos: Lista de documentos para processar

        Returns:
            Lista de documentos com page_content atualizado
        """
        documentos_processados = []

        for documento in documentos:
            try:
                # Aplicar pré-análise
                pre_analise_content = FeaturesCompose.pre_analise_ia_treinamento(
                    documento.page_content
                )
                documento.page_content = pre_analise_content
                documentos_processados.append(documento)

            except Exception as e:
                logger.error(f"Erro ao aplicar pré-análise no documento: {e}")
                # Mantém documento original em caso de erro
                documentos_processados.append(documento)

        return documentos_processados

    @staticmethod
    def processar_arquivo_upload(arquivo):
        """Processa arquivo uploadado e retorna caminho temporário"""
        if not arquivo:
            return None

        try:
            return arquivo.temporary_file_path()
        except AttributeError:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=os.path.splitext(arquivo.name)[1]
            ) as temp_file:
                for chunk in arquivo.chunks():
                    temp_file.write(chunk)
                return temp_file.name

    @staticmethod
    def processar_conteudo_texto(
        treinamento_id: int, conteudo: str, tag: str, grupo: str
    ) -> list[Document]:
        """Processa conteúdo de texto para treinamento"""
        if not conteudo:
            raise ValueError("Conteúdo não pode ser vazio")

        try:
            pre_analise_conteudo = FeaturesCompose.pre_analise_ia_treinamento(conteudo)
            data_conteudo = FeaturesCompose.load_document_conteudo(
                id=str(treinamento_id),
                conteudo=pre_analise_conteudo,
                tag=tag,
                grupo=grupo,
            )
            return data_conteudo
        except Exception as e:
            logger.error(f"Erro ao processar conteúdo texto: {e}")
            raise e

    @staticmethod
    def processar_arquivo_documento(
        treinamento_id: int, documento_path: str, tag: str, grupo: str
    ) -> list[Document]:
        """Processa arquivo de documento para treinamento"""
        if not documento_path:
            raise ValueError("Caminho do documento não pode ser vazio")

        try:
            data_file = FeaturesCompose.load_document_file(
                id=str(treinamento_id),
                path=documento_path,
                tag=tag,
                grupo=grupo,
            )

            return TreinamentoService.aplicar_pre_analise_documentos(data_file)

        except Exception as e:
            logger.error(f"Erro ao processar arquivo documento: {e}")
            raise e

    @staticmethod
    def limpar_arquivo_temporario(arquivo_path):
        """Remove arquivo temporário se existir"""
        if arquivo_path and os.path.exists(arquivo_path):
            try:
                os.unlink(arquivo_path)
            except OSError:
                pass


def treinar_ia(request):
    """View para treinamento de IA"""
    if not has_permission(request.user, "treinar_ia"):
        raise Http404()

    if request.method == "GET":
        return render(request, "treinar_ia.html")

    if request.method == "POST":
        return _processar_treinamento(request)


def _processar_treinamento(request):
    """Processa dados de treinamento enviados via POST"""
    tag = request.POST.get("tag")
    grupo = request.POST.get("grupo")
    conteudo = request.POST.get("conteudo")
    documento = request.FILES.get("documento")

    # Validações básicas
    if not tag or not grupo:
        messages.error(request, "Tag e Grupo são obrigatórios.")
        return render(request, "treinar_ia.html")

    if not conteudo and not documento:
        messages.error(request, "É necessário fornecer conteúdo ou documento.")
        return render(request, "treinar_ia.html")

    documento_path = None

    try:
        with transaction.atomic():
            # Criar registro de treinamento
            treinamento = Treinamentos.objects.create(
                tag=tag,
                grupo=grupo,
            )

            documents_list = []

            # Processar arquivo se fornecido
            if documento:
                documento_path = TreinamentoService.processar_arquivo_upload(documento)
                if documento_path:
                    docs_arquivo = TreinamentoService.processar_arquivo_documento(
                        treinamento.id, documento_path, tag, grupo
                    )
                    documents_list.extend(docs_arquivo)

            # Processar conteúdo de texto se fornecido
            if conteudo:
                docs_conteudo = TreinamentoService.processar_conteudo_texto(
                    treinamento.id, conteudo, tag, grupo
                )
                documents_list.extend(docs_conteudo)

            # Salvar documentos processados
            treinamento.set_documentos(documents_list)
            treinamento.save()

            messages.success(request, "Treinamento criado com sucesso!")
            return redirect("pre_processamento", id=treinamento.id)

    except Exception as e:
        logger.error(f"Erro ao processar treinamento: {e}")
        messages.error(request, "Erro interno do servidor. Tente novamente.")
        return render(request, "treinar_ia.html")

    finally:
        # Limpar arquivo temporário
        TreinamentoService.limpar_arquivo_temporario(documento_path)


def pre_processamento(request, id):
    """View para pré-processamento de treinamento"""
    if not has_permission(request.user, "treinar_ia"):
        raise Http404()

    if request.method == "GET":
        return _exibir_pre_processamento(request, id)

    if request.method == "POST":
        return _processar_pre_processamento(request, id)


def _exibir_pre_processamento(request, id):
    """Exibe página de pré-processamento"""
    try:
        treinamento = Treinamentos.objects.get(id=id)
        conteudo_unificado = treinamento.get_conteudo_unificado()
        texto_melhorado = FeaturesCompose.melhoria_ia_treinamento(conteudo_unificado)

        return render(
            request,
            "pre_processamento.html",
            {
                "dados_organizados": treinamento,
                "treinamento": texto_melhorado,
            },
        )
    except Exception as e:
        logger.error(f"Erro ao gerar pré-processamento: {e}")
        messages.error(request, "Erro ao processar dados de treinamento.")
        return redirect("treinar_ia")


def _processar_pre_processamento(request, id):
    """Processa ação do pré-processamento"""
    treinamento = Treinamentos.objects.get(id=id)
    acao = request.POST.get("acao")

    if not acao:
        messages.error(request, "Ação não especificada.")

        return redirect("pre_processamento", id=treinamento.id)

    try:
        with transaction.atomic():
            if acao == "aceitar":
                _aceitar_treinamento(id)
                messages.success(request, "Treinamento aceito e finalizado!")
            elif acao == "manter":
                treinamento.treinamento_finalizado = True
                treinamento.save()
                messages.success(request, "Treinamento mantido e finalizado!")
            elif acao == "descartar":
                treinamento.delete()
                messages.info(request, "Treinamento descartado.")
            else:
                messages.error(request, "Ação inválida.")
                return redirect("pre_processamento", id=treinamento.id)

    except Exception as e:
        logger.error(f"Erro ao processar ação {acao}: {e}")
        messages.error(request, "Erro ao processar ação. Tente novamente.")

        return redirect("pre_processamento", id=treinamento.id)

    return redirect("treinar_ia")


def _aceitar_treinamento(id):
    """Aceita treinamento e atualiza conteúdo melhorado individualmente para cada documento"""
    try:
        # Processa documentos - agora sempre será uma lista (JSONField)
        treinamento = Treinamentos.objects.get(id=id)
        documentos_lista = treinamento.get_documentos()
        if not documentos_lista:
            return

        documentos_melhorados = TreinamentoService.aplicar_pre_analise_documentos(
            documentos_lista
        )
        # Salva alterações
        treinamento.set_documentos(documentos_melhorados)
        treinamento.treinamento_finalizado = True
        treinamento.save()

    except Exception as e:
        logger.error(f"Erro ao aceitar treinamento {treinamento.id}: {e}")
        raise


@csrf_exempt
def webhook_whatsapp(request):
    """
    Webhook robusto para recebimento e processamento de mensagens do WhatsApp.

    Esta função é o ponto de entrada principal para mensagens do WhatsApp via webhook.
    Realiza validações completas, processa mensagens usando a função nova_mensagem(),
    determina o direcionamento apropriado (bot ou atendente humano), converte contexto
    de mensagens não textuais e prepara a mensagem para processamento posterior.

    Args:
        request (HttpRequest): Requisição HTTP contendo os dados do webhook
            do WhatsApp em formato JSON no body da requisição. Deve ser POST
            com Content-Type application/json.

    Returns:
        JsonResponse: Resposta JSON com status da operação:
            - Em caso de sucesso: {
                "status": "success",
                "mensagem_id": int,
                "direcionamento": str  # "bot" ou "humano"
              }
            - Em caso de erro: {"error": str} com códigos:
                * 400: Requisição inválida (JSON malformado, corpo vazio)
                * 401: API key inválida (quando implementada)
                * 405: Método HTTP não permitido (apenas POST aceito)
                * 500: Erro interno do servidor

    Raises:
        json.JSONDecodeError: Se o body da requisição não contém JSON válido
        Mensagem.DoesNotExist: Se a mensagem criada não for encontrada no banco
        ValidationError: Se dados do webhook são inválidos
        Exception: Para outros erros durante o processamento

    Validations:
        - Método HTTP deve ser POST
        - Body da requisição não pode estar vazio
        - JSON deve ser válido e estruturado como dicionário
        - Mensagem deve ser criada com sucesso no banco de dados
        - TODO: Validação de API key para segurança

    Processing Flow:
        1. Validação da requisição HTTP
        2. Parse e validação do JSON
        3. Logging de auditoria de entrada
        4. Processamento via nova_mensagem()
        5. Conversão de contexto para mensagens não textuais
        6. Determinação de direcionamento (bot vs humano)
        7. Logging completo de sucesso
        8. Resposta estruturada com metadados

    Security:
        - Função marcada com @csrf_exempt para chamadas externas
        - Logs não expõem dados sensíveis
        - Comportamento conservador em caso de erro (assume humano)
        - Preparada para validação de API key

    Performance:
        - Usa update_fields para economia em alterações de mensagem
        - Logs estruturados para facilitar monitoramento
        - Graceful degradation em falhas não críticas

    Examples:
        Payload típico do webhook:
        {
          "event": "messages.upsert",
          "instance": "arcane",
          "data": {
            "key": {
              "remoteJid": "5516992805442@s.whatsapp.net",
              "fromMe": false,
              "id": "5F2AAA4BD98BB388BBCD6FCB9B4ED660"
            },
            "pushName": "Cliente Exemplo",
            "message": {
              "extendedTextMessage": {
                "text": "Olá, preciso de ajuda com meu pedido"
              }
            },
            "messageType": "conversation",
            "messageTimestamp": 1748739583
          },
          "owner": "arcane",
          "source": "android",
          "destination": "localhost",
          "date_time": "2025-07-18T14:30:00.000Z",
          "sender": "5516999999999@s.whatsapp.net",
          "server_url": "http://localhost:8080",
          "apikey": "sua_api_key_aqui",
          "webhookUrl": "https://seu-dominio.com/webhook",
          "executionMode": "production"
        }

        Resposta de sucesso:
        {
          "status": "success",
          "mensagem_id": 12345,
          "direcionamento": "bot"
        }

    Notes:
        - Integração completa com sistema de logs para auditoria
        - Suporte a todos os tipos de mensagem do WhatsApp
        - Direcionamento inteligente baseado em contexto de atendimento
        - Preparado para futuras implementações de resposta automática
        - Tratamento robusto de erros com logs detalhados
    """
    try:
        # TODO: Implementar validação de API key se necessário
        # api_key = data.get('apikey')
        # if not _validar_api_key(api_key):
        #     return JsonResponse({"error": "API key inválida"}, status=401)
        
        # Validação básica da requisição
        if request.method != "POST":
            return JsonResponse({"error": "Método não permitido"}, status=405)

        if not request.body:
            return JsonResponse({"error": "Corpo da requisição vazio"}, status=400)

        # Parse do JSON com tratamento robusto de encoding
        try:
            # Tentar diferentes encodings para decodificar o corpo da requisição
            body_str = None
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    body_str = request.body.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if body_str is None:
                logger.error("Não foi possível decodificar o corpo da requisição com nenhum encoding")
                return JsonResponse({"error": "Erro de codificação de caracteres"}, status=400)
            
            data = json.loads(body_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON inválido recebido no webhook: {e}")
            return JsonResponse({"error": "JSON inválido"}, status=400)

        # Validação dos campos obrigatórios
        if not isinstance(data, dict):
            return JsonResponse({"error": "Formato de dados inválido"}, status=400)



        # Processar mensagem usando função nova_mensagem
        try:
            mensagem_id = nova_mensagem(data)
        except Exception as e:
            logger.error(f"Erro ao processar nova mensagem: {e}")
            return JsonResponse({"error": "Erro ao processar mensagem"}, status=500)

        # Validar se a mensagem foi realmente criada
        try:
            mensagem = Mensagem.objects.get(id=mensagem_id)
        except Mensagem.DoesNotExist:
            logger.error(f"Mensagem criada (ID: {mensagem_id}) não encontrada no banco")
            return JsonResponse({"error": "Mensagem não encontrada"}, status=500)

        # Processamento especial para mensagens não textuais
        if mensagem.tipo != TipoMensagem.TEXTO_FORMATADO:
            try:
                conteudo_original = mensagem.conteudo
                conteudo_convertido = _converter_contexto(metadata=mensagem.metadados)

                if conteudo_convertido != conteudo_original:
                    mensagem.conteudo = conteudo_convertido
                    mensagem.save(update_fields=["conteudo"])

            except Exception as e:
                # Continua processamento mesmo com erro na conversão
                logger.error(
                    f"Erro ao converter contexto da mensagem {mensagem_id}: {e}"
                )
        # Analise previa do conteudo da mensagem por agente de IA, detectando
        # intent e extraindo entidades
        try:
            _analisar_conteudo_mensagem(mensagem_id)
        except Exception as e:
            logger.error(f"Erro ao analisar conteúdo da mensagem {mensagem_id}: {e}")


        # Verificação de direcionamento do atendimento
        try:
            is_bot_responder = _pode_bot_responder_atendimento(mensagem.atendimento)
            direcionamento = "BOT" if is_bot_responder else "HUMANO"

            if is_bot_responder:
                # TODO: Implementar geração de resposta automática do bot
                # Esta é uma funcionalidade crítica que deve ser implementada
                # Exemplo de implementação:
                # try:
                #     from smart_core_assistant_painel.modules.ai_engine.features.features_compose import FeaturesCompose
                #     resposta = FeaturesCompose.gerar_resposta_automatica(mensagem)
                #     if resposta:
                #         mensagem.resposta_bot = resposta
                #         mensagem.respondida = True
                #         mensagem.save(update_fields=['resposta_bot', 'respondida'])
                #         logger.info(f"Resposta automática gerada para mensagem {mensagem_id}")
                # except Exception as e:
                #     logger.error(f"Erro ao gerar resposta automática: {e}")

                pass
            else:
                # Mensagem direcionada para atendente humano
                pass

        except Exception as e:
            logger.error(
                f"Erro ao verificar direcionamento da mensagem {mensagem_id}: {e}"
            )
            # Continua processamento assumindo direcionamento humano por
            # segurança
            is_bot_responder = False
            direcionamento = "HUMANO (por erro)"

        # Resposta de sucesso
        return JsonResponse(
            {
                "status": "success",
                "mensagem_id": mensagem_id,
                "direcionamento": direcionamento.lower(),
            },
            status=200,
        )

    except Exception as e:
        # Log detalhado do erro para debugging
        logger.error(f"Erro crítico no webhook WhatsApp: {e}", exc_info=True)
        return JsonResponse({"error": "Erro interno do servidor"}, status=500)


def _obter_entidades_metadados_validas() -> set[str]:
    """
    Obtém as entidades válidas para metadados do contato a partir do SERVICEHUB.

    Esta função extrai dinamicamente as entidades que devem ser armazenadas
    nos metadados do contato, baseando-se na configuração centralizada do sistema.
    Remove entidades que já são cadastradas automaticamente (contato, telefone).

    Returns:
        set[str]: Conjunto de entidades válidas para metadados

    Examples:
        >>> entidades = _obter_entidades_metadados_validas()
        >>> 'email' in entidades
        True
        >>> 'contato' in entidades  # Contato vai para o campo nome, não metadados
        False
    """
    try:
        # Obtém configuração de entidades válidas do SERVICEHUB
        valid_entity_types = SERVICEHUB.VALID_ENTITY_TYPES

        if not valid_entity_types:
            logger.warning("SERVICEHUB.VALID_ENTITY_TYPES não configurado")
            return set()

        # Parse do JSON das entidades válidas
        import json

        entidades_validas: set[str] = set()

        entidades_config = json.loads(valid_entity_types)

        # Extrai todas as entidades de todas as categorias
        if isinstance(entidades_config, dict) and "entity_types" in entidades_config:
            for categoria, entidades in entidades_config["entity_types"].items():
                if isinstance(entidades, dict):
                    entidades_validas.update(entidades.keys())

        # Remove entidades que não devem ir para metadados
        # Já cadastrado no recebimento da mensagem
        entidades_validas.discard("contato")
        entidades_validas.discard("telefone")
        logger.info(f"Entidades válidas para metadados: {entidades_validas}")
        return entidades_validas

    except Exception as e:
        logger.error(f"Erro ao obter entidades válidas do SERVICEHUB: {e}")
        return set()


def _processar_entidades_contato(
    mensagem: "Mensagem", entity_types: list[dict[str, Any]]
) -> None:
    """
    Processa entidades extraídas para atualizar dados do contato.

    Esta função analisa as entidades extraídas da mensagem e atualiza
    automaticamente os dados do contato conforme encontra informações relevantes.

    Comportamento:
    - Se encontra entidade "contato", atualiza o campo nome do contato (caso esteja vazio)
    - Para outras entidades com dados do contato (contato, email, cpf, etc.),
      salva nos metadados do contato
    - Se o nome do contato ainda não está salvo, pode ser solicitado via nova mensagem

    Args:
        mensagem (Mensagem): Instância da mensagem analisada
        entity_types (list[dict[str, Any]]): Lista de entidades extraídas
            Formato esperado: [{"tipo_entidade": "valor_extraido"}, ...]

    Returns:
        None: A função atualiza diretamente o contato no banco de dados

    Examples:
        >>> entity_types = [
        ...     {"contato": "João Silva"},
        ...     {"email": "joao@email.com"},
        ...     {"telefone": "(11) 99999-9999"}
        ... ]
        >>> _processar_entidades_contato(mensagem, entity_types)
        # Contato terá nome="João Silva" e metadados com email e telefone
    """
    try:
        atendimento = cast(Atendimento, mensagem.atendimento)
        contato = cast(Contato, atendimento.contato)
        contato_atualizado = False
        metadados_atualizados = False

        # Obter entidades válidas para metadados dinamicamente
        entidades_metadados = _obter_entidades_metadados_validas()

        for entidade_dict in entity_types:
            for tipo_entidade, valor in entidade_dict.items():
                # Processar entidade "contato" para atualizar nome
                if tipo_entidade.lower() == "nome_contato" and valor:
                    # Só atualiza nome se estiver vazio ou se novo nome for
                    # mais completo
                    if not contato.nome_contato or len(valor.strip()) > len(
                        contato.nome_contato or ""
                    ):
                        nome_limpo = valor.strip()
                        if nome_limpo and len(nome_limpo) >= 2:  # Validação básica
                            contato.nome_contato = nome_limpo
                            contato_atualizado = True

                # Processar outras entidades para metadados
                elif tipo_entidade.lower() in entidades_metadados and valor:
                    valor_limpo = valor.strip() if isinstance(valor, str) else valor
                    if valor_limpo:
                        # Atualizar metadados do contato
                        if not contato.metadados:
                            contato.metadados = {}

                        # Evitar duplicatas - só atualiza se não existe ou
                        # valor é diferente
                        if (
                            tipo_entidade.lower() not in contato.metadados
                            or contato.metadados[tipo_entidade.lower()] != valor_limpo
                        ):
                            contato.metadados[tipo_entidade.lower()] = valor_limpo
                            metadados_atualizados = True

        # Salvar contato se houve alterações
        if contato_atualizado or metadados_atualizados:
            update_fields = []
            if contato_atualizado:
                update_fields.append("nome_contato")
            if metadados_atualizados:
                update_fields.append("metadados")

            # Atualizar timestamp da última interação quando dados são
            # atualizados
            contato.ultima_interacao = timezone.now()
            update_fields.append("ultima_interacao")

            contato.save(update_fields=update_fields)

            # Se ainda não há nome do contato, solicitar dados
            if not contato.nome_contato:
                features = FeaturesCompose()
                features.solicitacao_info_cliene()

    except Exception as e:
        logger.error(f"Erro ao processar entidades do contato: {e}")
        # Não interrompe o fluxo em caso de erro
        pass


def _analisar_conteudo_mensagem(mensagem_id: int) -> None:
    """
    Análise prévia do conteúdo da mensagem para detectar intent e extrair entidades.

    Esta função utiliza o sistema de IA para analisar o conteúdo textual da mensagem,
    identificando a intenção do usuário e extraindo entidades relevantes. É uma etapa
    crítica para melhorar a compreensão do contexto e direcionamento das respostas.

    Args:
        mensagem (Mensagem): Instância da mensagem a ser analisada.
            Deve conter o campo 'conteudo' com texto a ser analisado.

    Returns:
        None: A função atualiza a mensagem diretamente no banco de dados.

    Raises:
        Exception: Capturada internamente e logada. Função não retorna valor
            em caso de erro, mas garante que o processamento continue.

    Notes:
        - Implementação planejada para análise de intent e entidades
        - Base para futuras melhorias na experiência do usuário
        - Logs de erro são gerados para facilitar troubleshooting

    Examples:
        >>> mensagem = Mensagem.objects.get(id=123)
        >>> _analisar_conteudo_mensagem(mensagem)
    """

    try:
        features = FeaturesCompose()
        mensagem: Mensagem = Mensagem.objects.get(id=mensagem_id)
        atendimento: Atendimento = cast(Atendimento, mensagem.atendimento)
        exists_atendimento_anterior = Atendimento.objects.filter(contato=atendimento.contato).exclude(id=atendimento.id).exists()
        # Carrega historico EXCLUINDO a mensagem atual para análise de contexto
        historico_atendimento = atendimento.carregar_historico_mensagens(excluir_mensagem_id=mensagem_id)
        # Se não há atendimentos anteriores, nem mensagens anteriores no histórico do atendimento atual, chama apresentação
        if not exists_atendimento_anterior:
            if not historico_atendimento.get("conteudo_mensagens"):
                features.mensagem_apresentacao()

        # Análise de intenção e extração de entidades
        resultado_analise = features.analise_previa_mensagem(
            historico_atendimento=historico_atendimento, context=mensagem.conteudo
        )
        mensagem.intent_detectado = resultado_analise.intent_types
        mensagem.entidades_extraidas = resultado_analise.entity_types

        mensagem.save(update_fields=["intent_detectado", "entidades_extraidas"])

        # Processar entidades para atualizar dados do contato
        _processar_entidades_contato(mensagem, resultado_analise.entity_types)

    except Exception as e:
        logger.error(f"Erro ao analisar conteúdo da mensagem {mensagem_id}: {e}")
        # Continua processamento mesmo com erro na análise
        # Não interrompe o fluxo para garantir resiliência
        pass


def _pode_bot_responder_atendimento(atendimento):
    """
    Verifica se o bot pode responder automaticamente em um atendimento específico.

    O bot não deve responder se há mensagens de atendente humano no atendimento
    ou se um atendente humano está associado ao atendimento, garantindo que
    a experiência do usuário não seja comprometida por respostas conflitantes.

    Args:
        atendimento (Atendimento): Instância do atendimento a ser verificado.
            Deve conter as relações 'mensagens' e 'atendente_humano'.

    Returns:
        bool: True se o bot pode responder automaticamente, False caso contrário.
            Retorna False também em caso de erro durante a verificação.

    Raises:
        Exception: Capturada internamente e logada. Função retorna False
            em caso de erro para garantir segurança operacional.

    Notes:
        - A verificação inclui tanto mensagens quanto associação direta de atendente
        - Em caso de erro, assume-se comportamento conservador (False)
        - Logs de erro são gerados para facilitar troubleshooting

    Examples:
        >>> atendimento = Atendimento.objects.get(id=123)
        >>> pode_responder = _pode_bot_responder_atendimento(atendimento)
        >>> if pode_responder:
        ...     # Bot pode responder automaticamente
        ...     pass
    """
    from .models import TipoRemetente

    try:
        # Verifica se existe alguma mensagem de atendente humano neste
        # atendimento ou se o atendimento tem um atendente humano associado
        mensagens_atendente = (
            atendimento.mensagens.filter(
                remetente=TipoRemetente.ATENDENTE_HUMANO
            ).exists()
            or atendimento.atendente_humano is not None
        )

        return not mensagens_atendente
    except Exception as e:
        logger.error(f"Erro ao verificar se bot pode responder: {e}")
        return False


def _converter_contexto(metadata: dict[str, Any]) -> str:
    """
    Converte metadados de mensagens multimídia para texto formatado legível.

    Esta função processa os metadados de mensagens não textuais (imagens,
    áudios, documentos, vídeos, stickers, etc.) e os converte em uma
    representação textual que pode ser compreendida e processada pelo
    sistema de IA para geração de respostas contextuais apropriadas.

    Args:
        metadata (dict): Dicionário contendo os metadados da mensagem.
            Estrutura típica inclui:
            - 'type': Tipo da mídia (image, audio, document, etc.)
            - 'mime_type'/'mimetype': Tipo MIME do arquivo
            - 'size'/'fileLength': Tamanho do arquivo em bytes
            - 'url': URL para download do arquivo
            - 'fileName': Nome original do arquivo
            - Campos específicos por tipo (duration, dimensions, etc.)

    Returns:
        str: Texto formatado representando o contexto da mensagem.
            Exemplos de retorno futuro:
            - "Imagem JPEG de 2.1MB (1920x1080)"
            - "Áudio MP3 de 45 segundos"
            - "Documento PDF: 'Relatório_Mensal.pdf' (856KB)"
            - "Vídeo MP4 de 2min30s (1280x720)"

    Raises:
        Exception: Repassada para o chamador em caso de erro na conversão.
            Logs de erro são gerados automaticamente para debugging.

    Implementation Status:
        - ATUAL: Retorna placeholder 'contexto' para todos os tipos
        - PLANEJADO: Conversão específica por tipo de mídia
        - FUTURO: Integração com análise de conteúdo por IA

    Processing Logic (Futuro):
        1. Identificar tipo de mídia pelos metadados
        2. Extrair informações relevantes (tamanho, formato, duração)
        3. Formatar texto descritivo apropriado
        4. Adicionar contexto específico quando possível

    Notes:
        - Função crítica para suporte completo a mensagens multimídia
        - Permite que o bot compreenda e responda a qualquer tipo de mensagem
        - Essencial para experiência de usuário completa no WhatsApp
        - Base para futuras funcionalidades de análise de conteúdo

    Examples:
        >>> # Imagem
        >>> metadata = {
        ...     "type": "image",
        ...     "mimetype": "image/jpeg",
        ...     "fileLength": 2048000,
        ...     "url": "https://example.com/image.jpg"
        ... }
        >>> _converter_contexto(metadata)
        'contexto'  # Atual
        # 'Imagem JPEG de 2MB'  # Implementação futura

        >>> # Áudio
        >>> metadata = {
        ...     "type": "audio",
        ...     "mimetype": "audio/ogg",
        ...     "seconds": 45,
        ...     "ptt": True
        ... }
        >>> _converter_contexto(metadata)
        'contexto'  # Atual
        # 'Mensagem de voz de 45 segundos'  # Implementação futura

        >>> # Documento
        >>> metadata = {
        ...     "type": "document",
        ...     "fileName": "Contrato_2025.pdf",
        ...     "mimetype": "application/pdf",
        ...     "fileLength": 856000
        ... }
        >>> _converter_contexto(metadata)
        'contexto'  # Atual
        # 'Documento PDF: Contrato_2025.pdf (856KB)'  # Implementação futura
    """
    try:
        # TODO: Implementar lógica específica de conversão por tipo de mídia
        #
        # Estrutura planejada:
        # if not metadata:
        #     return "Conteúdo sem metadados"
        #
        # media_type = metadata.get('type', 'unknown')
        #
        # if media_type == 'image':
        #     return _processar_contexto_imagem(metadata)
        # elif media_type == 'audio':
        #     return _processar_contexto_audio(metadata)
        # elif media_type == 'document':
        #     return _processar_contexto_documento(metadata)
        # elif media_type == 'video':
        #     return _processar_contexto_video(metadata)
        # else:
        #     return f"Conteúdo do tipo {media_type}"

        # Implementação atual: placeholder
        return "contexto"

    except Exception as e:
        logger.error(f"Erro ao converter contexto: {e}")
        raise e


def _validar_api_key(api_key: str) -> bool:
    """
    Valida se a API key fornecida é válida para autenticação do webhook.

    Esta função verifica se a API key enviada no payload do webhook é válida
    e tem permissão para enviar mensagens para o sistema. Implementa uma
    camada de segurança essencial para evitar chamadas não autorizadas.

    Args:
        api_key (str): Chave de API a ser validada. Pode vir do campo
            'apikey' no payload do webhook ou de headers HTTP.

    Returns:
        bool: True se a API key é válida e autorizada, False caso contrário.
            Comportamento atual: aceita qualquer key não vazia (desenvolvimento).

    Security Considerations:
        - API keys devem ser únicas por instância/cliente
        - Recomenda-se uso de hashing ou assinatura digital
        - Implementar rate limiting por API key
        - Logs de tentativas de acesso inválidas
        - Rotação periódica de chaves em produção

    Implementation Roadmap:
        - ATUAL: Validação básica (não vazia)
        - FASE 1: Validação contra banco de dados
        - FASE 2: Assinatura digital HMAC-SHA256
        - FASE 3: Rate limiting e blacklist
        - FASE 4: Rotação automática de chaves

    Notes:
        - TODO: Implementar validação real de API key
        - Considerar implementar verificação em banco de dados ou cache
        - Importante para segurança em ambiente de produção
        - Deve integrar com sistema de monitoramento de segurança

    Examples:
        >>> # Validação básica atual
        >>> api_key = "abc123def456"
        >>> if _validar_api_key(api_key):
        ...     # Processar webhook
        ...     pass

        >>> # API key vazia (rejeitada)
        >>> _validar_api_key("")
        False

        >>> # Implementação futura com HMAC
        >>> # import hmac, hashlib
        >>> # def _validar_api_key_hmac(api_key, payload, secret):
        >>> #     expected = hmac.new(
        >>> #         secret.encode(),
        >>> #         payload.encode(),
        >>> #         hashlib.sha256
        >>> #     ).hexdigest()
        >>> #     return hmac.compare_digest(expected, api_key)
    """
    # TODO: Implementar validação real de API key
    #
    # Exemplo de implementação robusta:
    #
    # 1. Validação em banco de dados:
    # try:
    #     api_config = APIKey.objects.get(
    #         key=api_key,
    #         ativo=True,
    #         expires_at__gt=timezone.now()
    #     )
    #     # Atualizar último uso
    #     api_config.ultimo_uso = timezone.now()
    #     api_config.save(update_fields=['ultimo_uso'])
    #     return True
    # except APIKey.DoesNotExist:
    #     logger.warning(f"API key inválida tentou acesso: {api_key[:8]}...")
    #     return False
    #
    # 2. Validação com assinatura HMAC:
    # secret = settings.WEBHOOK_SECRET
    # return hmac.compare_digest(
    #     expected_signature,
    #     hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    # )

    if not api_key:
        return False

    # Implementação temporária para desenvolvimento
    # Em produção, substituir por validação real
    return True
