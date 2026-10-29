"""Modelo de dados do sistema."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TipoUsuario(StrEnum):
    JOGADOR = "jogador"
    PROPRIETARIO = "proprietario"


class StatusPartida(StrEnum):
    AGENDADA = "agendada"
    CONFIRMADA = "confirmada"
    FINALIZADA = "finalizada"
    CANCELADA = "cancelada"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    tipo: Mapped[str] = mapped_column(String(20), default=TipoUsuario.JOGADOR)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Qualquer usuário pode ser responsável por quantos times quiser.
    times: Mapped[list["Time"]] = relationship(back_populates="responsavel")
    arenas: Mapped[list["Arena"]] = relationship(back_populates="proprietario")

    @property
    def eh_proprietario(self) -> bool:
        return self.tipo == TipoUsuario.PROPRIETARIO


class Time(Base):
    __tablename__ = "times"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True)
    cidade: Mapped[str | None] = mapped_column(String(100))
    responsavel_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    responsavel: Mapped[Usuario] = relationship(back_populates="times")


class Arena(Base):
    __tablename__ = "arenas"
    __table_args__ = (CheckConstraint("valor_hora >= 0", name="ck_arena_valor_hora"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    endereco: Mapped[str] = mapped_column(String(200))
    cidade: Mapped[str] = mapped_column(String(100))
    telefone: Mapped[str | None] = mapped_column(String(20))
    valor_hora: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    proprietario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    proprietario: Mapped[Usuario] = relationship(back_populates="arenas")


class Partida(Base):
    __tablename__ = "partidas"
    __table_args__ = (
        CheckConstraint("mandante_id <> visitante_id", name="ck_partida_times_diferentes"),
        CheckConstraint("duracao_min BETWEEN 30 AND 180", name="ck_partida_duracao"),
        CheckConstraint(
            "(gols_mandante IS NULL OR gols_mandante >= 0) AND "
            "(gols_visitante IS NULL OR gols_visitante >= 0)",
            name="ck_partida_placar",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    inicio: Mapped[datetime] = mapped_column(DateTime, index=True)
    duracao_min: Mapped[int] = mapped_column(Integer, default=60)
    status: Mapped[str] = mapped_column(String(20), default=StatusPartida.AGENDADA, index=True)
    mandante_id: Mapped[int] = mapped_column(ForeignKey("times.id"), index=True)
    visitante_id: Mapped[int] = mapped_column(ForeignKey("times.id"), index=True)
    arena_id: Mapped[int] = mapped_column(ForeignKey("arenas.id"), index=True)
    gols_mandante: Mapped[int | None] = mapped_column(Integer)
    gols_visitante: Mapped[int | None] = mapped_column(Integer)
    criado_por_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    mandante: Mapped[Time] = relationship(foreign_keys=[mandante_id])
    visitante: Mapped[Time] = relationship(foreign_keys=[visitante_id])
    arena: Mapped[Arena] = relationship()
    criado_por: Mapped[Usuario] = relationship()

    @property
    def fim(self) -> datetime:
        from datetime import timedelta

        return self.inicio + timedelta(minutes=self.duracao_min)

    @property
    def valor_total(self) -> Decimal:
        return (self.arena.valor_hora * Decimal(self.duracao_min) / Decimal(60)).quantize(
            Decimal("0.01")
        )

    @property
    def placar(self) -> str | None:
        if self.gols_mandante is None or self.gols_visitante is None:
            return None
        return f"{self.gols_mandante} x {self.gols_visitante}"
