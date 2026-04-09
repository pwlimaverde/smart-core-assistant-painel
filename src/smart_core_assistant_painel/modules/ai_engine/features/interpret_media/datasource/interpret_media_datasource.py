"""Datasource para interpretação de mídia via LLM multimodal."""

import base64
from typing import Any, cast

import httpx
from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import SecretStr

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    InterpretMediaParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import (
    IMData,
)
from smart_core_assistant_painel.modules.services import SERVICEHUB


class InterpretMediaDatasource(IMData):
    """Interpreta mídia visual/documental via Gemini Vision API.

    Suporta:
    - imageMessage: interpretação visual da imagem
    - videoMessage: análise completa do vídeo (frames + áudio)
    - documentMessage: extração de conteúdo textual
    """

    _DOWNLOAD_TIMEOUT_SECONDS = 30.0
    _MAX_MEDIA_SIZE_BYTES = 20 * 1024 * 1024  # 20MB (limite inline Gemini)

    # Mapeamento de tipo de mensagem para prompt
    _PROMPTS: dict[str, str] = {
        "imageMessage": (
            "Descreva detalhadamente o conteúdo desta imagem "
            "em português. Foque nos elementos principais, "
            "textos visíveis, objetos, pessoas e contexto geral. "
            "Se houver texto legível na imagem, transcreva-o."
        ),
        "videoMessage": (
            "Descreva detalhadamente o conteúdo deste vídeo "
            "em português. Inclua as principais cenas, ações, "
            "diálogos (se houver áudio), textos visíveis e o "
            "contexto geral. Faça um resumo completo."
        ),
        "documentMessage": (
            "Extraia e organize todo o conteúdo textual deste "
            "documento em português. Mantenha a estrutura "
            "original (títulos, listas, tabelas) quando possível. "
            "Se o documento estiver em outro idioma, traduza "
            "o conteúdo para português."
        ),
    }

    def __call__(
        self, parameters: InterpretMediaParameters
    ) -> str:
        """Executa interpretação da mídia via Gemini.

        Args:
            parameters: Parâmetros com base64/URL da mídia.

        Returns:
            Descrição textual do conteúdo da mídia.

        Raises:
            ValueError: Se a mídia exceder o limite ou
                formato inválido.
        """
        # 1. Obter bytes da mídia
        if parameters.media_base64:
            media_bytes = self._decode_base64(
                parameters.media_base64
            )
        else:
            media_bytes = self._download_media(
                parameters.media_url
            )

        if len(media_bytes) > self._MAX_MEDIA_SIZE_BYTES:
            raise ValueError(
                f"Mídia excede o limite de "
                f"{self._MAX_MEDIA_SIZE_BYTES // (1024 * 1024)}MB."
            )

        # 2. Preparar base64 para envio inline
        media_b64 = base64.b64encode(media_bytes).decode("utf-8")
        mimetype = parameters.mimetype or self._infer_mimetype(
            parameters.media_type
        )

        # 3. Selecionar prompt adequado
        prompt = self._PROMPTS.get(
            parameters.media_type,
            self._PROMPTS["imageMessage"],
        )

        # Adicionar nome do arquivo ao prompt de documentos
        if (
            parameters.media_type == "documentMessage"
            and parameters.file_name
        ):
            prompt = (
                f"{prompt}\n\nNome do arquivo: "
                f"{parameters.file_name}"
            )

        # 4. Instanciar LLM multimodal via ServiceHub
        llm = self._build_vision_llm()

        # 5. Construir mensagem multimodal e invocar
        # Para Gemini via langchain-google-genai v2+, usamos dicionários de conteúdo
        content: list[Any] = [
            {"type": "text", "text": prompt},
        ]

        if parameters.media_type == "imageMessage":
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mimetype};base64,{media_b64}"},
            })
        else:
            # Para vídeo e documentos, o Gemini via langchain suporta o tipo 'media'
            # ou 'image_url' com data URI para alguns casos, mas a forma correta
            # para vídeo é 'media' (baseado em implementações recentes do SDK)
            # Como fallback ou se o provedor for OpenAI, usamos a estrutura deles
            provider = (SERVICEHUB.VISION_PROVIDER or "google").strip().lower()
            if provider == "google":
                content.append({
                    "type": "media",
                    "media_category": "video" if "video" in mimetype else "document",
                    "data": media_b64,
                    "mime_type": mimetype,
                })
            else:
                # Fallback para provedores que usam image_url para tudo (como vision de imagens)
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mimetype};base64,{media_b64}"},
                })

        message = HumanMessage(content=cast(Any, content))

        response: BaseMessage = llm.invoke([message])
        # Lida com o conteúdo que pode ser string ou lista (multimodal)
        raw_content = response.content
        if isinstance(raw_content, list):
            texts = [
                str(c.get("text", ""))
                for c in raw_content
                if isinstance(c, dict)
            ]
            result = " ".join(texts).strip()
        else:
            result = str(raw_content).strip()

        if not result:
            raise ValueError(
                "LLM retornou resposta vazia para a mídia."
            )

        return result

    def _build_vision_llm(self) -> Any:
        """Constrói instância do LLM multimodal via config.

        Returns:
            Instância do ChatGoogleGenerativeAI (ou outro
            provedor configurado).
        """
        provider = (
            SERVICEHUB.VISION_PROVIDER or "google"
        ).strip().lower()
        model = (
            SERVICEHUB.VISION_MODEL or "gemini-2.5-flash"
        ).strip()
        api_key = (SERVICEHUB.GOOGLE_API_KEY or "").strip()

        if provider == "google":
            from langchain_google_genai import (
                ChatGoogleGenerativeAI,
            )

            # Usamos API_KEY do ServiceHub se disponível, senão tenta do ambiente
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=SecretStr(api_key) if api_key else None,  # type: ignore
                temperature=0,
            )

        if provider == "openai":
            from langchain_openai import ChatOpenAI

            openai_key = (SERVICEHUB.OPENAI_API_KEY or "").strip()
            return ChatOpenAI(
                model=model,
                api_key=SecretStr(openai_key) if openai_key else None,  # type: ignore
                temperature=0,
            )

        raise ValueError(
            f"Provedor de visão não suportado: {provider}"
        )

    def _download_media(self, url: str) -> bytes:
        """Faz download da mídia a partir de uma URL.

        Args:
            url: URL do arquivo de mídia.

        Returns:
            Bytes do conteúdo da mídia.
        """
        if not url:
            raise ValueError("URL da mídia não informada.")

        with httpx.Client(
            timeout=self._DOWNLOAD_TIMEOUT_SECONDS,
            follow_redirects=True,
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            if not response.content:
                raise ValueError(
                    "Download de mídia retornou conteúdo vazio."
                )
            return response.content

    @staticmethod
    def _decode_base64(media_base64: str) -> bytes:
        """Decodifica base64 para bytes.

        Args:
            media_base64: String base64 (aceita data URI).

        Returns:
            Bytes decodificados.
        """
        value = (media_base64 or "").strip()
        if not value:
            raise ValueError("Base64 da mídia vazio.")

        # Aceita data URI: data:image/jpeg;base64,AAA...
        if "," in value and value.lower().startswith("data:"):
            value = value.split(",", 1)[1]

        return base64.b64decode(value)

    @staticmethod
    def _infer_mimetype(media_type: str) -> str:
        """Infere o mimetype padrão com base no tipo de msg.

        Args:
            media_type: Tipo da mensagem WhatsApp.

        Returns:
            Mimetype padrão inferido.
        """
        defaults: dict[str, str] = {
            "imageMessage": "image/jpeg",
            "videoMessage": "video/mp4",
            "documentMessage": "application/pdf",
        }
        return defaults.get(media_type, "application/octet-stream")
