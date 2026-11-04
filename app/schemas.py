"""Esquemas de entrada e saída (validação de dados)."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import TipoUsuario


def _limpar(valor: str) -> str:
    valor = " ".join(valor.split())
    if not valor:
        raise ValueError("não pode ficar em branco")
    return valor


# ---------- Usuários ----------
class UsuarioCriar(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=72)
    tipo: TipoUsuario = TipoUsuario.JOGADOR

    _nome = field_validator("nome")(_limpar)

    @field_validator("email")
    @classmethod
    def _email_minusculo(cls, v: str) -> str:
        return v.lower()

    @field_validator("senha")
    @classmethod
    def _senha_cabe_no_bcrypt(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("senha longa demais (use até 72 caracteres simples)")
        return v


class Login(BaseModel):
    email: EmailStr
    senha: str


class UsuarioSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    email: str
    tipo: str


# ---------- Times ----------
class TimeCriar(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    cidade: str | None = Field(default=None, max_length=100)

    _nome = field_validator("nome")(_limpar)

    @field_validator("cidade")
    @classmethod
    def _cidade(cls, v: str | None) -> str | None:
        v = " ".join(v.split()) if v else None
        return v or None


class TimeSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    cidade: str | None
    responsavel_id: int


# ---------- Campos ----------
class CampoCriar(BaseModel):
    nome: str = Field(min_length=1, max_length=60)
    valor_hora: Decimal | None = Field(default=None, ge=0, le=100000, decimal_places=2)

    _nome = field_validator("nome")(_limpar)


class CampoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    valor_hora: Decimal | None
    preco_hora: Decimal


# ---------- Arenas ----------
class ArenaCriar(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    endereco: str = Field(min_length=3, max_length=200)
    cidade: str = Field(min_length=2, max_length=100)
    telefone: str | None = Field(default=None, max_length=20)
    valor_hora: Decimal = Field(ge=0, le=100000, decimal_places=2)
    # Só usado no cadastro: cria "Campo 1", "Campo 2"... Depois os campos são geridos um a um.
    quantidade_campos: int = Field(default=1, ge=1, le=20)

    _textos = field_validator("nome", "endereco", "cidade")(_limpar)

    @field_validator("telefone")
    @classmethod
    def _telefone(cls, v: str | None) -> str | None:
        if not v or not v.strip():
            return None
        digitos = "".join(c for c in v if c.isdigit())
        if not 10 <= len(digitos) <= 13:
            raise ValueError("telefone deve ter DDD + número (10 ou 11 dígitos)")
        return v.strip()


class ArenaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    endereco: str
    cidade: str
    telefone: str | None
    valor_hora: Decimal
    proprietario_id: int
    campos: list[CampoSaida]


# ---------- Partidas ----------
class PartidaCriar(BaseModel):
    mandante_id: int
    visitante_id: int
    # Informe o campo. A arena sozinha basta quando ela tem um único campo.
    arena_id: int | None = None
    campo_id: int | None = None
    inicio: datetime
    duracao_min: int = Field(default=60, ge=30, le=180)


class PartidaRemarcar(BaseModel):
    inicio: datetime
    duracao_min: int = Field(default=60, ge=30, le=180)
    # Opcional: troca para outro campo da mesma arena.
    campo_id: int | None = None


class Placar(BaseModel):
    gols_mandante: int = Field(ge=0, le=99)
    gols_visitante: int = Field(ge=0, le=99)


class PartidaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    inicio: datetime
    fim: datetime
    duracao_min: int
    status: str
    mandante: TimeSaida
    visitante: TimeSaida
    arena: ArenaSaida
    campo: CampoSaida
    gols_mandante: int | None
    gols_visitante: int | None
    valor_total: Decimal


class LinhaClassificacao(BaseModel):
    posicao: int
    time_id: int
    time: str
    pontos: int
    jogos: int
    vitorias: int
    empates: int
    derrotas: int
    gols_pro: int
    gols_contra: int
    saldo: int
