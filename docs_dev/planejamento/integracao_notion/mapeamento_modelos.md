# Mapeamento dos Models Django e Relacionamentos (Base para Notion)

Este documento sintetiza os modelos Django e suas propriedades/relacionamentos, servindo de base para a criação/validação dos databases do Notion e seus vínculos.

## Atendimentos.app: Atendimento, Mensagem, Enums

- Modelo `Atendimento`
  - Chave: `id` (AutoField)
  - `contato` (ForeignKey -> `clientes.Contato`, on_delete=CASCADE, related_name="atendimentos")
  - `departamento` (ForeignKey opcional -> `operacional.Departamento`, on_delete=SET_NULL, related_name="atendimentos")
  - `status` (CharField; choices: Fila, Em Atendimento, Aguardando Retorno, Resolvido, Cancelado)
  - `data_inicio` (DateTime, auto_now_add)
  - `data_fim` (DateTime, null/blank)
  - `data_ultima_mensagem` (DateTime, null/blank)
  - `assunto` (CharField, null/blank, até 200)
  - `prioridade` (CharField; choices: baixa, normal, alta, urgente; default: normal)
  - `atendente_humano` (ForeignKey opcional -> `operacional.AtendenteHumano`, on_delete=SET_NULL, related_name="atendimentos")
  - `contexto_conversa` (JSONField dict, default={})
  - `historico_status` (JSONField list[dict], default=[])
  - `tags` (JSONField list[str], default=[])
  - `avaliacao` (IntegerField 1..5, null/blank)
  - `feedback` (TextField, null/blank)
  - Meta: `db_table=oraculo_atendimento`, `ordering=[-data_inicio]`, índices por status/departamento/atendente
  - Métodos relevantes: `finalizar_atendimento`, `change_status`, `adicionar_historico_status`, `assign_to_agent`, `unassign_agent`, `transfer_to_department`, `touch_last_message`, `atualizar_contexto`, `get_contexto`, `transferir_para_humano`, `carregar_historico_mensagens`

- Modelo `Mensagem`
  - Chave: `id` (AutoField)
  - `atendimento` (ForeignKey -> `Atendimento`, on_delete=CASCADE, related_name="mensagens")
  - `tipo` (CharField; choices `TipoMensagem`; default TEXTO_FORMATADO)
  - `conteudo` (TextField)
  - `remetente` (CharField; choices: contato, bot, atendente_humano; default contato)
  - `timestamp` (DateTime, auto_now_add)
  - `message_id_whatsapp` (CharField, null/blank)
  - `metadados` (JSONField dict, default={})
  - `respondida` (Boolean, default=False)
  - `resposta_bot` (TextField, null/blank)
  - `intent_detectado` (JSONField list[dict], default=[])
  - `entidades_extraidas` (JSONField list[dict], default=[])
  - `confianca_resposta` (FloatField, null/blank)
  - Meta: `db_table=oraculo_mensagem`, `ordering=[timestamp]`
  - Métodos: `registrar_resposta_bot`

- Enums
  - `StatusAtendimento`: fila, em_atendimento, aguardando_retorno, resolvido, cancelado
  - `TipoMensagem`: extendedTextMessage, imageMessage, videoMessage, audioMessage, documentMessage, stickerMessage, locationMessage, contactMessage, listMessage, buttonsMessage, pollMessage, reactMessage
  - `TipoRemetente`: contato, bot, atendente_humano

## Clientes.app: Contato, Cliente

- Modelo `Contato`
  - Chave: `id` (AutoField)
  - `telefone` (CharField único; validação; normalizado para iniciar com 55)
  - `nome_contato` (CharField, null/blank)
  - `email` (EmailField, null/blank)
  - `nome_perfil_whatsapp` (CharField, null/blank)
  - `data_cadastro` (DateTime, auto_now_add)
  - `ultima_interacao` (DateTime, auto_now)
  - `ativo` (Boolean, default=True)
  - `metadados` (JSONField dict, default={})
  - Meta: `db_table=oraculo_contato`, `ordering=[-ultima_interacao]`

- Modelo `Cliente`
  - Chave: `id` (AutoField)
  - `nome_fantasia` (CharField, obrigatório)
  - `razao_social` (CharField, null/blank)
  - `tipo` (CharField; choices: fisica|juridica)
  - `cnpj` (CharField, null/blank; validação; formatado ao salvar)
  - `cpf` (CharField, null/blank; validação; formatado ao salvar)
  - `telefone` (CharField, null/blank; validação; formatado ao salvar)
  - `site` (URLField, null/blank)
  - `ramo_atividade` (CharField, null/blank)
  - `observacoes` (TextField, null/blank)
  - Endereço: `cep` (Char, validação, formatado), `logradouro` (Char), `numero` (Char), `complemento` (Char), `bairro` (Char), `cidade` (Char), `uf` (Char, upper), `pais` (Char, default=Brasil)
  - `contatos` (ManyToMany -> `Contato`, related_name="clientes")
  - `data_cadastro` (DateTime, auto_now_add)
  - `ultima_atualizacao` (DateTime, auto_now)
  - `ativo` (Boolean, default=True)
  - `metadados` (JSONField dict, default={})
  - Meta: `db_table=oraculo_cliente`, `ordering=[nome_fantasia]`
  - Métodos: `get_endereco_completo`, `adicionar_contato`, `remover_contato`, `atualizar_metadados`, `get_metadados`

## Operacional.app: Departamento, WhatsAppInstance, AtendenteHumano

- Modelo `Departamento`
  - Chave: `id` (AutoField)
  - `nome` (CharField único)
  - `descricao` (TextField, null/blank)
  - `ativo` (Boolean, default=True)
  - `configuracoes` (JSONField dict, default={})
  - `data_criacao` (DateTime, auto_now_add)
  - `metadados` (JSONField dict, default={})
  - Meta: `db_table=oraculo_departamento`, `ordering=[nome]`
  - Índices: [ativo,nome]
  - Método: `selecionar_proximo_atendente` (round-robin com capacidade)

- Modelo `WhatsAppInstance`
  - Chave: `id` (AutoField)
  - `departamento` (ForeignKey -> `Departamento`, on_delete=CASCADE, related_name="whatsapp_instances")
  - `telefone_instancia` (CharField único; validação; normalizado)
  - `api_key` (CharField único; validação)
  - `instance_id` (CharField, null/blank)
  - `ativo` (Boolean, default=True)
  - `data_criacao` (DateTime, auto_now_add)
  - `ultima_validacao` (DateTime, null/blank)
  - `metadados` (JSONField dict, default={})
  - Meta: `db_table=oraculo_whatsapp_instance`, `ordering=[departamento, telefone_instancia]`
  - Índices: api_key, telefone_instancia, [ativo, departamento]
  - Classe: `validar_api_key(data)` retorna instância ativa por `apikey` e `instance`

- Modelo `AtendenteHumano`
  - Chave: `id` (AutoField)
  - `telefone` (CharField único, null/blank; validação; normalizado +55)
  - `nome` (CharField)
  - `cargo` (CharField)
  - `departamento` (ForeignKey opcional -> `Departamento`, on_delete=SET_NULL, related_name="atendentes")
  - `whatsapp_instance` (OneToOne opcional -> `WhatsAppInstance`, on_delete=SET_NULL, related_name="atendente_ativo")
  - `email` (EmailField, null/blank)
  - `usuario_sistema` (CharField, null/blank)
  - `ativo` (Boolean, default=True)
  - `disponivel` (Boolean, default=True)
  - `max_atendimentos_simultaneos` (PositiveIntegerField, default=5)
  - `data_ultima_atribuicao` (DateTime, null/blank)
  - `horario_trabalho` (JSONField dict, default={})
  - `especialidades` (JSONField list[str], default=[])
  - `metadados` (JSONField dict, default={})
  - `data_cadastro` (DateTime, auto_now_add)
  - `ultima_atividade` (DateTime, auto_now)
  - Meta: `db_table=oraculo_atendentehumano`, `ordering=[nome]`
  - Índices: [departamento,disponivel], [disponivel,max_atendimentos_simultaneos], [data_ultima_atribuicao]
  - Métodos: `get_atendimentos_ativos`, `is_available`, `current_load`

## Relacionamentos Principais (para Notion)

- Atendimento → Contato (obrigatório, N:1)
- Atendimento → Departamento (opcional, N:1)
- Atendimento → AtendenteHumano (opcional, N:1)
- Mensagem → Atendimento (obrigatório, N:1)
- Cliente ↔ Contato (M:N)
- AtendenteHumano → Departamento (opcional, N:1)
- WhatsAppInstance → Departamento (obrigatório, N:1)

## Considerações de Mapeamento para Notion

- Databases necessários: Contatos, Clientes, Departamentos, Atendentes, Atendimentos, Mensagens
- Relações:
  - Atendimentos.Contato → Contatos
  - Atendimentos.Departamento → Departamentos
  - Atendimentos.Agente → Atendentes
  - Mensagens.Atendimento → Atendimentos
  - Clientes.Contatos → Contatos (relação M:N)
- Propriedades sugeridas em Notion devem refletir os campos essenciais e status/select/relations conforme enums e chaves principais.