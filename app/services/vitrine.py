"""Vitrine de arenas da página inicial: quem está em destaque e quais horários estão livres.

Um horário (de 1 hora, começando na hora cheia) está livre quando pelo menos um campo da
arena não tem jogo nele. As arenas ainda não guardam horário de funcionamento, então vale
o padrão abaixo para todas.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Arena, Partida
from app.services import relogio
from app.services.partidas import DURACAO_MAXIMA, OCUPAM_HORARIO

HORA_ABERTURA = 8
HORA_FECHAMENTO = 23          # último jogo de 1h começa às 22:00
DURACAO_SUGERIDA = timedelta(hours=1)
MAX_HORARIOS = 6              # quantos horários livres mostrar por arena


@dataclass
class HorarioLivre:
    inicio: datetime
    campo_id: int


@dataclass
class DiaLivre:
    rotulo: str               # "Hoje" ou "Amanhã"
    horarios: list[HorarioLivre] = field(default_factory=list)


@dataclass
class ItemVitrine:
    arena: Arena
    destaque: bool
    preco_minimo: Decimal
    dias: list[DiaLivre]

    @property
    def total_livres(self) -> int:
        return sum(len(d.horarios) for d in self.dias)


def cidades(db: Session) -> list[str]:
    return sorted({c for c in db.scalars(select(Arena.cidade))}, key=str.lower)


def _horarios_do_dia(dia: date, agora: datetime) -> list[datetime]:
    """Inícios possíveis num dia: horas cheias, sempre no futuro e dentro do funcionamento."""
    primeiro = datetime(dia.year, dia.month, dia.day, HORA_ABERTURA)
    proxima_hora = agora.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    inicio = max(primeiro, proxima_hora)
    ultimo = datetime(dia.year, dia.month, dia.day, HORA_FECHAMENTO) - DURACAO_SUGERIDA
    horarios = []
    while inicio <= ultimo:
        horarios.append(inicio)
        inicio += timedelta(hours=1)
    return horarios


def _livres(arena: Arena, ocupacoes: list[Partida], dia: date, agora: datetime) -> list[HorarioLivre]:
    livres = []
    for inicio in _horarios_do_dia(dia, agora):
        fim = inicio + DURACAO_SUGERIDA
        ocupados = {p.campo_id for p in ocupacoes if p.inicio < fim and p.fim > inicio}
        campo = next((c for c in arena.campos if c.id not in ocupados), None)
        if campo:
            livres.append(HorarioLivre(inicio, campo.id))
    return livres


def montar(db: Session, cidade: str | None = None) -> list[ItemVitrine]:
    agora = relogio.agora()
    hoje, amanha = agora.date(), agora.date() + timedelta(days=1)

    consulta = select(Arena).options(selectinload(Arena.campos))
    if cidade:
        consulta = consulta.where(Arena.cidade.ilike(cidade.strip()))
    arenas = list(db.scalars(consulta))
    if not arenas:
        return []

    # Uma consulta só para a agenda de hoje e amanhã de todas as arenas.
    janela_inicio = datetime(hoje.year, hoje.month, hoje.day)
    janela_fim = janela_inicio + timedelta(days=2)
    ocupacoes: dict[int, list[Partida]] = {a.id: [] for a in arenas}
    for p in db.scalars(
        select(Partida).where(
            Partida.arena_id.in_(ocupacoes),
            Partida.status.in_(OCUPAM_HORARIO),
            Partida.inicio < janela_fim,
            Partida.inicio > janela_inicio - DURACAO_MAXIMA,
        )
    ):
        ocupacoes[p.arena_id].append(p)

    itens = []
    for arena in arenas:
        dias, restantes = [], MAX_HORARIOS
        for rotulo, dia in (("Hoje", hoje), ("Amanhã", amanha)):
            livres = _livres(arena, ocupacoes[arena.id], dia, agora)[:restantes]
            if livres:
                dias.append(DiaLivre(rotulo, livres))
                restantes -= len(livres)
            # Mostra amanhã só quando hoje já está quase sem horário.
            if restantes <= MAX_HORARIOS // 2:
                break
        itens.append(ItemVitrine(
            arena=arena,
            destaque=arena.em_destaque(hoje),
            preco_minimo=min(c.preco_hora for c in arena.campos),
            dias=dias,
        ))

    # Destaques primeiro; depois quem tem mais horário livre.
    itens.sort(key=lambda i: (not i.destaque, -i.total_livres, i.arena.nome.lower()))
    return itens
