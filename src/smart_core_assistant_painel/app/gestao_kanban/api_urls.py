"""URLs JSON do Gestão Kanban (sob /workspace/kanban/api/)."""

from __future__ import annotations

from django.urls import path

from . import views_api

urlpatterns = [
    path(
        "fluxos/",
        views_api.FluxosListView.as_view(),
        name="fluxos_list",
    ),
    path(
        "board/",
        views_api.BoardSnapshotView.as_view(),
        name="board_snapshot",
    ),
    path(
        "board/move/",
        views_api.BoardMoveView.as_view(),
        name="board_move",
    ),
    path(
        "board/assign/",
        views_api.BoardAssignView.as_view(),
        name="board_assign",
    ),
    path(
        "board/transfer-fluxo/",
        views_api.BoardTransferFluxoView.as_view(),
        name="board_transfer_fluxo",
    ),
    path(
        "conversations/<int:atendimento_id>/custom-fields/<slug:slug>/",
        views_api.CustomFieldPatchView.as_view(),
        name="custom_field_patch",
    ),
    path(
        "export/",
        views_api.ExportView.as_view(),
        name="export",
    ),
    path(
        "etiquetas/",
        views_api.EtiquetasListView.as_view(),
        name="etiquetas_list",
    ),
    path(
        "conversations/<int:atendimento_id>/etiquetas/",
        views_api.ConversationEtiquetasView.as_view(),
        name="conversation_etiquetas",
    ),
    path(
        "conversations/<int:atendimento_id>/etiquetas/<int:etiqueta_id>/toggle/",
        views_api.ConversationEtiquetaToggleView.as_view(),
        name="conversation_etiqueta_toggle",
    ),
    path(
        "conversations/<int:atendimento_id>/notas/",
        views_api.ConversationNotasView.as_view(),
        name="conversation_notas",
    ),
    path(
        "conversations/<int:atendimento_id>/notas/<int:nota_id>/",
        views_api.ConversationNotaDeleteView.as_view(),
        name="conversation_nota_delete",
    ),
    path(
        "conversations/<int:atendimento_id>/timeline/",
        views_api.ConversationTimelineView.as_view(),
        name="conversation_timeline",
    ),
]
