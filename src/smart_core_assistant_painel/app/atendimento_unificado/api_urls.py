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
]
