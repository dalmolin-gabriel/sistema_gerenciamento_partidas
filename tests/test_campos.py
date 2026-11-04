"""Arenas com vários campos: cada campo tem a sua agenda e pode ter preço próprio."""

from tests.conftest import novo_cliente


def _arena_com_campos(cen, quantidade=2, **extra):
    return cen["dono"].post("/api/v1/arenas", json={
        "nome": "Complexo Sul", "endereco": "Rua D, 4", "cidade": "Criciúma",
        "valor_hora": "150.00", "quantidade_campos": quantidade, **extra,
    }).json()


def _marcar(cliente, mandante, visitante, campo_id=None, arena_id=None, inicio="2026-11-02T19:00:00", duracao=60):
    corpo = {"mandante_id": mandante, "visitante_id": visitante, "inicio": inicio, "duracao_min": duracao}
    if campo_id:
        corpo["campo_id"] = campo_id
    if arena_id:
        corpo["arena_id"] = arena_id
    return cliente.post("/api/v1/partidas", json=corpo)


def _outro_par(app):
    ana = novo_cliente(app, "Ana", "ana@teste.com")
    t1 = ana.post("/api/v1/times", json={"nome": "Içara"}).json()
    t2 = ana.post("/api/v1/times", json={"nome": "Içara B"}).json()
    return ana, t1["id"], t2["id"]


def test_arena_nasce_com_os_campos_pedidos(cenario):
    arena = _arena_com_campos(cenario, 3)
    assert [c["nome"] for c in arena["campos"]] == ["Campo 1", "Campo 2", "Campo 3"]
    # Sem informar, a arena tem um campo só.
    assert len(cenario["arena"]["campos"]) == 1


def test_dois_jogos_no_mesmo_horario_em_campos_diferentes(cenario, app):
    arena = _arena_com_campos(cenario)
    c1, c2 = (c["id"] for c in arena["campos"])
    g = cenario["gabriel"]
    assert _marcar(g, cenario["real"]["id"], cenario["unidos"]["id"], c1).status_code == 201

    ana, t1, t2 = _outro_par(app)
    assert _marcar(ana, t1, t2, c2).status_code == 201


def test_mesmo_campo_continua_com_conflito(cenario, app):
    arena = _arena_com_campos(cenario)
    c1 = arena["campos"][0]["id"]
    _marcar(cenario["gabriel"], cenario["real"]["id"], cenario["unidos"]["id"], c1, duracao=90)

    ana, t1, t2 = _outro_par(app)
    r = _marcar(ana, t1, t2, c1, inicio="2026-11-02T20:00:00")
    assert r.status_code == 409
    assert "Campo 1" in r.json()["detail"]


def test_time_nao_joga_em_dois_campos_ao_mesmo_tempo(cenario, app):
    arena = _arena_com_campos(cenario)
    c1, c2 = (c["id"] for c in arena["campos"])
    g = cenario["gabriel"]
    _marcar(g, cenario["real"]["id"], cenario["unidos"]["id"], c1)
    outro = g.post("/api/v1/times", json={"nome": "Galáticos"}).json()
    r = _marcar(g, cenario["real"]["id"], outro["id"], c2)
    assert r.status_code == 409
    assert "Real Pró-Vida" in r.json()["detail"]


def test_arena_com_varios_campos_exige_escolher_o_campo(cenario):
    arena = _arena_com_campos(cenario)
    r = _marcar(cenario["gabriel"], cenario["real"]["id"], cenario["unidos"]["id"], arena_id=arena["id"])
    assert r.status_code == 422
    assert "Escolha em qual" in r.json()["detail"]


def test_arena_com_um_campo_aceita_so_a_arena(cenario):
    r = _marcar(cenario["gabriel"], cenario["real"]["id"], cenario["unidos"]["id"], arena_id=cenario["arena"]["id"])
    assert r.status_code == 201
    assert r.json()["campo"]["nome"] == "Campo 1"


def test_campo_precisa_ser_da_arena_informada(cenario):
    arena = _arena_com_campos(cenario)
    r = _marcar(cenario["gabriel"], cenario["real"]["id"], cenario["unidos"]["id"],
                campo_id=arena["campos"][0]["id"], arena_id=cenario["arena"]["id"])
    assert r.status_code == 422


def test_preco_proprio_do_campo(cenario):
    arena = _arena_com_campos(cenario)
    dono = cenario["dono"]
    c2 = arena["campos"][1]["id"]
    r = dono.put(f"/api/v1/arenas/{arena['id']}/campos/{c2}", json={"nome": "Coberto", "valor_hora": "200.00"})
    assert r.json()["preco_hora"] == "200.00"
    p = _marcar(cenario["gabriel"], cenario["real"]["id"], cenario["unidos"]["id"], c2, duracao=90).json()
    assert p["valor_total"] == "300.00"
    # O outro campo segue o preço da arena.
    assert dono.get(f"/api/v1/arenas/{arena['id']}/campos").json()[0]["preco_hora"] == "150.00"


def test_gestao_de_campos_so_pelo_dono(cenario):
    arena = _arena_com_campos(cenario)
    url = f"/api/v1/arenas/{arena['id']}/campos"
    assert cenario["gabriel"].post(url, json={"nome": "Campo 3"}).status_code == 403
    dono = cenario["dono"]
    assert dono.post(url, json={"nome": "Campo 3"}).status_code == 201
    assert dono.post(url, json={"nome": "  campo 3 "}).status_code == 409


def test_excluir_campo(cenario):
    dono = cenario["dono"]
    # Não pode ficar sem nenhum campo.
    unico = cenario["arena"]["campos"][0]["id"]
    assert dono.delete(f"/api/v1/arenas/{cenario['arena']['id']}/campos/{unico}").status_code == 422

    arena = _arena_com_campos(cenario, 3)
    c1, c2, c3 = (c["id"] for c in arena["campos"])
    _marcar(cenario["gabriel"], cenario["real"]["id"], cenario["unidos"]["id"], c1)
    # Campo com partida fica no histórico.
    assert dono.delete(f"/api/v1/arenas/{arena['id']}/campos/{c1}").status_code == 409
    assert dono.delete(f"/api/v1/arenas/{arena['id']}/campos/{c3}").status_code == 204
    assert len(dono.get(f"/api/v1/arenas/{arena['id']}/campos").json()) == 2


def test_remarcar_para_outro_campo(cenario):
    arena = _arena_com_campos(cenario)
    c1, c2 = (c["id"] for c in arena["campos"])
    g = cenario["gabriel"]
    pid = _marcar(g, cenario["real"]["id"], cenario["unidos"]["id"], c1).json()["id"]
    r = g.post(f"/api/v1/partidas/{pid}/remarcar", json={"inicio": "2026-11-02T19:00:00", "campo_id": c2})
    assert r.status_code == 200
    assert r.json()["campo"]["id"] == c2
    # Campo de outra arena é recusado.
    outro = cenario["arena"]["campos"][0]["id"]
    assert g.post(f"/api/v1/partidas/{pid}/remarcar", json={"inicio": "2026-11-02T19:00:00",
                                                            "campo_id": outro}).status_code == 422


# ---------- telas ----------
def test_telas_de_arena_com_campos(cenario):
    dono, g = cenario["dono"], cenario["gabriel"]
    r = dono.post("/arenas/nova", data={"nome": "Complexo Norte", "endereco": "Rua E, 5", "cidade": "Içara",
                                        "telefone": "", "valor_hora": "120,00", "quantidade_campos": "2"})
    assert "Complexo Norte" in r.text and "Campo 2" in r.text
    arena = next(a for a in g.get("/api/v1/arenas").json() if a["nome"] == "Complexo Norte")

    r = dono.post(f"/arenas/{arena['id']}/campos/novo", data={"nome": "Areia", "valor_hora": "90,00"})
    assert "Campo “Areia” adicionado." in r.text

    c2 = arena["campos"][1]["id"]
    r = g.post("/partidas/nova", data={
        "mandante_id": cenario["real"]["id"], "visitante_id": cenario["unidos"]["id"], "campo_id": c2,
        "data": "2026-11-02", "hora": "19:00", "duracao_min": "60",
    })
    assert r.status_code == 200
    assert "Complexo Norte</a> · Campo 2" in r.text

    pagina = g.get(f"/arenas/{arena['id']}?campo={c2}")
    assert "Real Pró-Vida" in pagina.text
    vazia = g.get(f"/arenas/{arena['id']}?campo={arena['campos'][0]['id']}")
    assert "Agenda livre" in vazia.text


def test_form_de_partida_vindo_da_arena_ja_escolhe_o_campo(cenario):
    r = cenario["gabriel"].get(f"/partidas/nova?arena_id={cenario['arena']['id']}")
    campo_id = cenario["arena"]["campos"][0]["id"]
    assert f'<option value="{campo_id}" selected>' in r.text
