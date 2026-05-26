"""Modelos do shell de Atendimento Unificado.

O shell é **apenas a ponte/UI** que une a visualização de chat e kanban — não
possui modelos de domínio próprios (refatoração modular v6.0).

Os models de informação foram **consolidados no centro** `atendimentos.models`
(migration state-only, tabelas `atu_*` preservadas):

- ``CampoPersonalizado``, ``ValorCampoAtendimento``, ``Etiqueta``,
  ``EtiquetaAtendimento``, ``Nota`` → ``atendimentos.models``

O controle de leitura por atendente (``LeituraAtendimento``) foi **removido**:
os não-lidos usam ``Mensagem.lido`` (fonte da verdade, sem multiatendente).
"""
