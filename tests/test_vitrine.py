"""Vitrine de arenas no quadro grande da página inicial."""

from datetime import date, datetime
from urllib.parse import unquote

from app.models import Arena
from app.services import vitrine
from tests.conftest import AGORA

# AGORA = quarta 28/10/2026 12:00 → hoje os horários livres começam às 13:00.


def _marcar(cliente, cen, campo_id, inicio, mandante=None, visitante=None):
    r = cliente.post("/api/v1/partidas", json={
        "mandante_id": mandante or cen["real"]["id"], "visitante_id": visitante or cen["unidos"]["id"],
        "campo_id": campo_id, "inicio": inicio, "duracao_min": 60,
    })
    assert r.status_code == 201, r.text


def _item(db, nome):
    return next(i for i in vitrine.montar(db) if i.arena.nome == nome)


def test_horarios_livres_comecam_na_proxima_hora(cenario, db):
    item = _item(db, "Arena Centro")
    hoje = item.dias[0]
    assert hoje.rotulo == "Hoje"
    assert [h.inicio.hour for h in hoje.horarios] == [13, 14, 15, 16, 17, 18]


def test_horario_ocupado_some_quando_a_arena_tem_um_campo(cenario, db):
    _marcar(cenario["gabriel"], cenario, cenario["arena"]["campos"][0]["id"], "2026-10-28T13:00:00")
    horas = [h.inicio.hour for h in _item(db, "Arena Centro").dias[0].horarios]
    assert 13 not in horas and 14 in horas


def test_horario_continua_livre_se_outro_campo_esta_vago(cenario, db):
    arena = cenario["dono"].post("/api/v1/arenas", json={
        "nome": "Complexo Sul", "endereco": "Rua D, 4", "cidade": "Criciúma",
        "valor_hora": "150.00", "quantidade_campos": 2}).json()
    c1, c2 = (c["id"] for c in arena["campos"])
    _marcar(cenario["gabriel"], cenario, c1, "2026-10-28T13:00:00")
    treze = _item(db, "Complexo Sul").dias[0].horarios[0]
    assert treze.inicio.hour == 13
    assert treze.campo_id == c2  # o link de reserva aponta para o campo vago


def test_mostra_amanha_quando_hoje_esta_acabando(cenario, db, relogio_fixo):
    relogio_fixo["agora"] = datetime(2026, 10, 28, 20, 30)
    dias = _item(db, "Arena Centro").dias
    assert [d.rotulo for d in dias] == ["Hoje", "Amanhã"]
    assert [h.inicio.hour for h in dias[0].horarios] == [21, 22]
    assert [h.inicio.hour for h in dias[1].horarios] == [8, 9, 10, 11]


def test_destaque_aparece_primeiro_e_expira(cenario, db):
    cenario["dono"].post("/api/v1/arenas", json={
        "nome": "Arena Zeta", "endereco": "Rua Z, 1", "cidade": "Criciúma", "valor_hora": "100"})
    zeta = db.query(Arena).filter_by(nome="Arena Zeta").one()
    zeta.destaque_ate = AGORA.date()
    db.commit()
    itens = vitrine.montar(db)
    assert itens[0].arena.nome == "Arena Zeta" and itens[0].destaque

    zeta.destaque_ate = date(2026, 10, 27)  # venceu ontem
    db.commit()
    assert not _item(db, "Arena Zeta").destaque


def test_preco_a_partir_do_campo_mais_barato(cenario, db):
    dono, arena = cenario["dono"], cenario["arena"]
    dono.post(f"/api/v1/arenas/{arena['id']}/campos", json={"nome": "Campo 2", "valor_hora": "120.00"})
    assert str(_item(db, "Arena Centro").preco_minimo) == "120.00"


# ---------- tela ----------
def test_quadro_grande_mostra_as_arenas_e_filtra_por_cidade(cenario, cliente):
    cenario["dono"].post("/api/v1/arenas", json={
        "nome": "Içara Sports", "endereco": "Rua XV, 80", "cidade": "Içara", "valor_hora": "130"})
    r = cliente.get("/")
    assert "Arenas da região" in r.text
    assert "Arena Centro" in r.text and "Içara Sports" in r.text
    assert "/partidas/nova?campo_id=" in r.text

    r = cliente.get("/?cidade=içara")
    assert "Arenas em Içara" in r.text
    assert "Içara Sports" in r.text and "Arena Centro" not in r.text.split("vitrine-rodape")[0]


def test_cidade_desconhecida_mostra_todas(cenario, cliente):
    r = cliente.get("/?cidade=Atlantida")
    assert "Arenas da região" in r.text and "Arena Centro" in r.text


def test_clicar_no_horario_leva_ao_login_e_volta_com_a_reserva_preenchida(cenario, cliente):
    campo_id = cenario["arena"]["campos"][0]["id"]
    destino = f"/partidas/nova?campo_id={campo_id}&data=2026-10-28&hora=15:00"
    r = cliente.get(destino, follow_redirects=False)
    assert r.status_code == 303
    proximo = unquote(r.headers["location"].split("proximo=")[1])
    r = cliente.post("/entrar", data={"email": "gabriel@teste.com", "senha": "senha1234", "proximo": proximo},
                     follow_redirects=False)
    assert r.headers["location"] == destino
    tela = cenario["gabriel"].get(destino).text
    assert f'<option value="{campo_id}" selected>' in tela
    assert 'value="2026-10-28"' in tela and 'value="15:00"' in tela
