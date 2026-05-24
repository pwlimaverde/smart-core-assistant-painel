"""Datasource para transcrição de áudio via provedores externos."""

import base64
import os
import tempfile
from typing import Any, cast

import httpx
from loguru import logger

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    TranscribeAudioParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import (
    MediaAnalysis,
    TAData,
)
from smart_core_assistant_painel.modules.services import SERVICEHUB


class TranscribeAudioDatasource(TAData):
    """Datasource para transcrever áudio com OpenAI ou Groq.

    Retorna ``MediaAnalysis``: ``analise`` = transcrição completa (contexto do
    bot) e ``resumo`` = resumo curto gerado a partir da transcrição (exibido ao
    atendente).
    """

    _DOWNLOAD_TIMEOUT_SECONDS = 30.0
    _MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024

    def __call__(
        self, parameters: TranscribeAudioParameters
    ) -> MediaAnalysis:
        provider = (
            (SERVICEHUB.TRANSCRIPTION_PROVIDER or "openai").strip().lower()
        )
        model = (SERVICEHUB.TRANSCRIPTION_MODEL or "whisper-1").strip()
        language = (parameters.language or "pt").strip() or "pt"

        if parameters.audio_base64:
            audio_bytes = self._decode_base64_audio(parameters.audio_base64)
        else:
            audio_bytes = self._download_audio(parameters.audio_url)
        if len(audio_bytes) > self._MAX_AUDIO_SIZE_BYTES:
            raise ValueError("Áudio excede o limite de 25MB para transcrição.")

        extension = self._get_file_extension(parameters.mimetype)

        if provider == "openai":
            transcription = self._transcribe_openai(
                audio_bytes=audio_bytes,
                model=model,
                extension=extension,
                language=language,
            )
        elif provider == "groq":
            transcription = self._transcribe_groq(
                audio_bytes=audio_bytes,
                model=model,
                extension=extension,
                language=language,
            )
        else:
            raise ValueError(
                f"Provedor de transcrição não suportado: {provider}"
            )

        resumo = self._summarize_transcription(transcription)
        return MediaAnalysis(analise=transcription, resumo=resumo)

    def _summarize_transcription(self, transcription: str) -> str:
        """Gera um resumo curto da transcrição via LLM de texto.

        Reaproveita a configuração de visão do ``SERVICEHUB`` (provider/modelo)
        para uma chamada de texto leve. Em caso de falha, faz fallback para um
        recorte da própria transcrição — nunca quebra o fluxo de transcrição.
        """
        text = (transcription or "").strip()
        if not text:
            return ""
        try:
            llm = self._build_text_llm()
            prompt = (
                "Resuma em português, em 1 a 3 frases, o conteúdo do áudio "
                "transcrito abaixo. Responda apenas com o resumo.\n\n"
                f"Transcrição:\n{text}"
            )
            response = llm.invoke(prompt)
            content = getattr(response, "content", response)
            resumo = (
                content if isinstance(content, str) else str(content)
            ).strip()
            return resumo or self._fallback_resumo(text)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[TRANSCRIBE] Falha ao gerar resumo da transcrição: {}", exc
            )
            return self._fallback_resumo(text)

    @staticmethod
    def _fallback_resumo(text: str) -> str:
        text = text.strip()
        return text if len(text) <= 200 else text[:197].rstrip() + "..."

    @staticmethod
    def _build_text_llm() -> Any:
        """Constrói um LLM de texto a partir da config de visão do ServiceHub."""
        from pydantic import SecretStr

        provider = (SERVICEHUB.VISION_PROVIDER or "google").strip().lower()
        model = (SERVICEHUB.VISION_MODEL or "gemini-2.5-flash").strip()

        if provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI

            api_key = (SERVICEHUB.GOOGLE_API_KEY or "").strip()
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=SecretStr(api_key) if api_key else None,  # type: ignore[arg-type]
                temperature=0,
            )

        from langchain_openai import ChatOpenAI

        openai_key = (SERVICEHUB.OPENAI_API_KEY or "").strip()
        return ChatOpenAI(
            model=model,
            api_key=SecretStr(openai_key) if openai_key else None,  # type: ignore[arg-type]
            temperature=0,
        )

    def _download_audio(self, url: str) -> bytes:
        if not url:
            raise ValueError("URL do áudio não informada.")

        with httpx.Client(
            timeout=self._DOWNLOAD_TIMEOUT_SECONDS,
            follow_redirects=True,
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            if not response.content:
                raise ValueError("Download de áudio retornou conteúdo vazio.")
            return response.content

    @staticmethod
    def _decode_base64_audio(audio_base64: str) -> bytes:
        value = (audio_base64 or "").strip()
        if not value:
            raise ValueError("Base64 do áudio vazio.")

        # Aceita payload no formato data URI:
        # data:audio/ogg;base64,AAA...
        if "," in value and value.lower().startswith("data:"):
            value = value.split(",", 1)[1]

        try:
            return base64.b64decode(value, validate=False)
        except Exception as exc:
            raise ValueError("Base64 do áudio inválido.") from exc

    def _transcribe_openai(
        self,
        *,
        audio_bytes: bytes,
        model: str,
        extension: str,
        language: str,
    ) -> str:
        api_key = (SERVICEHUB.OPENAI_API_KEY or "").strip()
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY não configurada para transcrição."
            )

        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        temp_file_path = self._write_temp_file(audio_bytes, extension)

        try:
            with open(temp_file_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model=model,
                    file=audio_file,
                    language=language,
                )
            text = self._extract_transcription_text(response)
            if not text:
                raise ValueError("Transcrição OpenAI retornou texto vazio.")
            return text
        finally:
            self._delete_temp_file(temp_file_path)

    def _transcribe_groq(
        self,
        *,
        audio_bytes: bytes,
        model: str,
        extension: str,
        language: str,
    ) -> str:
        api_key = (SERVICEHUB.GROQ_API_KEY or "").strip()
        if not api_key:
            raise ValueError("GROQ_API_KEY não configurada para transcrição.")

        from groq import Groq

        client = Groq(api_key=api_key)
        temp_file_path = self._write_temp_file(audio_bytes, extension)

        try:
            with open(temp_file_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model=model,
                    file=audio_file,
                    language=language,
                )
            text = self._extract_transcription_text(response)
            if not text:
                raise ValueError("Transcrição Groq retornou texto vazio.")
            return text
        finally:
            self._delete_temp_file(temp_file_path)

    @staticmethod
    def _extract_transcription_text(response: Any) -> str:
        if isinstance(response, dict):
            resp_dict = cast(dict[str, Any], response)
            return str(resp_dict.get("text") or "").strip()
        text = getattr(response, "text", "")
        return str(text or "").strip()

    @staticmethod
    def _get_file_extension(mimetype: str) -> str:
        normalized = (mimetype or "").split(";")[0].strip().lower()
        mapping = {
            "audio/mpeg": ".mp3",
            "audio/mp3": ".mp3",
            "audio/mp4": ".mp4",
            "audio/ogg": ".ogg",
            "audio/opus": ".opus",
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
            "audio/webm": ".webm",
            "audio/x-m4a": ".m4a",
            "audio/m4a": ".m4a",
            "audio/aac": ".aac",
        }
        return mapping.get(normalized, ".ogg")

    @staticmethod
    def _write_temp_file(audio_bytes: bytes, extension: str) -> str:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=extension
        ) as tmp:
            tmp.write(audio_bytes)
            return tmp.name

    @staticmethod
    def _delete_temp_file(path: str) -> None:
        try:
            os.unlink(path)
        except OSError:
            pass
