"""Dependências compartilhadas: sessão do banco e usuário logado."""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import NaoAutenticado
from app.models import Usuario

DB = Annotated[Session, Depends(get_db)]


def usuario_opcional(request: Request, db: DB) -> Usuario | None:
    usuario_id = request.session.get("usuario_id")
    if usuario_id is None:
        return None
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        request.session.clear()
    return usuario


def usuario_logado(usuario: Annotated[Usuario | None, Depends(usuario_opcional)]) -> Usuario:
    if usuario is None:
        raise NaoAutenticado("Faça login para continuar.")
    return usuario


UsuarioOpcional = Annotated[Usuario | None, Depends(usuario_opcional)]
UsuarioLogado = Annotated[Usuario, Depends(usuario_logado)]
