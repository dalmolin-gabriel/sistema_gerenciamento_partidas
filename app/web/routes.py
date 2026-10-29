"""Telas do sistema (HTML renderizado no servidor)."""

from datetime import timedelta

from fastapi import APIRouter, Request
from pydantic import ValidationError

from app.deps import DB, UsuarioLogado, UsuarioOpcional
from app.errors import ErroDominio
from app.models import StatusPartida, TipoUsuario
from app.schemas import (
    ArenaCriar,
    PartidaCriar,
    PartidaRemarcar,
    Placar,
    TimeCriar,
    UsuarioCriar,
)
from app.services import arenas, classificacao, partidas, relogio, times, usuarios
from app.web.ui import avisar, erros_do_formulario, numero_decimal, redirecionar, render

router = APIRouter(include_in_schema=False)


def _proximo_seguro(destino: str | None) -> str:
    # Evita redirecionamento para outro site (open redirect).
    if destino and destino.startswith("/") and not destino.startswith("//"):
        return destino
    return "/"


def _inicio(form) -> str:
    data, hora = form.get("data", "").strip(), form.get("hora", "").strip()
    return f"{data}T{hora}" if data and hora else ""


# ======================= Autenticação =======================
@router.get("/entrar")
def entrar_form(request: Request, usuario: UsuarioOpcional, proximo: str | None = None):
    if usuario:
        return redirecionar("/")
    return render(request, "auth/entrar.html", proximo=_proximo_seguro(proximo), form={})


@router.post("/entrar")
async def entrar(request: Request, db: DB):
    form = await request.form()
    proximo = _proximo_seguro(form.get("proximo"))
    try:
        usuario = usuarios.autenticar(db, form.get("email", ""), form.get("senha", ""))
    except ErroDominio as e:
        return render(request, "auth/entrar.html", status_code=400, erro=e.mensagem,
                      proximo=proximo, form=form)
    request.session.clear()
    request.session["usuario_id"] = usuario.id
    avisar(request, f"Bem-vindo de volta, {usuario.nome.split()[0]}!")
    return redirecionar(proximo)


@router.get("/cadastro")
def cadastro_form(request: Request, usuario: UsuarioOpcional):
    if usuario:
        return redirecionar("/")
    return render(request, "auth/cadastro.html", form={}, erros={})


@router.post("/cadastro")
async def cadastro(request: Request, db: DB):
    form = await request.form()
    erros = {}
    if form.get("senha") != form.get("confirmar_senha"):
        erros["confirmar_senha"] = "As senhas não coincidem."
    try:
        dados = UsuarioCriar(
            nome=form.get("nome", ""), email=form.get("email", ""),
            senha=form.get("senha", ""), tipo=form.get("tipo") or TipoUsuario.JOGADOR,
        )
    except ValidationError as e:
        erros = erros_do_formulario(e) | erros
    if erros:
        return render(request, "auth/cadastro.html", status_code=400, form=form, erros=erros)
    try:
        usuario = usuarios.cadastrar(db, dados)
    except ErroDominio as e:
        return render(request, "auth/cadastro.html", status_code=400, form=form,
                      erros={"email": e.mensagem})
    request.session.clear()
    request.session["usuario_id"] = usuario.id
    avisar(request, "Conta criada! Comece cadastrando seu primeiro time.")
    return redirecionar("/")


@router.post("/sair")
def sair(request: Request):
    request.session.clear()
    return redirecionar("/entrar")


# ======================= Painel =======================
@router.get("/")
def painel(request: Request, db: DB, usuario: UsuarioOpcional):
    if usuario is None:
        return render(request, "inicio.html",
                      proximas=partidas.listar(db, futuras=True)[:6],
                      tabela=classificacao.tabela(db)[:5])
    return render(
        request, "painel.html", usuario=usuario,
        convites=partidas.pendentes_de_confirmacao(db, usuario),
        proximas=partidas.listar(db, usuario=usuario, futuras=True)[:8],
        aguardando_placar=[
            p for p in partidas.listar(db, usuario=usuario, futuras=False, status=StatusPartida.CONFIRMADA)
            if p.mandante.responsavel_id == usuario.id or p.arena.proprietario_id == usuario.id
        ],
        meus_times=times.listar_do_usuario(db, usuario),
        tabela=classificacao.tabela(db)[:5],
    )


# ======================= Times =======================
@router.get("/times")
def times_lista(request: Request, db: DB, usuario: UsuarioOpcional, busca: str | None = None):
    return render(request, "times/lista.html", usuario=usuario, times=times.listar(db, busca), busca=busca or "")


@router.get("/times/novo")
def time_novo_form(request: Request, usuario: UsuarioLogado):
    return render(request, "times/form.html", usuario=usuario, form={}, erros={}, time=None)


@router.post("/times/novo")
async def time_novo(request: Request, db: DB, usuario: UsuarioLogado):
    form = await request.form()
    try:
        time = times.criar(db, usuario, TimeCriar(nome=form.get("nome", ""), cidade=form.get("cidade")))
    except ValidationError as e:
        return render(request, "times/form.html", status_code=400, usuario=usuario, form=form,
                      erros=erros_do_formulario(e), time=None)
    except ErroDominio as e:
        return render(request, "times/form.html", status_code=400, usuario=usuario, form=form,
                      erros={"nome": e.mensagem}, time=None)
    avisar(request, f"Time {time.nome} criado.")
    return redirecionar(f"/times/{time.id}")


@router.get("/times/{time_id}")
def time_detalhe(time_id: int, request: Request, db: DB, usuario: UsuarioOpcional):
    time = times.obter(db, time_id)
    linha = next((l for l in classificacao.tabela(db) if l.time_id == time.id), None)
    return render(
        request, "times/detalhe.html", usuario=usuario, time=time, linha=linha,
        proximas=partidas.listar(db, time_id=time.id, futuras=True),
        historico=partidas.listar(db, time_id=time.id, futuras=False),
    )


@router.get("/times/{time_id}/editar")
def time_editar_form(time_id: int, request: Request, db: DB, usuario: UsuarioLogado):
    time = times.obter(db, time_id)
    if time.responsavel_id != usuario.id:
        avisar(request, "Só o responsável pelo time pode editá-lo.", "erro")
        return redirecionar(f"/times/{time.id}")
    return render(request, "times/form.html", usuario=usuario, time=time,
                  form={"nome": time.nome, "cidade": time.cidade or ""}, erros={})


@router.post("/times/{time_id}/editar")
async def time_editar(time_id: int, request: Request, db: DB, usuario: UsuarioLogado):
    form = await request.form()
    time = times.obter(db, time_id)
    try:
        times.atualizar(db, usuario, time_id, TimeCriar(nome=form.get("nome", ""), cidade=form.get("cidade")))
    except ValidationError as e:
        return render(request, "times/form.html", status_code=400, usuario=usuario, form=form,
                      erros=erros_do_formulario(e), time=time)
    except ErroDominio as e:
        return render(request, "times/form.html", status_code=400, usuario=usuario, form=form,
                      erros={"nome": e.mensagem}, time=time)
    avisar(request, "Time atualizado.")
    return redirecionar(f"/times/{time_id}")


@router.post("/times/{time_id}/excluir")
def time_excluir(time_id: int, request: Request, db: DB, usuario: UsuarioLogado):
    times.excluir(db, usuario, time_id)
    avisar(request, "Time excluído.")
    return redirecionar("/times")


# ======================= Arenas =======================
def _arena_do_form(form) -> ArenaCriar:
    return ArenaCriar(
        nome=form.get("nome", ""), endereco=form.get("endereco", ""), cidade=form.get("cidade", ""),
        telefone=form.get("telefone"), valor_hora=numero_decimal(form.get("valor_hora", "")),
    )


@router.get("/arenas")
def arenas_lista(request: Request, db: DB, usuario: UsuarioOpcional, cidade: str | None = None):
    return render(request, "arenas/lista.html", usuario=usuario, arenas=arenas.listar(db, cidade), cidade=cidade or "")


@router.get("/arenas/nova")
def arena_nova_form(request: Request, usuario: UsuarioLogado):
    if not usuario.eh_proprietario:
        avisar(request, "Apenas contas de proprietário podem cadastrar arenas.", "erro")
        return redirecionar("/arenas")
    return render(request, "arenas/form.html", usuario=usuario, form={}, erros={}, arena=None)


@router.post("/arenas/nova")
async def arena_nova(request: Request, db: DB, usuario: UsuarioLogado):
    form = await request.form()
    try:
        arena = arenas.criar(db, usuario, _arena_do_form(form))
    except ValidationError as e:
        return render(request, "arenas/form.html", status_code=400, usuario=usuario, form=form,
                      erros=erros_do_formulario(e), arena=None)
    avisar(request, f"Arena {arena.nome} cadastrada.")
    return redirecionar(f"/arenas/{arena.id}")


@router.get("/arenas/{arena_id}")
def arena_detalhe(arena_id: int, request: Request, db: DB, usuario: UsuarioOpcional):
    arena = arenas.obter(db, arena_id)
    agenda = [p for p in partidas.listar(db, arena_id=arena.id, futuras=True)
              if p.status != StatusPartida.CANCELADA]
    return render(request, "arenas/detalhe.html", usuario=usuario, arena=arena, agenda=agenda)


@router.get("/arenas/{arena_id}/editar")
def arena_editar_form(arena_id: int, request: Request, db: DB, usuario: UsuarioLogado):
    arena = arenas.obter(db, arena_id)
    if arena.proprietario_id != usuario.id:
        avisar(request, "Só o proprietário pode editar esta arena.", "erro")
        return redirecionar(f"/arenas/{arena.id}")
    form = {c: getattr(arena, c) or "" for c in ("nome", "endereco", "cidade", "telefone")}
    form["valor_hora"] = f"{arena.valor_hora:.2f}".replace(".", ",")
    return render(request, "arenas/form.html", usuario=usuario, arena=arena, form=form, erros={})


@router.post("/arenas/{arena_id}/editar")
async def arena_editar(arena_id: int, request: Request, db: DB, usuario: UsuarioLogado):
    form = await request.form()
    arena = arenas.obter(db, arena_id)
    try:
        arenas.atualizar(db, usuario, arena_id, _arena_do_form(form))
    except ValidationError as e:
        return render(request, "arenas/form.html", status_code=400, usuario=usuario, form=form,
                      erros=erros_do_formulario(e), arena=arena)
    avisar(request, "Arena atualizada.")
    return redirecionar(f"/arenas/{arena_id}")


@router.post("/arenas/{arena_id}/excluir")
def arena_excluir(arena_id: int, request: Request, db: DB, usuario: UsuarioLogado):
    arenas.excluir(db, usuario, arena_id)
    avisar(request, "Arena excluída.")
    return redirecionar("/arenas")


# ======================= Partidas =======================
ABAS = {"proximas": "Próximas", "historico": "Histórico", "minhas": "Minhas partidas"}


@router.get("/partidas")
def partidas_lista(request: Request, db: DB, usuario: UsuarioOpcional, aba: str = "proximas"):
    if aba == "minhas" and usuario is None:
        return redirecionar("/entrar?proximo=/partidas?aba=minhas")
    if aba == "historico":
        lista = partidas.listar(db, futuras=False)
    elif aba == "minhas":
        lista = partidas.listar(db, usuario=usuario)
    else:
        aba = "proximas"
        lista = [p for p in partidas.listar(db, futuras=True) if p.status != StatusPartida.CANCELADA]
    return render(request, "partidas/lista.html", usuario=usuario, partidas=lista, aba=aba, abas=ABAS)


def _contexto_nova(db, usuario, form, erros):
    sugestao = (relogio.agora() + timedelta(days=1)).replace(hour=19, minute=0, second=0)
    return dict(
        usuario=usuario, form=form, erros=erros,
        meus_times=times.listar_do_usuario(db, usuario),
        todos_times=times.listar(db), arenas=arenas.listar(db),
        sugestao_data=f"{sugestao:%Y-%m-%d}", hoje=f"{relogio.agora():%Y-%m-%d}",
    )


@router.get("/partidas/nova")
def partida_nova_form(request: Request, db: DB, usuario: UsuarioLogado):
    form = {k: v for k, v in request.query_params.items()}
    return render(request, "partidas/nova.html", **_contexto_nova(db, usuario, form, {}))


@router.post("/partidas/nova")
async def partida_nova(request: Request, db: DB, usuario: UsuarioLogado):
    form = await request.form()
    try:
        dados = PartidaCriar(
            mandante_id=form.get("mandante_id") or 0, visitante_id=form.get("visitante_id") or 0,
            arena_id=form.get("arena_id") or 0, inicio=_inicio(form),
            duracao_min=form.get("duracao_min") or 60,
        )
        partida = partidas.criar(db, usuario, dados)
    except ValidationError as e:
        erros = erros_do_formulario(e)
        if "inicio" in erros:
            erros["data"] = erros.pop("inicio")
        return render(request, "partidas/nova.html", status_code=400, **_contexto_nova(db, usuario, form, erros))
    except ErroDominio as e:
        return render(request, "partidas/nova.html", status_code=400,
                      **_contexto_nova(db, usuario, form, {"geral": e.mensagem}))
    if partida.status == StatusPartida.CONFIRMADA:
        avisar(request, "Partida marcada e já confirmada.")
    else:
        avisar(request, f"Partida marcada! Agora o responsável pelo {partida.visitante.nome} precisa confirmar.")
    return redirecionar(f"/partidas/{partida.id}")


@router.get("/partidas/{partida_id}")
def partida_detalhe(partida_id: int, request: Request, db: DB, usuario: UsuarioOpcional):
    p = partidas.obter(db, partida_id)
    uid = usuario.id if usuario else None
    agora = relogio.agora()
    ativa = p.status in (StatusPartida.AGENDADA, StatusPartida.CONFIRMADA)
    pode = dict(
        confirmar=p.status == StatusPartida.AGENDADA and p.visitante.responsavel_id == uid and p.inicio > agora,
        remarcar=ativa and p.mandante.responsavel_id == uid,
        cancelar=ativa and uid in (p.mandante.responsavel_id, p.visitante.responsavel_id, p.arena.proprietario_id),
        placar=p.status == StatusPartida.CONFIRMADA and p.inicio <= agora
        and uid in (p.mandante.responsavel_id, p.arena.proprietario_id),
        excluir=p.status == StatusPartida.CANCELADA and p.mandante.responsavel_id == uid,
    )
    return render(request, "partidas/detalhe.html", usuario=usuario, p=p, pode=pode,
                  erros=request.session.pop("erros_partida", {}))


@router.post("/partidas/{partida_id}/confirmar")
def partida_confirmar(partida_id: int, request: Request, db: DB, usuario: UsuarioLogado):
    partidas.confirmar(db, usuario, partida_id)
    avisar(request, "Partida confirmada. Bom jogo!")
    return redirecionar(f"/partidas/{partida_id}")


@router.post("/partidas/{partida_id}/cancelar")
def partida_cancelar(partida_id: int, request: Request, db: DB, usuario: UsuarioLogado):
    partidas.cancelar(db, usuario, partida_id)
    avisar(request, "Partida cancelada.")
    return redirecionar(f"/partidas/{partida_id}")


@router.post("/partidas/{partida_id}/remarcar")
async def partida_remarcar(partida_id: int, request: Request, db: DB, usuario: UsuarioLogado):
    form = await request.form()
    try:
        dados = PartidaRemarcar(inicio=_inicio(form), duracao_min=form.get("duracao_min") or 60)
    except ValidationError:
        avisar(request, "Informe uma data, horário e duração válidos para remarcar.", "erro")
        return redirecionar(f"/partidas/{partida_id}")
    partidas.remarcar(db, usuario, partida_id, dados)
    avisar(request, "Partida remarcada.")
    return redirecionar(f"/partidas/{partida_id}")


@router.post("/partidas/{partida_id}/placar")
async def partida_placar(partida_id: int, request: Request, db: DB, usuario: UsuarioLogado):
    form = await request.form()
    try:
        placar = Placar(gols_mandante=form.get("gols_mandante", ""), gols_visitante=form.get("gols_visitante", ""))
    except ValidationError:
        avisar(request, "Informe o número de gols de cada time (0 a 99).", "erro")
        return redirecionar(f"/partidas/{partida_id}")
    partidas.registrar_placar(db, usuario, partida_id, placar)
    avisar(request, "Placar registrado. A classificação foi atualizada.")
    return redirecionar(f"/partidas/{partida_id}")


@router.post("/partidas/{partida_id}/excluir")
def partida_excluir(partida_id: int, request: Request, db: DB, usuario: UsuarioLogado):
    partidas.excluir(db, usuario, partida_id)
    avisar(request, "Partida excluída.")
    return redirecionar("/partidas?aba=minhas")


# ======================= Classificação =======================
@router.get("/classificacao")
def classificacao_tela(request: Request, db: DB, usuario: UsuarioOpcional):
    return render(request, "classificacao.html", usuario=usuario, tabela=classificacao.tabela(db))
