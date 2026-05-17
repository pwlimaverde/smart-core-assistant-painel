"""Template tags para cache-busting de assets do Workspace."""

from __future__ import annotations

import os
from typing import Optional

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_versioned(path: str) -> str:
    """Retorna URL do static com `?v=<mtime>` se o arquivo for encontrado.

    Cache-busting baseado no mtime: o browser só reinvalida quando o
    arquivo realmente muda no disco. Robusto a hard refresh manual e a
    múltiplos deploys sem bump de versão.

    Fallback: se o arquivo não for localizado (ex.: em test), retorna a
    URL pura sem query string.
    """
    url = static(path)
    mtime = _resolve_mtime(path)
    if mtime is None:
        return url
    return f"{url}?v={int(mtime)}"


def _resolve_mtime(path: str) -> Optional[float]:
    try:
        located = finders.find(path)
    except Exception:
        located = None
    if not located or not isinstance(located, str):
        return None
    if not os.path.isfile(located):
        return None
    try:
        return os.path.getmtime(located)
    except OSError:
        return None
