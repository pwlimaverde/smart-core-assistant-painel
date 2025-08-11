import markdown  # type: ignore[import-untyped]
from typing import Any
from django import template
from django.utils.safestring import SafeString, mark_safe

register = template.Library()


@register.filter
def markdown_format(value: Any) -> SafeString | str:
    """Renderiza texto Markdown como HTML seguro.

    - Aceita qualquer tipo de entrada (como filtros de template do Django).
    - Quando o valor é truthy, renderiza via markdown e marca como seguro.
    - Caso contrário, retorna string vazia.
    """
    if value:
        html: str = markdown.markdown(str(value))
        return mark_safe(html)
    return ""
