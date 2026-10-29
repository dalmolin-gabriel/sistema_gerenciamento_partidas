from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import Conflito, NaoEncontrado, SemPermissao
from app.models import Arena, Partida, Usuario
from app.schemas import ArenaCriar


def listar(db: Session, cidade: str | None = None) -> list[Arena]:
    consulta = select(Arena).order_by(Arena.cidade, Arena.nome)
    if cidade:
        consulta = consulta.where(Arena.cidade.ilike(f"%{cidade.strip()}%"))
    return list(db.scalars(consulta))


def obter(db: Session, arena_id: int) -> Arena:
    arena = db.get(Arena, arena_id)
    if arena is None:
        raise NaoEncontrado("Arena não encontrada.")
    return arena


def _garantir_dono(arena: Arena, usuario: Usuario) -> None:
    if arena.proprietario_id != usuario.id:
        raise SemPermissao("Só o proprietário pode alterar esta arena.")


def criar(db: Session, usuario: Usuario, dados: ArenaCriar) -> Arena:
    if not usuario.eh_proprietario:
        raise SemPermissao("Apenas contas de proprietário podem cadastrar arenas.")
    arena = Arena(**dados.model_dump(), proprietario_id=usuario.id)
    db.add(arena)
    db.commit()
    db.refresh(arena)
    return arena


def atualizar(db: Session, usuario: Usuario, arena_id: int, dados: ArenaCriar) -> Arena:
    arena = obter(db, arena_id)
    _garantir_dono(arena, usuario)
    for campo, valor in dados.model_dump().items():
        setattr(arena, campo, valor)
    db.commit()
    return arena


def excluir(db: Session, usuario: Usuario, arena_id: int) -> None:
    arena = obter(db, arena_id)
    _garantir_dono(arena, usuario)
    if db.scalar(select(func.count(Partida.id)).where(Partida.arena_id == arena.id)):
        raise Conflito("Esta arena tem partidas no histórico e não pode ser excluída.")
    db.delete(arena)
    db.commit()
