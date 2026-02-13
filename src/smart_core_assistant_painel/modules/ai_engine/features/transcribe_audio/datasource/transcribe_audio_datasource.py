"""Datasource para transcrição de áudio via provedores externos."""

import base64
import os
import tempfile
from typing import Any

import httpx

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    TranscribeAudioParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import TAData
from smart_core_assistant_painel.modules.services import SERVICEHUB


class TranscribeAudioDatasource(TAData):
    """Datasource para transcrever áudio com OpenAI ou Groq."""

    _DOWNLOAD_TIMEOUT_SECONDS = 30.0
    _MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024

    def __call__(self, parameters: TranscribeAudioParameters) -> str:
        provider = (SERVICEHUB.TRANSCRIPTION_PROVIDER or "openai").strip().lower()
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
            return self._transcribe_openai(
                audio_bytes=audio_bytes,
                model=model,
                extension=extension,
                language=language,
            )
        if provider == "groq":
            return self._transcribe_groq(
                audio_bytes=audio_bytes,
                model=model,
                extension=extension,
                language=language,
            )

        raise ValueError(f"Provedor de transcrição não suportado: {provider}")

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
            raise ValueError("OPENAI_API_KEY não configurada para transcrição.")

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
            return str(response.get("text") or "").strip()
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
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
            tmp.write(audio_bytes)
            return tmp.name

    @staticmethod
    def _delete_temp_file(path: str) -> None:
        try:
            os.unlink(path)
        except OSError:
            pass

