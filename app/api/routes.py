"""API REST (JSON). Documentação interativa em /docs.

A autenticação usa a mesma sessão (cookie) das telas: faça POST em
/api/v1/auth/login e as próximas chamadas já vão autenticadas.
"""

from fastapi import APIRouter, Request, Response, status

from app.deps import DB, UsuarioLogado
from app.models import StatusPartida
from app.schemas import (
    ArenaCriar,
    ArenaSaida,
    LinhaClassificacao,
    Login,
    PartidaCriar,
    PartidaRemarcar,
    PartidaSaida,
    Placar,
    TimeCriar,
    TimeSaida,
    UsuarioCriar,
    UsuarioSaida,
)
from app.services import arenas, classificacao, partidas, times, usuarios

router = APIRouter(prefix="/api/v1")


# ---------- autenticação ----------
@router.post("/auth/cadastro", response_model=UsuarioSaida, status_code=201, tags=["Autenticação"])
def cadastro(dados: UsuarioCriar, request: Request, db: DB):
    usuario = usuarios.cadastrar(db, dados)
    request.session["usuario_id"] = usuario.id
    return usuario


@router.post("/auth/login", response_model=UsuarioSaida, tags=["Autenticação"])
def login(dados: Login, request: Request, db: DB):
    usuario = usuarios.autenticar(db, dados.email, dados.senha)
    request.session["usuario_id"] = usuario.id
    return usuario


@router.post("/auth/logout", status_code=204, tags=["Autenticação"])
def logout(request: Request):
    request.session.clear()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/auth/eu", response_model=UsuarioSaida, tags=["Autenticação"])
def eu(usuario: UsuarioLogado):
    return usuario


# ---------- times ----------
@router.get("/times", response_model=list[TimeSaida], tags=["Times"])
def listar_times(db: DB, busca: str | None = None):
    return times.listar(db, busca)


@router.get("/times/{time_id}", response_model=TimeSaida, tags=["Times"])
def obter_time(time_id: int, db: DB):
    return times.obter(db, time_id)


@router.post("/times", response_model=TimeSaida, status_code=201, tags=["Times"])
def criar_time(dados: TimeCriar, db: DB, usuario: UsuarioLogado):
    return times.criar(db, usuario, dados)


@router.put("/times/{time_id}", response_model=TimeSaida, tags=["Times"])
def atualizar_time(time_id: int, dados: TimeCriar, db: DB, usuario: UsuarioLogado):
    return times.atualizar(db, usuario, time_id, dados)


@router.delete("/times/{time_id}", status_code=204, tags=["Times"])
def excluir_time(time_id: int, db: DB, usuario: UsuarioLogado):
    times.excluir(db, usuario, time_id)
    return Response(status_code=204)


# ---------- arenas ----------
@router.get("/arenas", response_model=list[ArenaSaida], tags=["Arenas"])
def listar_arenas(db: DB, cidade: str | None = None):
    return arenas.listar(db, cidade)


@router.get("/arenas/{arena_id}", response_model=ArenaSaida, tags=["Arenas"])
def obter_arena(arena_id: int, db: DB):
    return arenas.obter(db, arena_id)


@router.post("/arenas", response_model=ArenaSaida, status_code=201, tags=["Arenas"])
def criar_arena(dados: ArenaCriar, db: DB, usuario: UsuarioLogado):
    return arenas.criar(db, usuario, dados)


@router.put("/arenas/{arena_id}", response_model=ArenaSaida, tags=["Arenas"])
def atualizar_arena(arena_id: int, dados: ArenaCriar, db: DB, usuario: UsuarioLogado):
    return arenas.atualizar(db, usuario, arena_id, dados)


@router.delete("/arenas/{arena_id}", status_code=204, tags=["Arenas"])
def excluir_arena(arena_id: int, db: DB, usuario: UsuarioLogado):
    arenas.excluir(db, usuario, arena_id)
    return Response(status_code=204)


# ---------- partidas ----------
@router.get("/partidas", response_model=list[PartidaSaida], tags=["Partidas"])
def listar_partidas(
    db: DB,
    status: StatusPartida | None = None,
    time_id: int | None = None,
    arena_id: int | None = None,
    futuras: bool | None = None,
):
    return partidas.listar(db, status=status, time_id=time_id, arena_id=arena_id, futuras=futuras)


@router.get("/partidas/{partida_id}", response_model=PartidaSaida, tags=["Partidas"])
def obter_partida(partida_id: int, db: DB):
    return partidas.obter(db, partida_id)


@router.post("/partidas", response_model=PartidaSaida, status_code=201, tags=["Partidas"])
def criar_partida(dados: PartidaCriar, db: DB, usuario: UsuarioLogado):
    return partidas.criar(db, usuario, dados)


@router.post("/partidas/{partida_id}/confirmar", response_model=PartidaSaida, tags=["Partidas"])
def confirmar_partida(partida_id: int, db: DB, usuario: UsuarioLogado):
    return partidas.confirmar(db, usuario, partida_id)


@router.post("/partidas/{partida_id}/remarcar", response_model=PartidaSaida, tags=["Partidas"])
def remarcar_partida(partida_id: int, dados: PartidaRemarcar, db: DB, usuario: UsuarioLogado):
    return partidas.remarcar(db, usuario, partida_id, dados)


@router.post("/partidas/{partida_id}/cancelar", response_model=PartidaSaida, tags=["Partidas"])
def cancelar_partida(partida_id: int, db: DB, usuario: UsuarioLogado):
    return partidas.cancelar(db, usuario, partida_id)


@router.post("/partidas/{partida_id}/placar", response_model=PartidaSaida, tags=["Partidas"])
def lancar_placar(partida_id: int, placar: Placar, db: DB, usuario: UsuarioLogado):
    return partidas.registrar_placar(db, usuario, partida_id, placar)


@router.delete("/partidas/{partida_id}", status_code=204, tags=["Partidas"])
def excluir_partida(partida_id: int, db: DB, usuario: UsuarioLogado):
    partidas.excluir(db, usuario, partida_id)
    return Response(status_code=204)


# ---------- classificação ----------
@router.get("/classificacao", response_model=list[LinhaClassificacao], tags=["Classificação"])
def tabela_classificacao(db: DB):
    return classificacao.tabela(db)
