from py_return_success_or_error import (
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.features.load_mensage_data.domain.model.message_data import (
    MessageData,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    DataMensageParameters,
)
from typing import Any

from smart_core_assistant_painel.modules.ai_engine.utils.types import LMDUsecase


class LoadMensageDataUseCase(LMDUsecase):
    def __call__(
        self, parameters: DataMensageParameters
    ) -> ReturnSuccessOrError[MessageData]:
        try:
            # Extrair informações básicas com verificações de segurança
            data_section = parameters.data.get("data")

            if not data_section:
                error = parameters.error
                error.message = f"{error.message} - Exception: Campo data não encontrado no payload do webhook"
                return ErrorReturn(error)

            key_section = data_section.get("key")
            if not key_section:
                error = parameters.error
                error.message = f"{error.message} - Exception: Campo key não encontrado no payload do webhook"
                return ErrorReturn(error)

            remote_jid = key_section.get("remoteJid")
            if not remote_jid:
                error = parameters.error
                error.message = f"{error.message} - Exception: Campo remoteJid não encontrado no payload do webhook"
                return ErrorReturn(error)

            # Extrair telefone do remoteJid
            phone = remote_jid.split("@")[0]
            message_id = key_section.get("id")

            # Extrair pushName (nome do perfil do WhatsApp)
            push_name = data_section.get("pushName", "")

            # Extrair fromMe para determinar o tipo de remetente
            from_me = key_section.get("fromMe", False)

            # Obter tipo da mensagem da estrutura real da mensagem
            # Priorizar a primeira chave do message sobre messageType
            message_section = data_section.get("message")
            if not message_section:
                raise ValueError("Campo 'message' não encontrado nos dados do webhook")

            # Usar primeira chave do message como tipo real da mensagem
            message_keys = message_section.keys()
            messageType = list(message_keys)[0] if message_keys else None

            # Se não conseguiu detectar da estrutura, usar messageType como
            # fallback
            if not messageType:
                messageType = data_section.get("messageType")

            # Extrair conteúdo da mensagem com base no tipo
            conteudo = ""
            metadados: dict[str, Any] = {}

            # Adicionar timestamp da mensagem nos metadados se disponível
            if "messageTimestamp" in data_section:
                metadados["messageTimestamp"] = data_section["messageTimestamp"]

            if messageType:
                message_data = message_section.get(messageType, {})

                if messageType == "conversation":
                    # Para tipo "conversation", o texto está diretamente no campo
                    conteudo = (
                        message_data
                        if isinstance(message_data, str)
                        else str(message_data)
                    )
                elif messageType == "extendedTextMessage":
                    # Para "extendedTextMessage", o texto está em 'text'
                    conteudo = message_data.get("text", "")
                elif messageType == "imageMessage":
                    # Para imagens, podemos extrair a caption e URL/dados da imagem
                    conteudo = message_data.get("caption", "Imagem recebida")
                    metadados["mimetype"] = message_data.get("mimetype")
                    metadados["url"] = message_data.get("url")
                    # Outros metadados relevantes para processamento posterior
                    metadados["fileLength"] = message_data.get("fileLength")
                elif messageType == "videoMessage":
                    # Para vídeos, similar às imagens
                    conteudo = message_data.get("caption", "Vídeo recebido")
                    metadados["mimetype"] = message_data.get("mimetype")
                    metadados["url"] = message_data.get("url")
                    metadados["seconds"] = message_data.get("seconds")
                    metadados["fileLength"] = message_data.get("fileLength")
                elif messageType == "audioMessage":
                    # Para áudios
                    conteudo = "Áudio recebido"
                    metadados["mimetype"] = message_data.get("mimetype")
                    metadados["url"] = message_data.get("url")
                    metadados["seconds"] = message_data.get("seconds")
                    metadados["ptt"] = message_data.get(
                        "ptt", False
                    )  # Se é mensagem de voz
                elif messageType == "documentMessage":
                    # Para documentos
                    conteudo = message_data.get("fileName", "Documento recebido")
                    metadados["mimetype"] = message_data.get("mimetype")
                    metadados["url"] = message_data.get("url")
                    metadados["fileLength"] = message_data.get("fileLength")
                elif messageType == "stickerMessage":
                    # Para stickers
                    conteudo = "Sticker recebido"
                    metadados["mimetype"] = message_data.get("mimetype")
                    metadados["url"] = message_data.get("url")
                elif messageType == "locationMessage":
                    # Para localização
                    conteudo = "Localização recebida"
                    metadados["latitude"] = message_data.get("degreesLatitude")
                    metadados["longitude"] = message_data.get("degreesLongitude")
                    metadados["name"] = message_data.get("name")
                    metadados["address"] = message_data.get("address")
                elif messageType == "contactMessage":
                    # Para contatos
                    conteudo = "Contato recebido"
                    metadados["displayName"] = message_data.get("displayName")
                    metadados["vcard"] = message_data.get("vcard")
                elif messageType == "listMessage":
                    # Para mensagens de lista
                    conteudo = message_data.get("title", "Lista recebida")
                    metadados["buttonText"] = message_data.get("buttonText")
                    metadados["description"] = message_data.get("description")
                    metadados["listType"] = message_data.get("listType")
                elif messageType == "buttonsMessage":
                    # Para mensagens com botões
                    conteudo = message_data.get("contentText", "Botões recebidos")
                    metadados["headerType"] = message_data.get("headerType")
                    metadados["footerText"] = message_data.get("footerText")
                elif messageType == "pollMessage":
                    # Para enquetes
                    conteudo = message_data.get("name", "Enquete recebida")
                    metadados["options"] = message_data.get("options")
                    metadados["selectableCount"] = message_data.get("selectableCount")
                elif messageType == "reactMessage":
                    # Para reações
                    conteudo = "Reação recebida"
                    metadados["emoji"] = message_data.get("text")
                    metadados["key"] = message_data.get("key")
                else:
                    # Para outros tipos não tratados especificamente
                    conteudo = f"Mensagem do tipo {messageType} recebida"

            return SuccessReturn(
                MessageData(
                    numero_telefone=phone,
                    from_me=from_me,
                    conteudo=conteudo,
                    message_type=messageType,
                    message_id=message_id,
                    metadados=metadados,
                    nome_perfil_whatsapp=push_name,
                )
            )
        except Exception as e:
            error = parameters.error
            error.message = f"{error.message} - Exception: {str(e)}"
            return ErrorReturn(error)
