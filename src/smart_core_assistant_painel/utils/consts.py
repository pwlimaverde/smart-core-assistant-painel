from pathlib import Path

from langchain_groq import ChatGroq

# constante para o caminho do arquivo de dados

PASTA_DATASETS = Path(__file__).parent.parent.parent / 'app/datasets'
WHATSAPP_API_BASE_URL = 'http://waha:3000'
WHATSAPP_API_SEND_TEXT_URL = 'api/sendText'
WHATSAPP_API_START_TYPING_URL = 'api/startTyping'
WHATSAPP_API_STOP_TYPING_URL = 'api/stopTyping'
LLM_CLASS = ChatGroq
