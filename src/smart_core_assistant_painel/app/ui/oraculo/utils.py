import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from django.core.cache import cache
from langchain_openai import ChatOpenAI
from loguru import logger

from smart_core_assistant_painel.modules.services.features.service_hub import SERVICEHUB

scheduler = BackgroundScheduler()
scheduler.start()


def send_message_response(phone):
    messages = cache.get(f"wa_buffer_{phone}", [])
    if messages:
        question = "\n".join(messages)
        data = SERVICEHUB.vetor_storage.read(question)
        context = "\n\n".join([doc.page_content for doc in data])

        messages = [
            {
                "role": "system",
                "content": f"Você é um assistente virtual e deve responder com precissão as perguntas sobre uma empresa.\n\n{context}",
            },
            {"role": "user", "content": question},
        ]

        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            streaming=True,
            temperature=0,
        )

        response = llm.invoke(messages).content

        logger.info(f"Resposta gerada: {response}")

    cache.delete(f"wa_buffer_{phone}")
    cache.delete(f"wa_timer_{phone}")


def sched_message_response(phone):
    if not cache.get(f"wa_timer_{phone}"):
        print(1)
        scheduler.add_job(
            send_message_response,
            "date",
            run_date=datetime.datetime.now() + datetime.timedelta(seconds=15),
            kwargs={"phone": phone},
            misfire_grace_time=60,
        )
        cache.set(f"wa_timer_{phone}", True, timeout=60)
