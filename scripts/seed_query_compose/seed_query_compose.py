# -*- coding: utf-8 -*-
"""
Script de seed para gerar o arquivo 'dados_query_compose_bd.json' na raiz do projeto
com descrições aprimoradas, exemplos e prompts de comportamento, e popular o banco
(QueryCompose) com esses dados, sem alterar o model.

Uso:
  - Windows/PowerShell (na raiz do repositório):
      python scripts/seed_query_compose.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# --------------------------- Configurações de caminhos ---------------------------
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parent.parent  # .../smart-core-assistant-painel
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_JSON = PROJECT_ROOT / "dados_query_compose_bd.json"

# --------------------------- Base de intents (informada pelo usuário) ---------------------------
INTENT_TYPES_INPUT: Dict[str, Dict[str, str]] = {
    "comunicacao_basica": {
        "saudacao": "cumprimentos e apresentações",
        "despedida": "finalizações de conversa",
        "agradecimento": "expressões de gratidão",
    },
    "busca_informacao": {
        "pergunta": "solicitações de informação",
        "esclarecimento": "pedidos de clarificação",
        "consulta": "verificações de status ou disponibilidade",
    },
    "acoes_comerciais": {
        "solicitacao_servico": "pedidos de serviços ou produtos",
        "cotacao": "solicitações de orçamento ou preço",
        "pedido": "ordens de compra ou contratação",
        "cancelamento": "solicitações de cancelamento",
    },
    "feedback_suporte": {
        "reclamacao": "queixas ou problemas",
        "elogio": "comentários positivos ou satisfação",
        "sugestao": "propostas de melhoria",
        "relato_problema": "descrição de dificuldades técnicas",
    },
    "confirmacoes_validacoes": {
        "confirmacao": "confirmações de ações ou informações",
        "negacao": "recusas ou negativas",
        "aceitacao": "concordâncias ou aprovações",
    },
    "informacoes_fornecidas": {
        "apresentacao": "identificação pessoal ou empresarial",
        "informacao": "dados ou detalhes fornecidos",
        "instrucao": "orientações ou direcionamentos",
    },
    "urgencia_priorizacao": {
        "urgente": "solicitações com alta prioridade",
        "agendamento": "marcação de compromissos ou reuniões",
        "acompanhamento": "verificação de andamento de processos",
    },
    "controle_atendimento": {
        "transferir_humano": "solicitações para falar com atendente",
        "escalar_supervisor": "pedidos para falar com supervisor",
        "pausar_atendimento": "pausar o atendimento temporariamente",
        "finalizar_atendimento": "encerrar o atendimento",
    },
    "autenticacao_seguranca": {
        "login": "tentativas de acesso ao sistema",
        "validar_identidade": "verificações de identidade",
        "reset_senha": "solicitações de redefinição de senha",
        "recuperar_acesso": "recuperação de acesso ao sistema",
    },
    "gerenciamento_dados": {
        "atualizar_dados": "atualização de informações",
        "excluir_dados": "exclusão de informações",
        "consultar_historico": "consulta ao histórico",
        "exportar_dados": "exportação de dados",
    },
}

# --------------------------- Descrições específicas por intent ---------------------------
TAG_DESCRIPTIONS: Dict[str, str] = {
    # comunicação básica
    "saudacao": (
        "Mensagens de abertura de conversa, saudações e cortesia inicial. "
        "Foco em reconhecer o cumprimento e conduzir para o objetivo do "
        "atendimento."
    ),
    "despedida": (
        "Mensagens que encerram a conversa de forma educada, com agradecimento "
        "ou sinalização de finalização do atendimento."
    ),
    "agradecimento": (
        "Expressões de gratidão pelo suporte ou informação recebida. "
        "Foco em reconhecer e manter a disponibilidade para próxima demanda."
    ),
    # busca de informação
    "pergunta": (
        "Solicitações objetivas de informação sobre produtos, serviços, prazos, "
        "condições ou políticas."
    ),
    "esclarecimento": (
        "Pedidos para esclarecer ou detalhar algo já mencionado, removendo "
        "dúvidas específicas."
    ),
    "consulta": (
        "Verificações de status, disponibilidade ou andamento de um pedido, "
        "serviço ou agenda."
    ),
    # ações comerciais
    "solicitacao_servico": (
        "Intenções de contratar, habilitar ou iniciar um serviço/produto, "
        "incluindo pedidos de orientação sobre o processo."
    ),
    "cotacao": (
        "Solicitações de preço, orçamento ou condições comerciais para um "
        "escopo definido."
    ),
    "pedido": (
        "Mensagens que formalizam a compra/contratação, confirmam itens ou "
        "pedem registro do pedido."
    ),
    "cancelamento": (
        "Solicitações para cancelar pedido, assinatura ou serviço, com foco em "
        "encerrar a contratação ou interromper um processo em curso."
    ),
    # feedback e suporte
    "reclamacao": (
        "Relatos de insatisfação, defeitos ou problemas no uso de um produto/"
        "serviço, buscando solução."
    ),
    "elogio": (
        "Feedbacks positivos, reconhecimento de qualidade do atendimento, "
        "produto ou serviço."
    ),
    "sugestao": (
        "Propostas de melhoria em produto, serviço, processo ou comunicação, "
        "com valor para o usuário."
    ),
    "relato_problema": (
        "Descrição de falhas técnicas, erros, indisponibilidade ou mau "
        "funcionamento, geralmente com pedido de correção."
    ),
    # confirmações e validações
    "confirmacao": (
        "Confirmações explícitas de dados, ações, reservas ou decisões para "
        "prosseguir com o fluxo."
    ),
    "negacao": (
        "Recusas ou negativas para prosseguir, aceitar termos ou realizar uma "
        "ação."
    ),
    "aceitacao": (
        "Concordância com proposta, condição ou encaminhamento, permitindo "
        "avançar de etapa."
    ),
    # informações fornecidas
    "apresentacao": (
        "Identificação pessoal/empresarial, cargo, setor ou contexto do "
        "interlocutor."
    ),
    "informacao": (
        "Envio de dados objetivos (ex.: e-mail, CPF, número de pedido, CEP), "
        "normalmente em complemento a uma solicitação."
    ),
    "instrucao": (
        "Direcionamentos claros sobre o que o agente deve fazer a seguir, "
        "passos ou comandos."
    ),
    # urgência e priorização
    "urgente": (
        "Pedidos que declaram alta prioridade ou urgência para resolução "
        "imediata."
    ),
    "agendamento": (
        "Solicitações para marcar, remarcar ou reservar datas/horários para "
        "reuniões, visitas ou serviços."
    ),
    "acompanhamento": (
        "Pedidos de atualização sobre o andamento de um processo, chamado, "
        "pedido ou caso."
    ),
    # controle de atendimento
    "transferir_humano": (
        "Pedidos explícitos para falar com atendente humano, suporte ou "
        "especialista."
    ),
    "escalar_supervisor": (
        "Solicitações de escalonamento para liderança/supervisão, visando "
        "tratativa prioritária."
    ),
    "pausar_atendimento": (
        "Pedir pausa temporária no atendimento, para retomar depois."
    ),
    "finalizar_atendimento": (
        "Encerramento do atendimento a pedido do usuário, com confirmação de "
        "fechamento."
    ),
    # autenticação e segurança
    "login": (
        "Dificuldades de acesso, credenciais ou bloqueio de conta ao tentar "
        "entrar no sistema."
    ),
    "validar_identidade": (
        "Verificação de identidade com dados mínimos e seguros antes de "
        "prosseguir com ações sensíveis."
    ),
    "reset_senha": (
        "Pedidos de redefinição de senha e instruções para recuperar acesso "
        "com segurança."
    ),
    "recuperar_acesso": (
        "Recuperação de acesso quando usuário perdeu controle da conta ou "
        "fator de autenticação."
    ),
    # gerenciamento de dados
    "atualizar_dados": (
        "Atualização de dados cadastrais (contato, endereço, preferências), "
        "com validação."
    ),
    "excluir_dados": (
        "Solicitação de exclusão/remoção de dados pessoais ou conta, com "
        "confirmação de irreversibilidade."
    ),
    "consultar_historico": (
        "Consulta ao histórico de pedidos, acessos, ações ou interações "
        "em período definido."
    ),
    "exportar_dados": (
        "Exportação/baixa de dados em formato específico (CSV, PDF, JSON), "
        "com escopo e período."
    ),
}

# --------------------------- Prompts de comportamento por intent ---------------------------
TAG_BEHAVIORS: Dict[str, str] = {
    # comunicação básica
    "saudacao": (
        "Aja como um assistente cordial e direto. Cumprimente brevemente, "
        "acolha o usuário e pergunte de forma objetiva como pode ajudar. "
        "Mantenha tom profissional e amistoso. Não solicite dados sensíveis."
    ),
    "despedida": (
        "Finalize com cortesia, agradeça a conversa e ofereça apoio futuro. "
        "Se adequado, confirme se há mais algo a tratar. Seja breve."
    ),
    "agradecimento": (
        "Responda ao agradecimento reconhecendo a satisfação do usuário. "
        "Reforce a disponibilidade para novas demandas, sem insistência."
    ),
    # busca de informação
    "pergunta": (
        "Forneça informações claras e verificáveis. Se o pedido for amplo, "
        "solicite até 2 esclarecimentos objetivos. Evite jargões e "
        "respostas longas."
    ),
    "esclarecimento": (
        "Reformule a explicação de maneira simples e direta. Se a dúvida "
        "persistir, faça 1-2 perguntas para entender o ponto exato."
    ),
    "consulta": (
        "Verifique status/disponibilidade. Se faltarem identificadores, peça "
        "apenas o essencial (ex.: número de pedido). Informe próximos passos."
    ),
    # ações comerciais
    "solicitacao_servico": (
        "Entenda o escopo do serviço/produto desejado e oriente os passos. "
        "Peça informações mínimas (tipo, quantidade, prazo) e confirme o "
        "resumo antes de prosseguir."
    ),
    "cotacao": (
        "Colete requisitos (quantidade, prazo, escopo, localidade). Se possível, "
        "apresente faixa de valores/condições e ressalte que é uma estimativa."
    ),
    "pedido": (
        "Confirme itens, quantidades, modalidades de pagamento e entrega. "
        "Apresente um resumo final para confirmação do usuário."
    ),
    "cancelamento": (
        "Confirme o item/serviço a cancelar e, se apropriado, o motivo. "
        "Explique efeitos do cancelamento e informe prazos/processo de "
        "confirmação."
    ),
    # feedback e suporte
    "reclamacao": (
        "Demonstre empatia e registre o ocorrido. Solicite detalhes objetivos "
        "(onde, quando, impacto) e proponha encaminhamento claro."
    ),
    "elogio": (
        "Agradeça o reconhecimento e, se adequado, solicite permissão para "
        "compartilhar internamente. Mantenha tom breve e positivo."
    ),
    "sugestao": (
        "Agradeça a ideia e peça detalhes de valor/benefício. Encaminhe para "
        "avaliação e ofereça retorno quando houver atualização."
    ),
    "relato_problema": (
        "Colete passos para reproduzir, mensagens de erro e evidências. "
        "Proponha próximos passos e, se preciso, encaminhe para suporte."
    ),
    # confirmações e validações
    "confirmacao": (
        "Reconheça a confirmação e avance para a próxima etapa com clareza. "
        "Evite revalidar o que já foi confirmado."
    ),
    "negacao": (
        "Respeite a negativa, interrompa o fluxo e ofereça alternativas "
        "quando fizer sentido."
    ),
    "aceitacao": (
        "Prossiga com o combinado, apresente um breve resumo do que será "
        "feito. Solicite confirmação final apenas se necessário."
    ),
    # informações fornecidas
    "apresentacao": (
        "Acolha a apresentação e direcione com pergunta objetiva sobre o "
        "objetivo da conversa. Mantenha tom profissional."
    ),
    "informacao": (
        "Valide se os dados estão completos e coerentes. Confirme como serão "
        "utilizados e prossiga com o próximo passo."
    ),
    "instrucao": (
        "Siga a instrução de forma seguro e ordenada. Se houver risco ou "
        "ambiguidade, peça confirmação antes de executar."
    ),
    # urgência e priorização
    "urgente": (
        "Priorize o caso. Solicite apenas informações essenciais e informe o "
        "plano de ação imediato e prazos estimados."
    ),
    "agendamento": (
        "Colete datas/horários preferidos, fuso horário e objetivo da reunião. "
        "Proponha opções e confirme a escolha."
    ),
    "acompanhamento": (
        "Busque a atualização mais recente. Se faltar identificador, peça o "
        "mínimo necessário e informe status e próximos passos."
    ),
    # controle de atendimento
    "transferir_humano": (
        "Verifique se a transferência é necessária e encaminhe com contexto. "
        "Explique prazos e canal de contato."
    ),
    "escalar_supervisor": (
        "Reconheça a solicitação de escalonamento, colete o motivo e encaminhe "
        "com prioridade. Informe SLA quando disponível."
    ),
    "pausar_atendimento": (
        "Confirme a pausa e combine quando e como retomar. Registre o "
        "contexto para continuidade futura."
    ),
    "finalizar_atendimento": (
        "Confirme o encerramento, faça um breve resumo das ações e deixe um "
        "canal aberto para retorno."
    ),
    # autenticação e segurança
    "login": (
        "Ajude a recuperar o acesso com passos claros (verificar credenciais, "
        "reset de senha). Evite pedir dados sensíveis em texto aberto."
    ),
    "validar_identidade": (
        "Solicite validações mínimas e seguras (ex.: e-mail e código enviado). "
        "Explique a finalidade e proteja a privacidade."
    ),
    "reset_senha": (
        "Guie o usuário pelo fluxo de redefinição com segurança e instruções "
        "passo a passo."
    ),
    "recuperar_acesso": (
        "Ofereça caminhos para recuperar a conta (verificação por e-mail/telefone). "
        "Priorize segurança e clareza."
    ),
    # gerenciamento de dados
    "atualizar_dados": (
        "Solicite os campos a atualizar e confirme o registro das alterações. "
        "Evite expor dados sensíveis."
    ),
    "excluir_dados": (
        "Explique a irreversibilidade, confirme a identidade de forma mínima e "
        "execute a exclusão com confirmação final."
    ),
    "consultar_historico": (
        "Peça o período/escopo desejado e entregue um resumo claro dos itens "
        "encontrados."
    ),
    "exportar_dados": (
        "Solicite formato, período e escopo. Informe como e quando o arquivo "
        "será disponibilizado."
    ),
}

# --------------------------- Funções de enriquecimento ---------------------------

def _humanize(text: str) -> str:
    return (text or "").replace("_", " ")


def improve_description(group: str, tag: str, base_text: str) -> str:
    # Descrição objetiva para classificação LLM, sem prefixos burocráticos
    return TAG_DESCRIPTIONS.get(tag, (base_text or "").strip())


def examples_for_tag(tag: str) -> List[str]:
    t = tag
    m: Dict[str, List[str]] = {
        # Comunicação básica
        "saudacao": [
            "Olá, tudo bem?",
            "Bom dia!",
            "Boa tarde, pode me ajudar?",
            "Olá!",
            "Oi",
        ],
        "despedida": [
            "Obrigado, até logo!",
            "Tchau, até mais.",
            "Nos falamos depois, boa noite.",
            "Agradeço o atendimento, encerro por aqui.",
            "Até breve!",
        ],
        "agradecimento": [
            "Obrigado pela ajuda!",
            "Valeu, era isso.",
            "Agradeço o retorno.",
            "Muito obrigado!",
            "Obrigada pela atenção.",
        ],
        # Busca de informação
        "pergunta": [
            "Você pode me informar os planos disponíveis?",
            "Qual o prazo de entrega?",
            "Como funciona o serviço?",
            "Quais são as formas de pagamento?",
            "Existe suporte 24h?",
        ],
        "esclarecimento": [
            "Poderia esclarecer o que está incluso no plano?",
            "Não entendi essa parte, pode explicar melhor?",
            "O que significa essa taxa adicional?",
            "Pode detalhar a diferença entre os pacotes?",
            "Como interpreto esse status?",
        ],
        "consulta": [
            "Qual o status do meu pedido?",
            "Meu cadastro foi aprovado?",
            "Há vagas para amanhã?",
            "O produto está disponível em estoque?",
            "Consegue verificar a minha solicitação?",
        ],
        # Ações comerciais
        "solicitacao_servico": [
            "Quero contratar o serviço básico.",
            "Como faço para solicitar a instalação?",
            "Preciso de um orçamento para consultoria.",
            "Quero assinar o plano premium.",
            "Como inicio o teste gratuito?",
        ],
        "cotacao": [
            "Pode me enviar uma cotação?",
            "Qual o preço do plano anual?",
            "Quanto custa esse serviço para 10 usuários?",
            "Tem desconto para pagamento à vista?",
            "Qual o orçamento para esse projeto?",
        ],
        "pedido": [
            "Gostaria de fazer um pedido deste produto.",
            "Quero confirmar a compra.",
            "Como finalizo o pedido?",
            "Pode registrar minha solicitação?",
            "Desejo efetivar a contratação.",
        ],
        "cancelamento": [
            "Quero cancelar meu plano.",
            "Desejo cancelar o pedido #123.",
            "Como faço para desistir da compra?",
            "Pode cancelar a assinatura?",
            "Preciso interromper o serviço.",
        ],
        # Feedback e suporte
        "reclamacao": [
            "Estou com um problema no acesso.",
            "O produto chegou com defeito.",
            "O serviço não está funcionando como esperado.",
            "Tive uma experiência ruim e quero registrar.",
            "Meu pedido está atrasado.",
        ],
        "elogio": [
            "Parabéns pelo atendimento!",
            "Gostei muito do serviço.",
            "Ótima experiência, obrigado!",
            "Funcionou perfeitamente.",
            "Estou satisfeito com o suporte.",
        ],
        "sugestao": [
            "Seria interessante ter um modo escuro.",
            "Sugiro adicionar mais opções de filtros.",
            "Poderiam melhorar a documentação?",
            "Uma ideia: integração com outro sistema.",
            "Teria como simplificar o fluxo de cadastro?",
        ],
        "relato_problema": [
            "Não consigo completar o cadastro.",
            "O site apresenta erro 500.",
            "O app fecha sozinho ao abrir.",
            "O pagamento não é processado.",
            "A página fica carregando sem parar.",
        ],
        # Confirmações e validações
        "confirmacao": [
            "Sim, desejo prosseguir.",
            "Confirmo meus dados.",
            "Está correto, pode continuar.",
            "Pode confirmar a reserva?",
            "Confirmo o cancelamento.",
        ],
        "negacao": [
            "Não, obrigado.",
            "Prefiro não prosseguir.",
            "Não concordo com os termos.",
            "Não desejo contratar agora.",
            "Não é isso que eu queria.",
        ],
        "aceitacao": [
            "Concordo com a proposta.",
            "Aceito os termos.",
            "Está ótimo para mim.",
            "Fechado, podemos avançar.",
            "A proposta atende às minhas necessidades.",
        ],
        # Informações fornecidas
        "apresentacao": [
            "Meu nome é Ana.",
            "Sou da empresa ABC Ltda.",
            "Trabalho na área de TI.",
            "Falo em nome do setor financeiro.",
            "Represento a equipe de suporte.",
        ],
        "informacao": [
            "Meu CEP é 12345-678.",
            "Meu e-mail é user@exemplo.com.",
            "O número do pedido é 4567.",
            "Tenho disponibilidade pela manhã.",
            "Sou cliente desde 2021.",
        ],
        "instrucao": [
            "Siga para a etapa de pagamento.",
            "Acesse o menu de configurações.",
            "Clique em 'Recuperar senha'.",
            "Baixe o relatório em PDF.",
            "Envie os documentos solicitados.",
        ],
        # Urgência e priorização
        "urgente": [
            "Preciso de ajuda com urgência!",
            "É prioridade máxima.",
            "Pode tratar como urgente?",
            "Preciso resolver isso hoje.",
            "Atendimento urgente, por favor.",
        ],
        "agendamento": [
            "Quero agendar uma reunião.",
            "Pode marcar para amanhã às 10h?",
            "Preciso reservar um horário.",
            "Agende uma visita técnica.",
            "Quero remarcar meu compromisso.",
        ],
        "acompanhamento": [
            "Alguma atualização sobre minha solicitação?",
            "Pode me informar o andamento?",
            "Qual o progresso do caso?",
            "Sabe me dizer quando conclui?",
            "Tem novidade sobre o ticket?",
        ],
        # Controle de atendimento
        "transferir_humano": [
            "Quero falar com um atendente humano.",
            "Pode me transferir para um agente?",
            "Preferia falar com uma pessoa.",
            "Pode encaminhar para o suporte humano?",
            "Preciso de um atendente, por favor.",
        ],
        "escalar_supervisor": [
            "Quero falar com um supervisor.",
            "Pode escalar este caso?",
            "Preciso de alguém responsável.",
            "Desejo falar com a gerência.",
            "Por favor, encaminhe ao superior.",
        ],
        "pausar_atendimento": [
            "Podemos pausar o atendimento por enquanto?",
            "Quero continuar depois.",
            "Podemos retomar amanhã?",
            "Pausa rápida, já volto.",
            "Voltamos a falar mais tarde.",
        ],
        "finalizar_atendimento": [
            "Podemos encerrar por aqui.",
            "Obrigado, pode finalizar.",
            "Concluímos, obrigado.",
            "Encerrar atendimento, por favor.",
            "Pode fechar o chamado.",
        ],
        # Autenticação e segurança
        "login": [
            "Não consigo fazer login.",
            "Esqueci minha senha.",
            "Como acesso minha conta?",
            "Minha conta foi bloqueada?",
            "Quero entrar no sistema.",
        ],
        "validar_identidade": [
            "Como valido minha identidade?",
            "Preciso confirmar meus dados.",
            "Pode verificar se sou eu mesmo?",
            "Quais documentos são necessários?",
            "Como funciona a verificação?",
        ],
        "reset_senha": [
            "Quero redefinir minha senha.",
            "Como recupero minha senha?",
            "Não lembro a senha, pode ajudar?",
            "Recebi o código para reset, e agora?",
            "O link de redefinição expirou.",
        ],
        "recuperar_acesso": [
            "Perdi o acesso à minha conta.",
            "Como recuperar o acesso?",
            "Minha conta foi comprometida.",
            "Consegue restaurar meu acesso?",
            "Não tenho mais o dispositivo de 2FA.",
        ],
        # Gerenciamento de dados
        "atualizar_dados": [
            "Quero atualizar meu endereço.",
            "Preciso alterar meu telefone.",
            "Como atualizo meus dados cadastrais?",
            "Desejo corrigir meu e-mail.",
            "Atualize minhas preferências.",
        ],
        "excluir_dados": [
            "Quero excluir meus dados.",
            "Solicito a remoção da minha conta.",
            "Desejo apagar meu histórico.",
            "Como elimino minhas informações?",
            "Apague meus registros, por favor.",
        ],
        "consultar_historico": [
            "Quero consultar meu histórico de pedidos.",
            "Pode enviar meu extrato?",
            "Quais foram minhas últimas ações?",
            "Como vejo meu histórico de acesso?",
            "Preciso do histórico do último mês.",
        ],
        "exportar_dados": [
            "Como exporto meus dados?",
            "Preciso de um CSV com meus registros.",
            "Pode gerar um relatório em PDF?",
            "Exportar dados de pedidos.",
            "Quero baixar meus dados pessoais.",
        ],
    }
    if t in m:
        return m[t]
    base = _humanize(tag)
    return [
        f"Tenho uma solicitação sobre '{base}'.",
        f"Preciso de ajuda com '{base}'.",
        f"Poderia explicar '{base}'?",
        f"Qual é o procedimento para '{base}'?",
        f"Como funciona '{base}'?",
    ]


def build_system_prompt(group: str, tag: str) -> str:
    # Prompt específico por intent, com fallback genérico
    return TAG_BEHAVIORS.get(
        tag,
        (
            "Atue de forma profissional, clara e objetiva. Se necessário, "
            "peça até 2 esclarecimentos curtos antes de responder."
        ),
    )


# --------------------------- Geração do JSON enriquecido ---------------------------

def generate_records() -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for group, tags in INTENT_TYPES_INPUT.items():
        for tag, base_desc in tags.items():
            desc = improve_description(group, tag, base_desc)
            examples = examples_for_tag(tag)
            prompt = build_system_prompt(group, tag)
            records.append(
                {
                    "tag": tag,
                    "grupo": group,
                    "descricao": desc,
                    "exemplo": "\n".join(examples),
                    "comportamento": prompt,
                }
            )
    return records


# --------------------------- Execução principal ---------------------------

def main() -> None:
    records = generate_records()

    # 1) Salvar JSON na raiz do projeto (como lista de objetos prontos para inserção)
    OUTPUT_JSON.write_text(
        json.dumps(records, ensure_ascii=False, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    print(f"Arquivo gerado (lista de registros): {OUTPUT_JSON}")

    # 2) Popular o banco (Django) sem alterar o model
    sys.path.insert(0, str(SRC_DIR))
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "smart_core_assistant_painel.app.ui.core.settings",
    )
    try:
        import django  # type: ignore
        django.setup()
        from smart_core_assistant_painel.app.ui.treinamento.models import (  # type: ignore
            QueryCompose,
        )
    except Exception as e:  # noqa: BLE001
        print(f"Falha ao inicializar Django: {e}")
        return

    total = 0
    for item in records:
        QueryCompose.objects.update_or_create(
            grupo=item["grupo"],
            tag=item["tag"],
            defaults={
                "descricao": item["descricao"],
                "exemplo": item["exemplo"],
                "comportamento": item["comportamento"],
            },
        )
        total += 1
    print(f"Registros QueryCompose afetados: {total}")


if __name__ == "__main__":
    main()