"""Utilidades de formateo de texto (tiempo, etc.)."""
from __future__ import annotations


def format_time(seconds: float) -> str:
    """Formatea segundos como ``HH:MM:SS`` (u ``MM:SS`` si dura menos de una hora)."""
    total_ms = max(0, int(round(seconds * 1000)))
    hours, remainder_ms = divmod(total_ms, 3_600_000)
    minutes, remainder_ms = divmod(remainder_ms, 60_000)
    secs, _ = divmod(remainder_ms, 1000)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
