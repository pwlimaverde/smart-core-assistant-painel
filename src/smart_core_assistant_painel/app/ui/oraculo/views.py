import os
import tempfile

from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render
from langchain.docstore.document import Document
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
    def processar_conteudo_texto(
            treinamento_id,
            conteudo,
            tag,
            grupo) -> list[Document]:
        """Processa conteúdo de texto para treinamento"""
        if not conteudo:
            raise ValueError("Conteúdo não pode ser vazio")

        try:
            pre_analise_conteudo = FeaturesCompose.pre_analise_ia_treinamento(
                conteudo)
            data_conteudo = FeaturesCompose.load_document_conteudo(
                id=treinamento_id,
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
            treinamento_id, documento_path, tag, grupo) -> list[Document]:
        """Processa arquivo de documento para treinamento"""
        if not documento_path:
            raise ValueError("Caminho do documento não pode ser vazio")

        try:
            data_file = FeaturesCompose.load_document_file(
                id=treinamento_id,
                path=documento_path,
                tag=tag,
                grupo=grupo,
            )

            for documento in data_file:
                # Apenas modificar o page_content do documento existente
                pre_analise_content = FeaturesCompose.pre_analise_ia_treinamento(
                    documento.page_content)

                # Modificar diretamente o page_content
                documento.page_content = pre_analise_content

            return data_file

        except Exception as e:
            logger.error(f"Erro ao processar arquivo documento: {e}")
            raise e

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
            treinamento.set_documentos(documents_list)
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

    if request.method == 'GET':
        return _exibir_pre_processamento(request, id)

    if request.method == 'POST':
        return _processar_pre_processamento(request, id)


def _exibir_pre_processamento(request, id):
    """Exibe página de pré-processamento"""
    try:
        treinamento = Treinamentos.objects.get(id=id)
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


def _processar_pre_processamento(request, id):
    """Processa ação do pré-processamento"""
    treinamento = Treinamentos.objects.get(id=id)
    acao = request.POST.get('acao')

    if not acao:
        messages.error(request, 'Ação não especificada.')
        return redirect('pre_processamento', id=treinamento.id)

    try:
        with transaction.atomic():
            if acao == 'aceitar':
                _aceitar_treinamento(id)
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


def _aceitar_treinamento(id):
    """Aceita treinamento e atualiza conteúdo melhorado individualmente para cada documento"""
    try:
        # Processa documentos - agora sempre será uma lista (JSONField)
        treinamento = Treinamentos.objects.get(id=id)
        documentos_lista = treinamento.get_documentos()

        if not documentos_lista:
            logger.warning(
                f"Nenhum documento encontrado para treinamento {
                    treinamento.id}")
            return

        documentos_melhorados = []

        for documento in documentos_lista:
            # Apenas modificar o page_content do documento existente
            pre_analise_content = FeaturesCompose.pre_analise_ia_treinamento(
                documento.page_content)

            # Modificar diretamente o page_content
            documento.page_content = pre_analise_content

            documentos_melhorados.append(documento)

        # Salva alterações
        treinamento.set_documentos(documentos_melhorados)
        treinamento.treinamento_finalizado = True
        treinamento.save()

        logger.info(
            f"Treinamento {
                treinamento.id} aceito com {
                len(documentos_melhorados)} documentos melhorados")

    except Exception as e:
        logger.error(f"Erro ao aceitar treinamento {treinamento.id}: {e}")
        raise
