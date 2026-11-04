from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.errors import Conflito, NaoEncontrado, RegraNegocio, SemPermissao
from app.models import Arena, Campo, Partida, Usuario
from app.schemas import ArenaCriar, CampoCriar


def listar(db: Session, cidade: str | None = None) -> list[Arena]:
    consulta = select(Arena).options(selectinload(Arena.campos)).order_by(Arena.cidade, Arena.nome)
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
    arena = Arena(**dados.model_dump(exclude={"quantidade_campos"}), proprietario_id=usuario.id)
    # Toda arena nasce com pelo menos um campo; os nomes podem ser trocados depois.
    arena.campos = [Campo(nome=f"Campo {n}") for n in range(1, dados.quantidade_campos + 1)]
    db.add(arena)
    db.commit()
    db.refresh(arena)
    return arena


def atualizar(db: Session, usuario: Usuario, arena_id: int, dados: ArenaCriar) -> Arena:
    arena = obter(db, arena_id)
    _garantir_dono(arena, usuario)
    for campo, valor in dados.model_dump(exclude={"quantidade_campos"}).items():
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


# ---------- campos ----------
def obter_campo(db: Session, arena_id: int, campo_id: int) -> Campo:
    campo = db.get(Campo, campo_id)
    if campo is None or campo.arena_id != arena_id:
        raise NaoEncontrado("Campo não encontrado nesta arena.")
    return campo


def _garantir_nome_de_campo_livre(db: Session, arena_id: int, nome: str, ignorar_id: int | None = None) -> None:
    consulta = select(Campo.id).where(Campo.arena_id == arena_id, func.lower(Campo.nome) == nome.lower())
    if ignorar_id:
        consulta = consulta.where(Campo.id != ignorar_id)
    if db.scalar(consulta):
        raise Conflito(f"Esta arena já tem um campo chamado “{nome}”.")


def adicionar_campo(db: Session, usuario: Usuario, arena_id: int, dados: CampoCriar) -> Campo:
    arena = obter(db, arena_id)
    _garantir_dono(arena, usuario)
    _garantir_nome_de_campo_livre(db, arena.id, dados.nome)
    campo = Campo(arena_id=arena.id, nome=dados.nome, valor_hora=dados.valor_hora)
    db.add(campo)
    db.commit()
    db.refresh(campo)
    return campo


def atualizar_campo(db: Session, usuario: Usuario, arena_id: int, campo_id: int, dados: CampoCriar) -> Campo:
    arena = obter(db, arena_id)
    _garantir_dono(arena, usuario)
    campo = obter_campo(db, arena.id, campo_id)
    _garantir_nome_de_campo_livre(db, arena.id, dados.nome, ignorar_id=campo.id)
    campo.nome, campo.valor_hora = dados.nome, dados.valor_hora
    db.commit()
    return campo


def excluir_campo(db: Session, usuario: Usuario, arena_id: int, campo_id: int) -> None:
    arena = obter(db, arena_id)
    _garantir_dono(arena, usuario)
    campo = obter_campo(db, arena.id, campo_id)
    if len(arena.campos) <= 1:
        raise RegraNegocio("A arena precisa ter pelo menos um campo.")
    if db.scalar(select(func.count(Partida.id)).where(Partida.campo_id == campo.id)):
        raise Conflito(f"O campo “{campo.nome}” tem partidas no histórico e não pode ser excluído. Renomeie-o se quiser.")
    db.delete(campo)
    db.commit()
    db.refresh(arena)
