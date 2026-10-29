from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.errors import Conflito, NaoEncontrado, SemPermissao
from app.models import Partida, Time, Usuario
from app.schemas import TimeCriar


def listar(db: Session, busca: str | None = None) -> list[Time]:
    consulta = select(Time).order_by(Time.nome)
    if busca:
        consulta = consulta.where(Time.nome.ilike(f"%{busca.strip()}%"))
    return list(db.scalars(consulta))


def listar_do_usuario(db: Session, usuario: Usuario) -> list[Time]:
    return list(db.scalars(select(Time).where(Time.responsavel_id == usuario.id).order_by(Time.nome)))


def obter(db: Session, time_id: int) -> Time:
    time = db.get(Time, time_id)
    if time is None:
        raise NaoEncontrado("Time não encontrado.")
    return time


def _garantir_nome_livre(db: Session, nome: str, ignorar_id: int | None = None) -> None:
    consulta = select(Time.id).where(func.lower(Time.nome) == nome.lower())
    if ignorar_id:
        consulta = consulta.where(Time.id != ignorar_id)
    if db.scalar(consulta):
        raise Conflito(f"Já existe um time chamado “{nome}”.")


def _garantir_responsavel(time: Time, usuario: Usuario) -> None:
    if time.responsavel_id != usuario.id:
        raise SemPermissao("Só o responsável pelo time pode alterá-lo.")


def criar(db: Session, usuario: Usuario, dados: TimeCriar) -> Time:
    # Sem limite: qualquer usuário pode vincular quantos times quiser.
    _garantir_nome_livre(db, dados.nome)
    time = Time(nome=dados.nome, cidade=dados.cidade, responsavel_id=usuario.id)
    db.add(time)
    db.commit()
    db.refresh(time)
    return time


def atualizar(db: Session, usuario: Usuario, time_id: int, dados: TimeCriar) -> Time:
    time = obter(db, time_id)
    _garantir_responsavel(time, usuario)
    _garantir_nome_livre(db, dados.nome, ignorar_id=time.id)
    time.nome, time.cidade = dados.nome, dados.cidade
    db.commit()
    return time


def excluir(db: Session, usuario: Usuario, time_id: int) -> None:
    time = obter(db, time_id)
    _garantir_responsavel(time, usuario)
    tem_partidas = db.scalar(
        select(func.count(Partida.id)).where(
            or_(Partida.mandante_id == time.id, Partida.visitante_id == time.id)
        )
    )
    if tem_partidas:
        raise Conflito("Este time tem partidas no histórico e não pode ser excluído.")
    db.delete(time)
    db.commit()
