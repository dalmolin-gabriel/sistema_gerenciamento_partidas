"""Tabela de classificação a partir das partidas finalizadas.

Vitória = 3 pontos, empate = 1. Desempate: pontos, vitórias, saldo, gols pró, nome.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Partida, StatusPartida, Time
from app.schemas import LinhaClassificacao


def tabela(db: Session) -> list[LinhaClassificacao]:
    stats: dict[int, dict] = {
        t.id: dict(time_id=t.id, time=t.nome, pontos=0, jogos=0, vitorias=0, empates=0,
                   derrotas=0, gols_pro=0, gols_contra=0)
        for t in db.scalars(select(Time))
    }
    partidas = db.scalars(select(Partida).where(Partida.status == StatusPartida.FINALIZADA))
    for p in partidas:
        for time_id, pro, contra in (
            (p.mandante_id, p.gols_mandante, p.gols_visitante),
            (p.visitante_id, p.gols_visitante, p.gols_mandante),
        ):
            s = stats[time_id]
            s["jogos"] += 1
            s["gols_pro"] += pro
            s["gols_contra"] += contra
            if pro > contra:
                s["vitorias"] += 1
                s["pontos"] += 3
            elif pro == contra:
                s["empates"] += 1
                s["pontos"] += 1
            else:
                s["derrotas"] += 1

    jogaram = [s for s in stats.values() if s["jogos"]]
    jogaram.sort(
        key=lambda s: (-s["pontos"], -s["vitorias"], -(s["gols_pro"] - s["gols_contra"]),
                       -s["gols_pro"], s["time"].lower())
    )
    return [
        LinhaClassificacao(posicao=i, saldo=s["gols_pro"] - s["gols_contra"], **s)
        for i, s in enumerate(jogaram, start=1)
    ]
