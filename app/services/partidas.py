"""Regras de negócio das partidas.

Ciclo de vida: agendada → confirmada → finalizada (com placar).
Em qualquer momento antes de finalizar, a partida pode ser cancelada.
"""

from datetime import datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.errors import Conflito, NaoEncontrado, RegraNegocio, SemPermissao
from app.models import Arena, Partida, StatusPartida, Time, Usuario
from app.schemas import PartidaCriar, PartidaRemarcar, Placar
from app.services import arenas as arenas_service
from app.services import relogio
from app.services import times as times_service

DURACAO_MAXIMA = timedelta(minutes=180)
ATIVAS = (StatusPartida.AGENDADA, StatusPartida.CONFIRMADA)
OCUPAM_HORARIO = (StatusPartida.AGENDADA, StatusPartida.CONFIRMADA, StatusPartida.FINALIZADA)


def _consulta_base():
    return select(Partida).options(
        joinedload(Partida.mandante), joinedload(Partida.visitante), joinedload(Partida.arena)
    )


def obter(db: Session, partida_id: int) -> Partida:
    partida = db.scalar(_consulta_base().where(Partida.id == partida_id))
    if partida is None:
        raise NaoEncontrado("Partida não encontrada.")
    return partida


def listar(
    db: Session,
    *,
    status: str | None = None,
    time_id: int | None = None,
    arena_id: int | None = None,
    usuario: Usuario | None = None,
    futuras: bool | None = None,
) -> list[Partida]:
    consulta = _consulta_base()
    if status:
        consulta = consulta.where(Partida.status == status)
    if time_id:
        consulta = consulta.where(or_(Partida.mandante_id == time_id, Partida.visitante_id == time_id))
    if arena_id:
        consulta = consulta.where(Partida.arena_id == arena_id)
    if usuario is not None:
        meus_times = select(Time.id).where(Time.responsavel_id == usuario.id)
        consulta = consulta.where(
            or_(Partida.mandante_id.in_(meus_times), Partida.visitante_id.in_(meus_times))
        )
    agora = relogio.agora()
    if futuras is True:
        consulta = consulta.where(Partida.inicio >= agora).order_by(Partida.inicio)
    elif futuras is False:
        consulta = consulta.where(Partida.inicio < agora).order_by(Partida.inicio.desc())
    else:
        consulta = consulta.order_by(Partida.inicio.desc())
    return list(db.scalars(consulta).unique())


def pendentes_de_confirmacao(db: Session, usuario: Usuario) -> list[Partida]:
    """Convites que o usuário precisa aceitar (ele é responsável pelo visitante)."""
    meus_times = select(Time.id).where(Time.responsavel_id == usuario.id)
    consulta = (
        _consulta_base()
        .where(Partida.status == StatusPartida.AGENDADA, Partida.visitante_id.in_(meus_times))
        .where(Partida.inicio >= relogio.agora())
        .order_by(Partida.inicio)
    )
    return list(db.scalars(consulta).unique())


# ---------- validações ----------
def _validar_horario(inicio: datetime, duracao_min: int) -> None:
    if inicio <= relogio.agora():
        raise RegraNegocio("A partida precisa ser marcada para uma data e horário futuros.")
    if inicio > relogio.agora() + timedelta(days=365):
        raise RegraNegocio("Só é possível agendar com até 1 ano de antecedência.")
    if inicio.minute % 15 or inicio.second:
        raise RegraNegocio("O horário de início deve ser em intervalos de 15 minutos (ex.: 19:00, 19:15).")


def _verificar_conflitos(
    db: Session,
    *,
    arena_id: int,
    times_ids: tuple[int, int],
    inicio: datetime,
    duracao_min: int,
    ignorar_id: int | None = None,
) -> None:
    fim = inicio + timedelta(minutes=duracao_min)
    # Trava a linha da arena até o commit: duas reservas simultâneas não passam juntas.
    db.execute(select(Arena.id).where(Arena.id == arena_id).with_for_update())
    consulta = _consulta_base().where(
        Partida.status.in_(OCUPAM_HORARIO),
        Partida.inicio < fim,
        Partida.inicio > inicio - DURACAO_MAXIMA,
        or_(
            Partida.arena_id == arena_id,
            Partida.mandante_id.in_(times_ids),
            Partida.visitante_id.in_(times_ids),
        ),
    )
    if ignorar_id:
        consulta = consulta.where(Partida.id != ignorar_id)

    for outra in db.scalars(consulta).unique():
        if not (outra.inicio < fim and outra.fim > inicio):
            continue
        faixa = f"{outra.inicio:%d/%m %H:%M}–{outra.fim:%H:%M}"
        if outra.arena_id == arena_id:
            raise Conflito(f"A arena já está ocupada nesse horário ({faixa}).")
        ocupado = outra.mandante if outra.mandante_id in times_ids else outra.visitante
        raise Conflito(f"O time {ocupado.nome} já tem uma partida nesse horário ({faixa}).")


def _exigir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise SemPermissao(mensagem)


# ---------- operações ----------
def criar(db: Session, usuario: Usuario, dados: PartidaCriar) -> Partida:
    if dados.mandante_id == dados.visitante_id:
        raise RegraNegocio("Um time não pode jogar contra ele mesmo.")
    mandante = times_service.obter(db, dados.mandante_id)
    visitante = times_service.obter(db, dados.visitante_id)
    arena = arenas_service.obter(db, dados.arena_id)
    _exigir(mandante.responsavel_id == usuario.id, "Você só pode marcar partidas para os seus times.")
    _validar_horario(dados.inicio, dados.duracao_min)
    _verificar_conflitos(
        db,
        arena_id=arena.id,
        times_ids=(mandante.id, visitante.id),
        inicio=dados.inicio,
        duracao_min=dados.duracao_min,
    )
    # Se o mesmo usuário cuida dos dois times, não há o que confirmar.
    status = (
        StatusPartida.CONFIRMADA
        if visitante.responsavel_id == usuario.id
        else StatusPartida.AGENDADA
    )
    partida = Partida(
        inicio=dados.inicio,
        duracao_min=dados.duracao_min,
        status=status,
        mandante_id=mandante.id,
        visitante_id=visitante.id,
        arena_id=arena.id,
        criado_por_id=usuario.id,
    )
    db.add(partida)
    db.commit()
    return obter(db, partida.id)


def confirmar(db: Session, usuario: Usuario, partida_id: int) -> Partida:
    partida = obter(db, partida_id)
    _exigir(
        partida.visitante.responsavel_id == usuario.id,
        "Só o responsável pelo time visitante pode confirmar a partida.",
    )
    if partida.status != StatusPartida.AGENDADA:
        raise RegraNegocio("Apenas partidas agendadas podem ser confirmadas.")
    if partida.inicio <= relogio.agora():
        raise RegraNegocio("Essa partida já começou e não pode mais ser confirmada.")
    partida.status = StatusPartida.CONFIRMADA
    db.commit()
    return partida


def remarcar(db: Session, usuario: Usuario, partida_id: int, dados: PartidaRemarcar) -> Partida:
    partida = obter(db, partida_id)
    _exigir(
        partida.mandante.responsavel_id == usuario.id,
        "Só o responsável pelo time mandante pode remarcar a partida.",
    )
    if partida.status not in ATIVAS:
        raise RegraNegocio("Só é possível remarcar partidas agendadas ou confirmadas.")
    _validar_horario(dados.inicio, dados.duracao_min)
    _verificar_conflitos(
        db,
        arena_id=partida.arena_id,
        times_ids=(partida.mandante_id, partida.visitante_id),
        inicio=dados.inicio,
        duracao_min=dados.duracao_min,
        ignorar_id=partida.id,
    )
    partida.inicio, partida.duracao_min = dados.inicio, dados.duracao_min
    # Novo horário precisa de novo aceite do adversário.
    if partida.visitante.responsavel_id != usuario.id:
        partida.status = StatusPartida.AGENDADA
    db.commit()
    return partida


def cancelar(db: Session, usuario: Usuario, partida_id: int) -> Partida:
    partida = obter(db, partida_id)
    _exigir(
        usuario.id
        in (partida.mandante.responsavel_id, partida.visitante.responsavel_id, partida.arena.proprietario_id),
        "Só os responsáveis pelos times ou o dono da arena podem cancelar.",
    )
    if partida.status not in ATIVAS:
        raise RegraNegocio("Essa partida não pode mais ser cancelada.")
    partida.status = StatusPartida.CANCELADA
    db.commit()
    return partida


def registrar_placar(db: Session, usuario: Usuario, partida_id: int, placar: Placar) -> Partida:
    partida = obter(db, partida_id)
    _exigir(
        usuario.id in (partida.mandante.responsavel_id, partida.arena.proprietario_id),
        "Só o responsável pelo mandante ou o dono da arena pode lançar o placar.",
    )
    if partida.status != StatusPartida.CONFIRMADA:
        raise RegraNegocio("Só partidas confirmadas podem receber placar.")
    if partida.inicio > relogio.agora():
        raise RegraNegocio("O placar só pode ser lançado depois que a partida começar.")
    partida.gols_mandante = placar.gols_mandante
    partida.gols_visitante = placar.gols_visitante
    partida.status = StatusPartida.FINALIZADA
    db.commit()
    return partida


def excluir(db: Session, usuario: Usuario, partida_id: int) -> None:
    partida = obter(db, partida_id)
    _exigir(partida.mandante.responsavel_id == usuario.id, "Só o mandante pode excluir a partida.")
    if partida.status != StatusPartida.CANCELADA:
        raise RegraNegocio("Cancele a partida antes de excluí-la. Partidas realizadas ficam no histórico.")
    db.delete(partida)
    db.commit()
