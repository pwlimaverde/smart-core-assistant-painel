"""Wrapper ChatGoogleGenerativeAI com fallback Free → Paga.

Estratégia: por padrão usa a `google_api_key_free` do ConfigProvider. Em caso de
`ResourceExhausted` (HTTP 429) marca a chave como "burnt" no Redis até o reset
diário e cai para a `google_api_key` (paga). Próximas chamadas no mesmo dia
leem a flag e vão direto para a paga sem nova tentativa na free.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, AsyncIterator, Iterator, List, Optional, Union, cast

from django.core.cache import cache
from google.api_core.exceptions import ResourceExhausted, TooManyRequests
from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatGenerationChunk, ChatResult
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger
from pydantic import ConfigDict, PrivateAttr, SecretStr

from smart_core_assistant_painel.modules.services.config.provider import (
    ConfigProvider,
)

_BURNT_KEY_PREFIX = "gemini:free:burnt"
_BURNT_TTL_SECONDS = 86400


def _burnt_key() -> str:
    return f"{_BURNT_KEY_PREFIX}:{date.today():%Y-%m-%d}"


def _is_free_burnt() -> bool:
    return bool(cache.get(_burnt_key()))


def _mark_burnt() -> None:
    cache.set(_burnt_key(), "1", timeout=_BURNT_TTL_SECONDS)


def _log_burnt(operation: str, model: str = "") -> None:
    """Log destacado do momento exato em que a Free Tier foi esgotada.

    Usa logger.error porque é um evento crítico de auditoria: acontece no
    máximo 1x por dia (na transição) e precisa ficar visível para análise
    posterior de consumo. Inclui timestamp UTC explícito e qual operação
    disparou o estouro.
    """
    now_utc = datetime.now(timezone.utc).isoformat()
    parts = [f"[GEMINI_FALLBACK] Free Tier ESGOTADO @ {now_utc}"]
    parts.append(f"operacao={operation}")
    if model:
        parts.append(f"model={model}")
    parts.append("caindo para chave paga; reset diario automatico.")
    logger.error(" | ".join(parts))


def _is_quota_error(exc: BaseException) -> bool:
    """Detecta esgotamento de quota Gemini Free Tier em variantes de exceção."""
    if isinstance(exc, (ResourceExhausted, TooManyRequests)):
        return True
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if status == 429:
        return True
    msg = str(exc).upper()
    return "RESOURCE_EXHAUSTED" in msg or "QUOTA" in msg or "RATE_LIMIT" in msg


class _FallbackRunnable(Runnable[Any, Any]):
    """Runnable que envolve duas variantes (free e paid) e delega com fallback."""

    def __init__(
        self,
        free: Runnable[Any, Any],
        paid: Runnable[Any, Any],
        model: str = "",
    ) -> None:
        self._free = free
        self._paid = paid
        self._model = model

    def invoke(
        self,
        input: Any,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Any:
        if not _is_free_burnt():
            try:
                return self._free.invoke(input, config, **kwargs)
            except Exception as e:
                if _is_quota_error(e):
                    _mark_burnt()
                    _log_burnt("Runnable.invoke", self._model)
                else:
                    raise
        return self._paid.invoke(input, config, **kwargs)

    async def ainvoke(
        self,
        input: Any,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Any:
        if not _is_free_burnt():
            try:
                return await self._free.ainvoke(input, config, **kwargs)
            except Exception as e:
                if _is_quota_error(e):
                    _mark_burnt()
                    _log_burnt("Runnable.ainvoke", self._model)
                else:
                    raise
        return await self._paid.ainvoke(input, config, **kwargs)


class ChatGoogleGenerativeAIWithFallback(BaseChatModel):
    """ChatGoogleGenerativeAI com fallback automático Free → Paga.

    Usa `google_api_key_free` por padrão. No primeiro 429 do dia, marca burnt
    no Redis (TTL diário) e cai para `google_api_key`. Todas as chamadas
    subsequentes no mesmo dia vão direto para a paga.
    """

    # extra="ignore" absorve api_key/google_api_key vindos de extra_params do
    # LlmParameters — as chaves reais vêm do ConfigProvider.
    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=True)

    model: str
    temperature: float = 0.0

    _free_llm: Optional[ChatGoogleGenerativeAI] = PrivateAttr(default=None)
    _paid_llm: Optional[ChatGoogleGenerativeAI] = PrivateAttr(default=None)

    def model_post_init(self, __context: Any) -> None:
        cfg = ConfigProvider.get()
        paid_key = (cfg.google_api_key or "").strip()
        free_key = (cfg.google_api_key_free or "").strip() or paid_key

        if not paid_key:
            raise ValueError(
                "google_api_key (paga) não configurada — "
                "ChatGoogleGenerativeAIWithFallback exige a chave paga como fallback."
            )

        self._free_llm = ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=SecretStr(free_key),  # type: ignore[call-arg]
            temperature=self.temperature,
        )
        self._paid_llm = ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=SecretStr(paid_key),  # type: ignore[call-arg]
            temperature=self.temperature,
        )

    @property
    def _free(self) -> ChatGoogleGenerativeAI:
        assert self._free_llm is not None
        return self._free_llm

    @property
    def _paid(self) -> ChatGoogleGenerativeAI:
        assert self._paid_llm is not None
        return self._paid_llm

    @property
    def _llm_type(self) -> str:
        return "google_generative_ai_with_fallback"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        if not _is_free_burnt():
            try:
                return self._free._generate(
                    messages, stop, run_manager, **kwargs
                )  # type: ignore[reportPrivateUsage]
            except Exception as e:
                if _is_quota_error(e):
                    _mark_burnt()
                    _log_burnt("_generate", self.model)
                else:
                    raise
        return self._paid._generate(messages, stop, run_manager, **kwargs)  # type: ignore[reportPrivateUsage]

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        if not _is_free_burnt():
            try:
                return await self._free._agenerate(
                    messages, stop, run_manager, **kwargs
                )  # type: ignore[reportPrivateUsage]
            except Exception as e:
                if _is_quota_error(e):
                    _mark_burnt()
                    _log_burnt("_agenerate", self.model)
                else:
                    raise
        return await self._paid._agenerate(
            messages, stop, run_manager, **kwargs
        )  # type: ignore[reportPrivateUsage]

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        if not _is_free_burnt():
            try:
                yield from self._free._stream(
                    messages, stop, run_manager, **kwargs
                )  # type: ignore[reportPrivateUsage]
                return
            except Exception as e:
                if _is_quota_error(e):
                    _mark_burnt()
                    _log_burnt("_stream", self.model)
                else:
                    raise
        yield from self._paid._stream(messages, stop, run_manager, **kwargs)  # type: ignore[reportPrivateUsage]

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        if not _is_free_burnt():
            try:
                async for chunk in self._free._astream(
                    messages, stop, run_manager, **kwargs
                ):  # type: ignore[reportPrivateUsage]
                    yield chunk
                return
            except Exception as e:
                if _is_quota_error(e):
                    _mark_burnt()
                    _log_burnt("_astream", self.model)
                else:
                    raise
        async for chunk in self._paid._astream(
            messages, stop, run_manager, **kwargs
        ):  # type: ignore[reportPrivateUsage]
            yield chunk

    def with_structured_output(  # type: ignore[override]
        self,
        schema: Union[type, dict[str, Any]],
        **kwargs: Any,
    ) -> Runnable[Any, Any]:
        free_r = cast(
            Runnable[Any, Any],
            self._free.with_structured_output(schema, **kwargs),
        )
        paid_r = cast(
            Runnable[Any, Any],
            self._paid.with_structured_output(schema, **kwargs),
        )
        return _FallbackRunnable(free_r, paid_r, self.model)

    def bind_tools(  # type: ignore[override]
        self,
        tools: List[Any],
        **kwargs: Any,
    ) -> Runnable[Any, Any]:
        free_r = cast(
            Runnable[Any, Any], self._free.bind_tools(tools, **kwargs)
        )
        paid_r = cast(
            Runnable[Any, Any], self._paid.bind_tools(tools, **kwargs)
        )
        return _FallbackRunnable(free_r, paid_r, self.model)
