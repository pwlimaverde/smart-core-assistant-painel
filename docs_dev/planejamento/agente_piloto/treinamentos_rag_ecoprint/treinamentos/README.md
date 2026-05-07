# Treinamentos RAG - Ecoprint (Base de Conhecimento por Produto)

Esta pasta contem guias tecnicos segmentados por produto/servico da Ecoprint, pensados para serem recuperados via RAG (consulta sem internet).

Regras de conteudo:
- Foco em conhecimento do produto: definicoes, variacoes, materiais, acabamentos, especificacoes de arquivo e termos tecnicos.
- Evitar instrucoes longas de comportamento do agente (sem "questionarios" e sem fluxos que incentivem insistencia).
- Sempre que existir dependencia de instalacao/visita tecnica/maquina aplicadora, o texto descreve a dependencia como caracteristica do produto/servico.

Observacao:
- Os arquivos em `intents/` podem conter "Comportamento" para orientar roteamento/coleta, mas devem respeitar:
  - pergunta unica para coleta
  - follow-up unico
  - nao pedir telefone do cliente
  - transferir assim que tiver o minimo

## Indice

Cada documento possui no topo os campos `## Tag` e `## Grupo` com o valor exato para copiar/colar no formulario.

- `offset_panfletos_em_grade.md` (Grupo: `offset`, Tag: `panfletos_em_grade`)
- `offset_folders_e_dobras.md` (Grupo: `offset`, Tag: `folders_e_dobras`)
- `offset_cartazes_e_impressos_promocionais.md` (Grupo: `offset`, Tag: `cartazes_e_impressos_promocionais`)
- `offset_catalogos_revistas_livros.md` (Grupo: `offset`, Tag: `catalogos_revistas_livros`)
- `offset_embalagens_cartuchos_e_caixas.md` (Grupo: `offset`, Tag: `embalagens_cartuchos_e_caixas`)
- `offset_bulas_e_encartes.md` (Grupo: `offset`, Tag: `bulas_e_encartes`)
- `digital_cartoes_e_papelaria_rapida.md` (Grupo: `digital`, Tag: `cartoes_e_papelaria_rapida`)
- `digital_convites_crachas_certificados.md` (Grupo: `digital`, Tag: `convites_crachas_certificados`)
- `flexo_rotulos_e_etiquetas_autoadesivas.md` (Grupo: `flexo`, Tag: `rotulos_e_etiquetas_autoadesivas`)
- `visual_adesivos_vinil_recorte_perfurado.md` (Grupo: `visual`, Tag: `adesivos_vinil_recorte_perfurado`)
- `visual_banners_faixas_e_lonas.md` (Grupo: `visual`, Tag: `banners_faixas_e_lonas`)
- `visual_outdoor_blueback_e_midia_externa.md` (Grupo: `visual`, Tag: `outdoor_blueback_e_midia_externa`)
- `visual_fachadas_placas_acm_letras_caixa.md` (Grupo: `visual`, Tag: `fachadas_placas_acm_letras_caixa`)
- `visual_envelopamento_e_plotagem_de_frotas.md` (Grupo: `visual`, Tag: `envelopamento_e_plotagem_de_frotas`)

