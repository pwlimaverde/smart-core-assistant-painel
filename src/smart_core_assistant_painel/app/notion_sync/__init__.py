"""
App de sincronização com plataformas externas (Notion, Airtable, etc).

Este módulo implementa uma arquitetura em 3 camadas para sincronização
bidirecional de dados entre Django e plataformas externas, mantendo
o Django como fonte primária de verdade.

Arquitetura:
    - Interface Abstrata: Define o contrato para qualquer serviço externo
    - Models de Tracking: Armazenam metadados de sincronização
    - Services: Implementações concretas (Notion, Airtable, etc)
    - Signals: Capturam mudanças nos models principais
    - Mappers: Conversão de dados Django ↔ Plataforma Externa
"""

default_app_config = "smart_core_assistant_painel.app.notion_sync.apps.NotionSyncConfig"
