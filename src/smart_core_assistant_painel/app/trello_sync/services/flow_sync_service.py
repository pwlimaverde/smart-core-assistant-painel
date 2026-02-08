from typing import Any, Optional

from decouple import config
from django.db import router, transaction
from loguru import logger

from smart_core_assistant_painel.app.trello_sync.models import (
    TrelloBoard,
    TrelloList,
)
from smart_core_assistant_painel.app.operacional.models import (
    FluxoAtendimento,
    EtapaFluxo,
)
from smart_core_assistant_painel.modules.services import (
    SERVICEHUB,
    FeaturesCompose,
)
from smart_core_assistant_painel.modules.services.features.unifield_data_services.domain.interface.unified_data_service import (
    UnifiedDataService,
)


class FlowSyncService:
    """[TRL-FLW-001] Serviço de sincronização de fluxo (Departamento/Etapas → Board/Lists).

    Geração Automática de Quadros e Listas.

    Comentário: usa TrelloUnifiedDataService para criar artefatos.
    """

    def __init__(self) -> None:
        # Comentário (PT-BR): Obtém o UDS do SERVICEHUB. Se não estiver
        # inicializado, executa o compose para registrar a instância.
        try:
            self.client: UnifiedDataService = SERVICEHUB.unified_data_service
        except Exception:
            FeaturesCompose.unifield_data_services()
            self.client = SERVICEHUB.unified_data_service

    def _callback_url(self, tenant_slug: Optional[str] = None) -> str:
        """Constrói URL de callback para webhook Trello.

        Comentário (PT-BR): URL pública para receber webhooks.
        Se tenant_slug for fornecido, inclui na URL para garantir
        que o webhook seja processado no contexto correto do tenant.

        Args:
            tenant_slug: Slug do tenant para incluir na URL.

        Returns:
            URL completa com tenant_slug, se fornecido.
        """
        base_url: str = config(
            "TRELLO_WEBHOOK_CALLBACK_URL",
            default="http://localhost:8000/api/trello_sync/webhook/",
        )

        # Remove trailing slash para normalização
        base_url = base_url.rstrip("/")

        if tenant_slug:
            return f"{base_url}/{tenant_slug}/"

        return f"{base_url}/"

    def _should_register_webhook(self, callback_url: str) -> bool:
        """Decide se o webhook deve ser registrado.

        Comentário (PT-BR): Por padrão, evitamos registrar webhooks quando
        a URL é local (localhost/127.0.0.1), pois o Trello valida o endpoint
        publicamente acessível e retorna 400 se não conseguir alcançar.
        Pode-se forçar via `TRELLO_ENABLE_WEBHOOKS=true`.
        """
        enable_flag: str = config("TRELLO_ENABLE_WEBHOOKS", default="auto")
        flag = enable_flag.strip().lower()

        # Detecção simples de URL local
        is_local: bool = (
            "localhost" in callback_url or "127.0.0.1" in callback_url
        )

        if flag in {"true", "1", "yes"}:
            return True
        if flag in {"false", "0", "no"}:
            return False
        # Modo "auto": evita registrar se URL for local
        return not is_local

    def ensure_board_for_fluxo(
        self, fluxo: Any, name: Optional[str] = None
    ) -> TrelloBoard:
        """
        Garante board Trello para um FluxoAtendimento e registra webhook.
        """
        # 1. Verificação rápida (sem lock)
        existing: Optional[TrelloBoard] = getattr(fluxo, "trello_board", None)
        if existing:
            return existing

        # 2. Lock no Fluxo para garantir serialização
        # Precisamos importar FluxoAtendimento para o get, ou usar type(fluxo)
        # Assumindo que 'fluxo' é instância de FluxoAtendimento.
        # Mas para garantir, vamos usar o ID.
        fluxo_id = getattr(fluxo, "id", None)
        if not fluxo_id:
            raise ValueError("Fluxo sem ID")

        with transaction.atomic(using=router.db_for_write(FluxoAtendimento)):
            # Re-busca o fluxo com lock para bloquear outros processos
            # Importante: select_for_update bloqueia a linha até o fim da transação
            fluxo_locked = FluxoAtendimento.objects.select_for_update().get(
                id=fluxo_id
            )

            # 3. Verificação pós-lock (Double-Check Locking)
            # Tenta buscar o board novamente via DB para garantir que não foi criado
            # enquanto esperávamos o lock.
            existing_locked = TrelloBoard.objects.filter(
                fluxo=fluxo_locked
            ).first()
            if existing_locked:
                return existing_locked

            # 4. Criação do Board (API + DB)
            # Nota: Chamada de API dentro de transação segura o lock por mais tempo,
            # mas é necessário para evitar a race condition de criação duplicada no Trello.

            board_id_trello: str = self.client.create_container(
                name or fluxo_locked.nome
            )

            # Após criar, buscar dados do board para preencher metadados.
            data: Optional[dict[str, Any]] = self.client.get_container(
                board_id_trello
            )
            board_data: dict[str, Any] = data if isinstance(data, dict) else {}

            board: TrelloBoard = TrelloBoard.objects.create(
                fluxo=fluxo_locked,
                external_id=board_id_trello,
                name=board_data.get("name", name or fluxo_locked.nome),
                url=board_data.get("shortUrl"),
                metadata=board_data,
            )

        # Comentário: Webhook agora é registrado via task assíncrona (task_fluxo_ensure_board)
        # para garantir robustez e retry, removendo a lógica inline daqui.
        # Comentário: após criar o board, garantir listas para etapas já existentes
        try:
            etapas = getattr(fluxo, "etapas", None)
            if etapas is not None:
                for etapa in etapas.all():
                    try:
                        self.ensure_list_for_etapa(etapa)
                    except Exception as exc:
                        logger.warning(
                            "Falha ao garantir lista para etapa {id}: {}",
                            exc,
                            id=getattr(etapa, "id", None),
                        )
                # Após garantir listas, tenta reordenar
                try:
                    self.reorder_lists_for_fluxo(fluxo)
                except Exception as exc:
                    logger.warning(
                        "Falha ao reordenar listas após criação do board: {}",
                        exc,
                    )
        except Exception as exc:
            logger.warning(
                "Falha ao pós-processar criação do board (listas/reordenação): {}",
                exc,
            )

        return board

    def ensure_list_for_etapa(self, etapa: Any) -> TrelloList:
        """[TRL-LST-001] Garante list Trello para a EtapaFluxo associada a um board."""
        etapa_id = getattr(etapa, "id", None)
        if not etapa_id:
            raise ValueError("Etapa sem ID")

        with transaction.atomic(using=router.db_for_write(EtapaFluxo)):
            # Lock na etapa para evitar duplicidade de criação de lista
            etapa_locked = EtapaFluxo.objects.select_for_update().get(
                id=etapa_id
            )

            # Re-check se já existe após o lock
            existing: Optional[TrelloList] = getattr(
                etapa_locked, "trello_list", None
            )
            if existing:
                return existing

            board: Optional[TrelloBoard] = getattr(
                etapa_locked.fluxo, "trello_board", None
            )
            if not board:
                # Comentário: Se o board não existir, tenta garanti-lo agora.
                # O lock no ensure_board_for_fluxo evitará duplicidade.
                try:
                    board = self.ensure_board_for_fluxo(etapa_locked.fluxo)
                except Exception as exc:
                    raise RuntimeError(
                        f"Falha ao garantir board para etapa {etapa_locked.id}: {exc}"
                    ) from exc

            # Comentário: add_data_source cria a lista e retorna seu ID.
            # Trello não aceita posições negativas; mapeia valores < 0 para 0 (topo).
            try:
                ordem_raw = getattr(etapa_locked, "ordem", 0)
                ordem_val: float = float(
                    ordem_raw if ordem_raw is not None else 0
                )
            except Exception:
                ordem_val = 0.0
            if ordem_val < 0:
                ordem_val = 0.0
            list_id: str = self.client.add_data_source(
                container_id=board.external_id,
                data_source_id=etapa_locked.nome,
                position=ordem_val,
            )
            # Buscar dados completos da lista para metadados.
            data: Optional[dict[str, Any]] = self.client.get_data_source(
                list_id
            )
            list_data: dict[str, Any] = data if isinstance(data, dict) else {}

            lista: TrelloList = TrelloList.objects.create(
                etapa=etapa_locked,
                board=board,
                external_id=list_id,
                name=list_data.get("name", etapa_locked.nome),
                position=list_data.get("pos", 0.0),
                metadata=list_data,
            )
            return lista

    def reorder_lists_for_fluxo(self, fluxo: Any) -> None:
        """Reordena as listas do board conforme `etapa.ordem`.

        Comentário: percorre etapas do fluxo (ordenadas por `ordem`) e
        aplica a posição correspondente nas listas Trello.
        """
        board: Optional[TrelloBoard] = getattr(fluxo, "trello_board", None)
        if not board:
            return

        # Busca todas as listas vinculadas ao board deste fluxo.
        listas = TrelloList.objects.filter(board=board).select_related("etapa")
        # Ordena pelas etapas do fluxo
        ordered = sorted(
            listas,
            key=lambda tl: int(getattr(tl.etapa, "ordem", 0) or 0),
        )
        for tl in ordered:
            try:
                raw = getattr(tl.etapa, "ordem", 0)
                ordem_val: float = float(raw if raw is not None else 0)
            except Exception:
                ordem_val = 0.0
            # Comentário: Trello não aceita posições negativas; normaliza para 0.
            if ordem_val < 0:
                ordem_val = 0.0
            try:
                self.client.set_data_source_position(tl.external_id, ordem_val)
            except Exception as exc:
                logger.warning(
                    "Falha ao reordenar lista {id}: {}", exc, id=tl.external_id
                )

    def archive_list_for_etapa(self, etapa: Any) -> None:
        """Arquiva a lista Trello vinculada à `EtapaFluxo`.

        Comentário: chamado em eventos de exclusão da etapa para
        fechar a lista no Trello, mantendo histórico sem apagar.
        """
        lista: Optional[TrelloList] = getattr(etapa, "trello_list", None)
        if not lista:
            return
        try:
            self.client.archive_data_source(lista.external_id)
            logger.info(
                "Lista arquivada no Trello: etapa={etapa} list={list}",
                etapa=getattr(etapa, "nome", ""),
                list=lista.external_id,
            )
        except Exception as exc:
            logger.warning(
                "Falha ao arquivar lista do Trello para etapa {etapa}: {}",
                exc,
                etapa=getattr(etapa, "id", ""),
            )

    def archive_board_for_fluxo(self, fluxo: Any) -> None:
        """Arquiva o board Trello vinculado ao `FluxoAtendimento`.

        Comentário: chamado em eventos de exclusão do fluxo para
        fechar o board no Trello e removê-lo da visualização.
        """
        board: Optional[TrelloBoard] = getattr(fluxo, "trello_board", None)
        if not board:
            return
        try:
            self.client.archive_container(board.external_id)
            logger.info(
                "Board arquivado no Trello: fluxo={fluxo} board={board}",
                fluxo=getattr(fluxo, "nome", ""),
                board=board.external_id,
            )
        except Exception as exc:
            logger.warning(
                "Falha ao arquivar board do Trello para fluxo {fluxo}: {}",
                exc,
                fluxo=getattr(fluxo, "id", ""),
            )
