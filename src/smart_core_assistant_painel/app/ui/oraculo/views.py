import json
import os
import tempfile

from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render
from loguru import logger
from rolepermissions.checkers import has_permission

from smart_core_assistant_painel.modules.ai_engine.features.features_compose import (
    FeaturesCompose, )

from .models import Treinamentos


class TreinamentoService:
    """Serviço para gerenciar operações de treinamento"""

    @staticmethod
    def processar_arquivo_upload(arquivo):
        """Processa arquivo uploadado e retorna caminho temporário"""
        if not arquivo:
            return None

        try:
            return arquivo.temporary_file_path()
        except AttributeError:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=os.path.splitext(arquivo.name)[1]
            ) as temp_file:
                for chunk in arquivo.chunks():
                    temp_file.write(chunk)
                return temp_file.name

    @staticmethod
    def processar_conteudo_texto(treinamento_id, conteudo, tag, grupo):
        """Processa conteúdo de texto para treinamento"""
        if not conteudo:
            return []

        try:
            pre_analise_conteudo = FeaturesCompose.pre_analise_ia_treinamento(
                conteudo)
            data_conteudo = FeaturesCompose.load_document_conteudo(
                id=treinamento_id,
                conteudo=pre_analise_conteudo,
                tag=tag,
                grupo=grupo,
            )
            return json.loads(data_conteudo) if data_conteudo else []
        except Exception as e:
            logger.error(f"Erro ao processar conteúdo texto: {e}")
            return []

    @staticmethod
    def processar_arquivo_documento(
            treinamento_id, documento_path, tag, grupo):
        """Processa arquivo de documento para treinamento"""
        if not documento_path:
            return []

        try:
            data_file = FeaturesCompose.load_document_file(
                id=treinamento_id,
                path=documento_path,
                tag=tag,
                grupo=grupo,
            )

            doc_dict = json.loads(data_file)
            documents_list = []

            for documento_str in doc_dict:
                documento = json.loads(documento_str)

                if 'page_content' in documento:
                    pre_analise_content = FeaturesCompose.pre_analise_ia_treinamento(
                        documento['page_content'])
                    documento['page_content'] = pre_analise_content

                documents_list.append(documento)

            return documents_list
        except Exception as e:
            logger.error(f"Erro ao processar arquivo documento: {e}")
            return []

    @staticmethod
    def limpar_arquivo_temporario(arquivo_path):
        """Remove arquivo temporário se existir"""
        if arquivo_path and os.path.exists(arquivo_path):
            try:
                os.unlink(arquivo_path)
            except OSError as e:
                logger.warning(
                    f"Erro ao remover arquivo temporário {arquivo_path}: {e}")


def treinar_ia(request):
    """View para treinamento de IA"""
    if not has_permission(request.user, 'treinar_ia'):
        raise Http404()

    if request.method == 'GET':
        return render(request, 'treinar_ia.html')

    if request.method == 'POST':
        return _processar_treinamento(request)


def _processar_treinamento(request):
    """Processa dados de treinamento enviados via POST"""
    tag = request.POST.get('tag')
    grupo = request.POST.get('grupo')
    conteudo = request.POST.get('conteudo')
    documento = request.FILES.get('documento')

    # Validações básicas
    if not tag or not grupo:
        messages.error(request, 'Tag e Grupo são obrigatórios.')
        return render(request, 'treinar_ia.html')

    if not conteudo and not documento:
        messages.error(request, 'É necessário fornecer conteúdo ou documento.')
        return render(request, 'treinar_ia.html')

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
                documento_path = TreinamentoService.processar_arquivo_upload(
                    documento)
                if documento_path:
                    docs_arquivo = TreinamentoService.processar_arquivo_documento(
                        treinamento.id, documento_path, tag, grupo)
                    documents_list.extend(docs_arquivo)

            # Processar conteúdo de texto se fornecido
            if conteudo:
                docs_conteudo = TreinamentoService.processar_conteudo_texto(
                    treinamento.id, conteudo, tag, grupo
                )
                documents_list.extend(docs_conteudo)

            # Salvar documentos processados
            treinamento.documentos = documents_list
            treinamento.save()

            messages.success(request, 'Treinamento criado com sucesso!')
            return redirect('pre_processamento', id=treinamento.id)

    except Exception as e:
        logger.error(f"Erro ao processar treinamento: {e}")
        messages.error(request, 'Erro interno do servidor. Tente novamente.')
        return render(request, 'treinar_ia.html')

    finally:
        # Limpar arquivo temporário
        TreinamentoService.limpar_arquivo_temporario(documento_path)


def pre_processamento(request, id):
    """View para pré-processamento de treinamento"""
    if not has_permission(request.user, 'treinar_ia'):
        raise Http404()

    try:
        treinamento = Treinamentos.objects.get(id=id)
    except Treinamentos.DoesNotExist:
        messages.error(request, 'Treinamento não encontrado.')
        return redirect('treinar_ia')

    if request.method == 'GET':
        return _exibir_pre_processamento(request, treinamento)

    if request.method == 'POST':
        return _processar_pre_processamento(request, treinamento)


def _exibir_pre_processamento(request, treinamento):
    """Exibe página de pré-processamento"""
    try:
        conteudo_unificado = treinamento.get_conteudo_unificado()
        texto_melhorado = FeaturesCompose.melhoria_ia_treinamento(
            conteudo_unificado)

        return render(request, 'pre_processamento.html', {
            'dados_organizados': treinamento,
            'treinamento': texto_melhorado,
        })
    except Exception as e:
        logger.error(f"Erro ao gerar pré-processamento: {e}")
        messages.error(request, 'Erro ao processar dados de treinamento.')
        return redirect('treinar_ia')


def _processar_pre_processamento(request, treinamento):
    """Processa ação do pré-processamento"""
    acao = request.POST.get('acao')

    if not acao:
        messages.error(request, 'Ação não especificada.')
        return redirect('pre_processamento', id=treinamento.id)

    try:
        with transaction.atomic():
            if acao == 'aceitar':
                _aceitar_treinamento(treinamento)
                messages.success(request, 'Treinamento aceito e finalizado!')
            elif acao == 'manter':
                treinamento.treinamento_finalizado = True
                treinamento.save()
                messages.success(request, 'Treinamento mantido e finalizado!')
            elif acao == 'descartar':
                treinamento.delete()
                messages.info(request, 'Treinamento descartado.')
            else:
                messages.error(request, 'Ação inválida.')
                return redirect('pre_processamento', id=treinamento.id)

    except Exception as e:
        logger.error(f"Erro ao processar ação {acao}: {e}")
        messages.error(request, 'Erro ao processar ação. Tente novamente.')
        return redirect('pre_processamento', id=treinamento.id)

    return redirect('treinar_ia')


def _aceitar_treinamento(treinamento):
    """Aceita treinamento e atualiza conteúdo melhorado individualmente para cada documento"""
    try:
        # Processa documentos - agora sempre será uma lista (JSONField)
        documentos_lista = treinamento.documentos or []

        if not documentos_lista:
            logger.warning(
                f"Nenhum documento encontrado para treinamento {
                    treinamento.id}")
            return

        documentos_melhorados = []

        for doc in documentos_lista:
            documento_dict = json.loads(doc) if isinstance(doc, str) else doc

            # Valida se o documento tem page_content
            if 'page_content' not in documento_dict:
                logger.warning(
                    f"Documento sem page_content no treinamento {
                        treinamento.id}")
                documentos_melhorados.append(documento_dict)
                continue

            # Melhora o conteúdo individual de cada documento
            conteudo_original = documento_dict['page_content']
            if conteudo_original:
                texto_melhorado = FeaturesCompose.melhoria_ia_treinamento(
                    conteudo_original)
                documento_dict['page_content'] = texto_melhorado

            documentos_melhorados.append(documento_dict)

        # Salva alterações
        treinamento.documentos = documentos_melhorados
        treinamento.treinamento_finalizado = True
        treinamento.save()

        logger.info(
            f"Treinamento {
                treinamento.id} aceito com {
                len(documentos_melhorados)} documentos melhorados")

    except Exception as e:
        logger.error(f"Erro ao aceitar treinamento {treinamento.id}: {e}")
        raise
