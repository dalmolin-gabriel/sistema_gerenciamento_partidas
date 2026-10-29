from datetime import datetime

import pytest


def marcar(cliente, cen, inicio="2026-11-02T19:00:00", duracao=60, mandante=None, visitante=None, arena=None):
    return cliente.post("/api/v1/partidas", json={
        "mandante_id": mandante or cen["real"]["id"],
        "visitante_id": visitante or cen["unidos"]["id"],
        "arena_id": arena or cen["arena"]["id"],
        "inicio": inicio,
        "duracao_min": duracao,
    })


def test_marca_partida_aguardando_confirmacao(cenario):
    r = marcar(cenario["gabriel"], cenario)
    assert r.status_code == 201, r.text
    p = r.json()
    assert p["status"] == "agendada"
    assert p["valor_total"] == "180.00"


def test_time_nao_joga_contra_si_mesmo(cenario):
    r = marcar(cenario["gabriel"], cenario, visitante=cenario["real"]["id"])
    assert r.status_code == 422


def test_nao_marca_no_passado(cenario):
    assert marcar(cenario["gabriel"], cenario, inicio="2026-10-27T19:00:00").status_code == 422


def test_horario_em_intervalos_de_15_min(cenario):
    assert marcar(cenario["gabriel"], cenario, inicio="2026-11-02T19:07:00").status_code == 422


def test_so_marca_partida_para_o_proprio_time(cenario):
    # Lucas tenta escalar o time do Gabriel como mandante
    assert marcar(cenario["lucas"], cenario).status_code == 403


def test_conflito_de_arena_com_sobreposicao(cenario, app):
    from tests.conftest import novo_cliente

    g = cenario["gabriel"]
    assert marcar(g, cenario, inicio="2026-11-02T19:00:00", duracao=90).status_code == 201
    # Outro par de times, mesma arena, começando no meio do jogo anterior
    ana = novo_cliente(app, "Ana", "ana@teste.com")
    t1 = ana.post("/api/v1/times", json={"nome": "Içara"}).json()
    t2 = ana.post("/api/v1/times", json={"nome": "Içara B"}).json()
    r = marcar(ana, cenario, inicio="2026-11-02T20:00:00", mandante=t1["id"], visitante=t2["id"])
    assert r.status_code == 409
    assert "arena" in r.json()["detail"]
    # Logo após o término (20:30) está livre
    assert marcar(ana, cenario, inicio="2026-11-02T20:30:00", mandante=t1["id"], visitante=t2["id"]).status_code == 201


def test_conflito_de_time_em_outra_arena(cenario):
    dono = cenario["dono"]
    outra = dono.post("/api/v1/arenas", json={"nome": "Arena 2", "endereco": "Rua C, 3", "cidade": "Criciúma",
                                              "valor_hora": "120"}).json()
    g = cenario["gabriel"]
    assert marcar(g, cenario).status_code == 201
    r = marcar(g, cenario, arena=outra["id"], inicio="2026-11-02T19:30:00")
    assert r.status_code == 409
    assert "time" in r.json()["detail"]


def test_partida_cancelada_libera_horario(cenario):
    g = cenario["gabriel"]
    pid = marcar(g, cenario).json()["id"]
    assert g.post(f"/api/v1/partidas/{pid}/cancelar").json()["status"] == "cancelada"
    assert marcar(g, cenario).status_code == 201


def test_fluxo_completo_ate_classificacao(cenario, relogio_fixo):
    g, l = cenario["gabriel"], cenario["lucas"]
    pid = marcar(g, cenario).json()["id"]

    # Mandante não confirma o próprio convite; o visitante sim.
    assert g.post(f"/api/v1/partidas/{pid}/confirmar").status_code == 403
    assert l.post(f"/api/v1/partidas/{pid}/confirmar").json()["status"] == "confirmada"

    # Placar antes do jogo começar é recusado.
    assert g.post(f"/api/v1/partidas/{pid}/placar", json={"gols_mandante": 3, "gols_visitante": 1}).status_code == 422

    relogio_fixo["agora"] = datetime(2026, 11, 2, 20, 30)
    assert l.post(f"/api/v1/partidas/{pid}/placar", json={"gols_mandante": 0, "gols_visitante": 9}).status_code == 403
    r = g.post(f"/api/v1/partidas/{pid}/placar", json={"gols_mandante": 3, "gols_visitante": 1})
    assert r.json()["status"] == "finalizada"

    tabela = g.get("/api/v1/classificacao").json()
    assert [(t["time"], t["pontos"], t["saldo"]) for t in tabela] == [("Real Pró-Vida", 3, 2), ("Unidos FC", 0, -2)]
    # Finalizada não pode mais ser cancelada
    assert g.post(f"/api/v1/partidas/{pid}/cancelar").status_code == 422


def test_dono_da_arena_pode_lancar_placar(cenario, relogio_fixo):
    g, l, dono = cenario["gabriel"], cenario["lucas"], cenario["dono"]
    pid = marcar(g, cenario).json()["id"]
    l.post(f"/api/v1/partidas/{pid}/confirmar")
    relogio_fixo["agora"] = datetime(2026, 11, 2, 21, 0)
    assert dono.post(f"/api/v1/partidas/{pid}/placar", json={"gols_mandante": 2, "gols_visitante": 2}).status_code == 200


def test_mesmo_responsavel_nos_dois_times_ja_confirma(cenario):
    g = cenario["gabriel"]
    outro = g.post("/api/v1/times", json={"nome": "Galáticos"}).json()
    r = marcar(g, cenario, visitante=outro["id"])
    assert r.json()["status"] == "confirmada"


def test_remarcar_exige_nova_confirmacao(cenario):
    g, l = cenario["gabriel"], cenario["lucas"]
    pid = marcar(g, cenario).json()["id"]
    l.post(f"/api/v1/partidas/{pid}/confirmar")
    r = g.post(f"/api/v1/partidas/{pid}/remarcar", json={"inicio": "2026-11-03T20:00:00", "duracao_min": 90})
    assert r.status_code == 200
    assert r.json()["status"] == "agendada"
    assert r.json()["fim"] == "2026-11-03T21:30:00"
    assert l.post(f"/api/v1/partidas/{pid}/remarcar", json={"inicio": "2026-11-04T20:00:00"}).status_code == 403


def test_remarcar_para_o_mesmo_horario_nao_conflita_consigo_mesma(cenario):
    g = cenario["gabriel"]
    pid = marcar(g, cenario).json()["id"]
    r = g.post(f"/api/v1/partidas/{pid}/remarcar", json={"inicio": "2026-11-02T19:00:00", "duracao_min": 90})
    assert r.status_code == 200


def test_excluir_so_depois_de_cancelar(cenario):
    g = cenario["gabriel"]
    pid = marcar(g, cenario).json()["id"]
    assert g.delete(f"/api/v1/partidas/{pid}").status_code == 422
    g.post(f"/api/v1/partidas/{pid}/cancelar")
    assert g.delete(f"/api/v1/partidas/{pid}").status_code == 204
    assert g.get(f"/api/v1/partidas/{pid}").status_code == 404


def test_terceiro_nao_cancela(cenario, app):
    from tests.conftest import novo_cliente

    pid = marcar(cenario["gabriel"], cenario).json()["id"]
    estranho = novo_cliente(app, "Zé", "ze@teste.com")
    assert estranho.post(f"/api/v1/partidas/{pid}/cancelar").status_code == 403
    assert cenario["dono"].post(f"/api/v1/partidas/{pid}/cancelar").status_code == 200


@pytest.mark.parametrize("duracao", [15, 240])
def test_duracao_fora_do_limite(cenario, duracao):
    assert marcar(cenario["gabriel"], cenario, duracao=duracao).status_code == 422
