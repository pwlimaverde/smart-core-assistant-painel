"""URLs JSON do Chat Evolution (sob /workspace/chat/api/)."""

from __future__ import annotations

from django.urls import path

# Por enquanto as views ainda residem em atendimento_unificado
# Serão movidas no próximo passo da refatoração
from smart_core_assistant_painel.app.atendimento_unificado import views_api

urlpatterns = [
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
        "conversations/<int:atendimento_id>/presence/",
        views_api.ConversationPresenceView.as_view(),
        name="conversation_presence",
    ),
    path(
        "conversations/<int:atendimento_id>/upload/",
        views_api.ConversationUploadView.as_view(),
        name="conversation_upload",
    ),
    path(
        "conversations/<int:atendimento_id>/medias/",
        views_api.ConversationMediasView.as_view(),
        name="conversation_medias",
    ),
    path(
        "notifications/unread-count/",
        views_api.NotificationsUnreadCountView.as_view(),
        name="notifications_unread_count",
    ),
]
