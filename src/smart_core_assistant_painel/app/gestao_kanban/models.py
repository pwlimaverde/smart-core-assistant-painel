"""Modelos do app Gestão Kanban.

Este app cuida **apenas da manipulação dos cards** — lê o centro
`atendimentos.models` (Atendimento, CampoPersonalizado, Etiqueta, Nota, etc.)
via selectors e o atualiza por signals. Não detém models de informação próprios.
"""
