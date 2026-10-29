"""Hora atual no fuso configurado. Fica isolada para os testes poderem controlá-la."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import get_settings


def agora() -> datetime:
    return datetime.now(ZoneInfo(get_settings().timezone)).replace(tzinfo=None, microsecond=0)
