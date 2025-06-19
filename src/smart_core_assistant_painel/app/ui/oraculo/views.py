import json

from django.http import Http404
from django.shortcuts import redirect, render
from loguru import logger
from rolepermissions.checkers import has_permission

from smart_core_assistant_painel.app.features.features_compose import FeaturesCompose
from smart_core_assistant_painel.app.ui.oraculo.utils import (
    gerar_documentos,
)

from .models import Treinamentos


def treinar_ia(request):
    if not has_permission(request.user, 'treinar_ia'):
        raise Http404()
    if request.method == 'GET':
        return render(request, 'treinar_ia.html')
    elif request.method == 'POST':
        tag = request.POST.get('tag')
        grupo = request.POST.get('grupo')
        conteudo = request.POST.get('conteudo')
        documento = request.FILES.get('documento')
        treinamento = Treinamentos(
            tag=tag,
            grupo=grupo,
        )
        treinamento.save()

        documento_path = None
        if documento:
            try:
                # Tenta obter o path temporário (para arquivos grandes)
                documento_path = documento.temporary_file_path()
            except AttributeError:
                # Para arquivos em memória, criar arquivo temporário
                import os
                import tempfile

                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(documento.name)[1]) as temp_file:
                    for chunk in documento.chunks():
                        temp_file.write(chunk)
                    documento_path = temp_file.name

        conteudo_processado = gerar_documentos(
            id=treinamento.id,
            path=documento_path if documento else None,
            tag=tag,
            grupo=grupo,
            conteudo=conteudo,
        )

        treinamento.documento = conteudo_processado
        treinamento.save()
        if documento_path and os.path.exists(documento_path):
            os.unlink(documento_path)

        return redirect('pre_processamento', id=treinamento.id)


def pre_processamento(request, id):
    treinamento_id = id
    dados = Treinamentos.objects.get(id=treinamento_id)
    texto_melhorado = FeaturesCompose.melhoria_ia_treinamento(
        dados.conteudo['page_content'])
    logger.info(f"Documento Carregado✅ {dados.conteudo}")
    logger.info(f"Texto melhorado✅ {texto_melhorado}")
    if not has_permission(request.user, 'treinar_ia'):
        raise Http404()
    if request.method == 'GET':

        return render(
            request, 'pre_processamento.html', {
                'dados_organizados': dados.conteudo,
                'treinamento': texto_melhorado,
            })
    elif request.method == 'POST':
        acao = request.POST.get('acao')

        if acao == 'aceitar':
            documento_dict = json.loads(dados.documento)
            documento_dict['page_content'] = texto_melhorado
            dados.documento = json.dumps(documento_dict)
            dados.treinamento_finalizado = True
            dados.save()
        elif acao == 'manter':
            dados.treinamento_finalizado = True
            dados.save()
        elif acao == 'descartar':
            dados.delete()

        return redirect('treinar_ia')


# @csrf_exempt
# def chat(request):
#     if request.method == 'GET':
#         return render(request, 'chat.html')
#     elif request.method == 'POST':
#         # TODO: Tarefa 6 - Criar uma pergunta
#         ...

# @csrf_exempt
# def stream_response(request):
#     # TODO: Usar IA para obter a resposta e enviar em tempo real
#     ...

# def ver_fontes(request, id):
#     return render(request, 'ver_fontes.html')
