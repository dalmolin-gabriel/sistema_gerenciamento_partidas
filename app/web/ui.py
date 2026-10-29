"""Utilidades das telas: templates, filtros em pt-BR, avisos e tradução de erros."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.models import StatusPartida
from app.services import relogio

templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

DIAS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

STATUS_ROTULO = {
    StatusPartida.AGENDADA: "Aguardando confirmação",
    StatusPartida.CONFIRMADA: "Confirmada",
    StatusPartida.FINALIZADA: "Finalizada",
    StatusPartida.CANCELADA: "Cancelada",
}


def dinheiro(valor: Decimal | float | None) -> str:
    if valor is None:
        return "—"
    texto = f"{Decimal(valor):,.2f}"
    return "R$ " + texto.replace(",", "_").replace(".", ",").replace("_", ".")


def data_curta(d: datetime | date) -> str:
    return f"{DIAS[d.weekday()]}, {d.day:02d} {MESES[d.month - 1]}"


def data_longa(d: datetime | date) -> str:
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


templates.env.filters["dinheiro"] = dinheiro
templates.env.filters["data_curta"] = data_curta
templates.env.filters["data_longa"] = data_longa
templates.env.filters["hora"] = lambda d: f"{d:%H:%M}"
templates.env.filters["status_rotulo"] = lambda s: STATUS_ROTULO.get(s, s)
templates.env.globals["agora"] = relogio.agora


def avisar(request: Request, mensagem: str, tipo: str = "ok") -> None:
    request.session.setdefault("avisos", []).append([tipo, mensagem])


def redirecionar(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def render(request: Request, template: str, status_code: int = 200, **contexto):
    avisos = request.session.pop("avisos", [])
    return templates.TemplateResponse(
        request,
        template,
        {"avisos": avisos, "usuario": contexto.pop("usuario", None), **contexto},
        status_code=status_code,
    )


_MENSAGENS = {
    "missing": "Campo obrigatório.",
    "string_too_short": "Deve ter pelo menos {min_length} caracteres.",
    "string_too_long": "Deve ter no máximo {max_length} caracteres.",
    "greater_than_equal": "Deve ser maior ou igual a {ge}.",
    "less_than_equal": "Deve ser menor ou igual a {le}.",
    "int_parsing": "Informe um número inteiro.",
    "int_type": "Informe um número inteiro.",
    "decimal_parsing": "Informe um valor numérico (ex.: 150,00).",
    "decimal_max_places": "Use no máximo 2 casas decimais.",
    "datetime_parsing": "Informe data e horário válidos.",
    "datetime_from_date_parsing": "Informe data e horário válidos.",
    "enum": "Opção inválida.",
}


def erros_do_formulario(exc: ValidationError) -> dict[str, str]:
    """Converte erros do Pydantic em mensagens em português, por campo."""
    erros: dict[str, str] = {}
    for erro in exc.errors():
        campo = str(erro["loc"][0]) if erro["loc"] else "geral"
        tipo = erro["type"]
        if tipo == "value_error":
            msg = str(erro.get("ctx", {}).get("error", erro["msg"]))
            if "email" in campo:
                msg = "Informe um e-mail válido."
        else:
            modelo = _MENSAGENS.get(tipo, "Valor inválido.")
            msg = modelo.format(**erro.get("ctx", {}))
        erros.setdefault(campo, msg[0].upper() + msg[1:])
    return erros


def numero_decimal(texto: str) -> str:
    """Aceita '1.234,50', '1234,50' ou '1234.50'."""
    texto = texto.strip().replace("R$", "").strip()
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    return texto
