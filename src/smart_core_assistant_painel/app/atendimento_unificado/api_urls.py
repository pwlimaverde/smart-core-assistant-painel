"""URLs JSON do Workspace (sob /workspace/api/)."""

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
        "conversations/",
        views_api.ConversationsListView.as_view(),
        name="conversations_list",
    ),
    path(
        "conversations/<int:atendimento_id>/messages/",
        views_api.ConversationMessagesView.as_view(),
        name="conversation_messages",
    ),
    path(
        "conversations/<int:atendimento_id>/detail/",
        views_api.ConversationDetailView.as_view(),
        name="conversation_detail",
    ),
    path(
        "conversations/<int:atendimento_id>/send/",
        views_api.ConversationSendView.as_view(),
        name="conversation_send",
    ),
    path(
        "conversations/<int:atendimento_id>/mark-read/",
        views_api.ConversationMarkReadView.as_view(),
        name="conversation_mark_read",
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
        "conversations/<int:atendimento_id>/custom-fields/<slug:slug>/",
        views_api.CustomFieldPatchView.as_view(),
        name="custom_field_patch",
    ),
    path(
        "conversations/<int:atendimento_id>/upload/",
        views_api.ConversationUploadView.as_view(),
        name="conversation_upload",
    ),
    path(
        "export/",
        views_api.ExportView.as_view(),
        name="export",
    ),
    # ─── Notificações / sino ───────────────────────────────────────────
    path(
        "notifications/unread-count/",
        views_api.NotificationsUnreadCountView.as_view(),
        name="notifications_unread_count",
    ),
    # ─── Etiquetas ─────────────────────────────────────────────────────
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
    # ─── Notas internas ────────────────────────────────────────────────
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
    # ─── Mídias e Timeline (sidebar de detalhes) ────────────────────────
    path(
        "conversations/<int:atendimento_id>/medias/",
        views_api.ConversationMediasView.as_view(),
        name="conversation_medias",
    ),
    path(
        "conversations/<int:atendimento_id>/timeline/",
        views_api.ConversationTimelineView.as_view(),
        name="conversation_timeline",
    ),
    # ─── Transferência entre fluxos ────────────────────────────────────
    path(
        "board/transfer-fluxo/",
        views_api.BoardTransferFluxoView.as_view(),
        name="board_transfer_fluxo",
    ),
]
