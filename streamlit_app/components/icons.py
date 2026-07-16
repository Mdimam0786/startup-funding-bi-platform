"""
Minimal inline SVG icon set (Lucide-style, stroke-based, single color via
currentColor so icons inherit theme text color automatically). Avoids
pulling in an external icon font/library dependency for a handful of icons.
"""

_SIZE = 18
_STROKE = 1.8


def _svg(paths: str, size: int = _SIZE) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{_STROKE}" '
        f'stroke-linecap="round" stroke-linejoin="round">{paths}</svg>'
    )


ICONS = {
    "home": _svg('<path d="M3 9.5 12 3l9 6.5"/><path d="M5 9.5V21h14V9.5"/><path d="M9 21v-6h6v6"/>'),
    "chart-bar": _svg('<path d="M4 20V10"/><path d="M12 20V4"/><path d="M20 20v-7"/>'),
    "flask": _svg('<path d="M9 3h6"/><path d="M10 3v6l-5.5 9.5A1.5 1.5 0 0 0 5.8 21h12.4a1.5 1.5 0 0 0 1.3-2.5L14 9V3"/>'),
    "database": _svg('<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.66 3.58 3 8 3s8-1.34 8-3V5"/><path d="M4 12c0 1.66 3.58 3 8 3s8-1.34 8-3"/>'),
    "brain": _svg('<path d="M9.5 3a2.5 2.5 0 0 1 2.5 2.5v13a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.02-4.63A2.5 2.5 0 0 1 6.5 8.5 2.5 2.5 0 0 1 9.5 3Z"/><path d="M14.5 3a2.5 2.5 0 0 0-2.5 2.5v13a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.02-4.63A2.5 2.5 0 0 0 17.5 8.5 2.5 2.5 0 0 0 14.5 3Z"/>'),
    "layers": _svg('<path d="m12 2 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5"/><path d="m3 17 9 5 9-5"/>'),
    "compass": _svg('<circle cx="12" cy="12" r="9"/><path d="m16 8-2 6-6 2 2-6 6-2Z"/>'),
    "sitemap": _svg('<rect x="3" y="3" width="6" height="6" rx="1"/><rect x="15" y="3" width="6" height="6" rx="1"/><rect x="9" y="15" width="6" height="6" rx="1"/><path d="M6 9v3a3 3 0 0 0 3 3h0"/><path d="M18 9v3a3 3 0 0 1-3 3h0"/>'),
    "book": _svg('<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>'),
    "info": _svg('<circle cx="12" cy="12" r="9"/><path d="M12 16v-5"/><path d="M12 8h.01"/>'),
    "github": _svg('<path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21"/>'),
    "linkedin": _svg('<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 11v5"/><path d="M8 8v.01"/><path d="M12 16v-5"/><path d="M16 16v-3a2 2 0 0 0-4 0"/>'),
    "download": _svg('<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/>'),
    "sun": _svg('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),
    "moon": _svg('<path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5Z"/>'),
    "search": _svg('<circle cx="11" cy="11" r="7"/><path d="m20 20-3-3"/>'),
    "trending-up": _svg('<path d="M3 17l6-6 4 4 7-8"/><path d="M15 7h5v5"/>'),
    "users": _svg('<circle cx="9" cy="8" r="3.5"/><path d="M2 20c0-3.3 3-6 7-6s7 2.7 7 6"/><circle cx="17" cy="8" r="3"/><path d="M17 12.2c2.6.4 5 2.3 5 5.8"/>'),
    "globe": _svg('<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18Z"/>'),
    "target": _svg('<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>'),
    "zap": _svg('<path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z"/>'),
    "check-circle": _svg('<circle cx="12" cy="12" r="9"/><path d="m8.5 12 2.5 2.5 5-5"/>'),
    "external-link": _svg('<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><path d="M15 3h6v6"/><path d="M10 14 21 3"/>'),
}


def icon(name: str, size: int = _SIZE, color: str = None) -> str:
    """Returns an inline <svg> string. If color is given, wraps in a span forcing that color."""
    svg = ICONS.get(name, ICONS["info"])
    if size != _SIZE:
        svg = svg.replace(f'width="{_SIZE}"', f'width="{size}"').replace(f'height="{_SIZE}"', f'height="{size}"')
    if color:
        return f'<span style="color:{color}; display:inline-flex;">{svg}</span>'
    return svg
