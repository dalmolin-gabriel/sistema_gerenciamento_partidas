from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import Conflito, NaoAutenticado
from app.models import Usuario
from app.schemas import UsuarioCriar
from app.security import gerar_hash, verificar_senha


def cadastrar(db: Session, dados: UsuarioCriar) -> Usuario:
    if db.scalar(select(Usuario).where(Usuario.email == dados.email)):
        raise Conflito("Já existe uma conta com esse e-mail.")
    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=gerar_hash(dados.senha),
        tipo=dados.tipo,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def autenticar(db: Session, email: str, senha: str) -> Usuario:
    usuario = db.scalar(select(Usuario).where(Usuario.email == email.strip().lower()))
    if usuario is None or not verificar_senha(senha, usuario.senha_hash):
        raise NaoAutenticado("E-mail ou senha incorretos.")
    return usuario
