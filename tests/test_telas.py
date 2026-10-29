"""Testes das telas: garantem que as páginas renderizam e que os formulários funcionam."""

from tests.conftest import novo_cliente


def test_paginas_publicas(cliente):
    for url in ("/", "/entrar", "/cadastro", "/times", "/arenas", "/partidas", "/classificacao", "/docs"):
        r = cliente.get(url)
        assert r.status_code == 200, url


def test_pagina_protegida_redireciona_para_login(cliente):
    r = cliente.get("/times/novo", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"].startswith("/entrar?proximo=/times/novo")


def test_cadastro_pelo_formulario_e_painel(cliente):
    r = cliente.post("/cadastro", data={"nome": "Gabriel", "email": "g@t.com", "senha": "senha1234",
                                        "confirmar_senha": "senha1234", "tipo": "jogador"})
    assert r.status_code == 200
    assert "Seu painel" in r.text
    assert "Conta criada" in r.text


def test_cadastro_mostra_erros_em_portugues(cliente):
    r = cliente.post("/cadastro", data={"nome": "G", "email": "x", "senha": "1", "confirmar_senha": "2"})
    assert r.status_code == 400
    assert "As senhas não coincidem." in r.text
    assert "Informe um e-mail válido." in r.text
    assert "pelo menos 2 caracteres" in r.text


def test_login_errado_pelo_formulario(app, cliente):
    novo_cliente(app)
    r = cliente.post("/entrar", data={"email": "gabriel@teste.com", "senha": "errada"})
    assert r.status_code == 400
    assert "E-mail ou senha incorretos." in r.text


def test_login_nao_redireciona_para_outro_site(app, cliente):
    novo_cliente(app)
    r = cliente.post("/entrar", data={"email": "gabriel@teste.com", "senha": "senha1234",
                                      "proximo": "//site-malicioso.com"}, follow_redirects=False)
    assert r.headers["location"] == "/"


def test_fluxo_pelas_telas(cenario):
    g, l = cenario["gabriel"], cenario["lucas"]
    # Criar um segundo time pelo formulário
    r = g.post("/times/novo", data={"nome": "Galáticos", "cidade": "Criciúma"})
    assert "Time Galáticos criado." in r.text

    # Marcar partida pelo formulário
    r = g.post("/partidas/nova", data={
        "mandante_id": cenario["real"]["id"], "visitante_id": cenario["unidos"]["id"],
        "arena_id": cenario["arena"]["id"], "data": "2026-11-02", "hora": "19:00", "duracao_min": "60",
    })
    assert r.status_code == 200
    assert "Aguardando confirmação" in r.text
    assert "R$ 180,00" in r.text

    # O visitante vê o convite no painel e confirma
    painel = l.get("/")
    assert "Convites para confirmar" in painel.text
    pid = l.get("/api/v1/partidas").json()[0]["id"]
    r = l.post(f"/partidas/{pid}/confirmar")
    assert "Partida confirmada" in r.text


def test_formulario_de_partida_mostra_conflito(cenario):
    g = cenario["gabriel"]
    dados = {"mandante_id": cenario["real"]["id"], "visitante_id": cenario["unidos"]["id"],
             "arena_id": cenario["arena"]["id"], "data": "2026-11-02", "hora": "19:00", "duracao_min": "60"}
    g.post("/partidas/nova", data=dados)
    r = g.post("/partidas/nova", data=dados)
    assert r.status_code == 400
    assert "já está ocupada" in r.text


def test_acao_sem_permissao_vira_aviso(cenario):
    lucas = cenario["lucas"]
    r = lucas.post(f"/times/{cenario['real']['id']}/excluir", headers={"referer": "/times"})
    assert r.status_code == 200
    assert "Só o responsável pelo time pode alterá-lo." in r.text


def test_arena_aceita_valor_com_virgula(cenario):
    r = cenario["dono"].post("/arenas/nova", data={"nome": "Quadra Nova", "endereco": "Rua X, 9",
                                                   "cidade": "Içara", "telefone": "", "valor_hora": "1.250,50"})
    assert "R$ 1.250,50" in r.text
