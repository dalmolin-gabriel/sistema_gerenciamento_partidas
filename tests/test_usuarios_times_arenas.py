from sqlalchemy import select

from app.models import Usuario
from tests.conftest import novo_cliente


def test_cadastro_guarda_senha_com_hash(app, db):
    novo_cliente(app)
    usuario = db.scalar(select(Usuario))
    assert usuario.senha_hash != "senha1234"
    assert usuario.senha_hash.startswith("$2")


def test_cadastro_nao_expoe_senha(app):
    c = novo_cliente(app)
    assert "senha" not in c.usuario and "senha_hash" not in c.usuario


def test_email_duplicado(app, cliente):
    novo_cliente(app)
    r = cliente.post("/api/v1/auth/cadastro", json={"nome": "Outro", "email": "GABRIEL@teste.com", "senha": "senha1234"})
    assert r.status_code == 409


def test_senha_curta_e_email_invalido(cliente):
    r = cliente.post("/api/v1/auth/cadastro", json={"nome": "X Y", "email": "nao-e-email", "senha": "123"})
    assert r.status_code == 422


def test_login_e_senha_errada(app, cliente):
    novo_cliente(app)
    assert cliente.post("/api/v1/auth/login", json={"email": "gabriel@teste.com", "senha": "errada123"}).status_code == 401
    assert cliente.post("/api/v1/auth/login", json={"email": "gabriel@teste.com", "senha": "senha1234"}).status_code == 200
    assert cliente.get("/api/v1/auth/eu").json()["email"] == "gabriel@teste.com"


def test_rotas_protegidas_exigem_login(cliente):
    assert cliente.post("/api/v1/times", json={"nome": "Sem Dono"}).status_code == 401


def test_usuario_pode_ter_varios_times(app):
    """A antiga restrição de um time por capitão foi removida."""
    c = novo_cliente(app)
    for nome in ("Time A", "Time B", "Time C"):
        assert c.post("/api/v1/times", json={"nome": nome}).status_code == 201
    meus = [t for t in c.get("/api/v1/times").json() if t["responsavel_id"] == c.usuario["id"]]
    assert len(meus) == 3


def test_nome_de_time_unico_sem_diferenciar_maiusculas(app):
    c = novo_cliente(app)
    c.post("/api/v1/times", json={"nome": "Real Pró-Vida"})
    assert c.post("/api/v1/times", json={"nome": "  real   pró-vida "}).status_code == 409


def test_somente_responsavel_edita_e_exclui_time(cenario):
    lucas, real = cenario["lucas"], cenario["real"]
    assert lucas.put(f"/api/v1/times/{real['id']}", json={"nome": "Hackeado"}).status_code == 403
    assert lucas.delete(f"/api/v1/times/{real['id']}").status_code == 403
    gabriel = cenario["gabriel"]
    assert gabriel.put(f"/api/v1/times/{real['id']}", json={"nome": "Real 2026"}).json()["nome"] == "Real 2026"


def test_time_com_partida_nao_pode_ser_excluido(cenario):
    g = cenario["gabriel"]
    g.post("/api/v1/partidas", json={"mandante_id": cenario["real"]["id"], "visitante_id": cenario["unidos"]["id"],
                                     "arena_id": cenario["arena"]["id"], "inicio": "2026-11-02T19:00:00"})
    assert g.delete(f"/api/v1/times/{cenario['real']['id']}").status_code == 409


def test_apenas_proprietario_cadastra_arena(cenario):
    dados = {"nome": "Quadra", "endereco": "Rua B, 1", "cidade": "Içara", "valor_hora": "100"}
    assert cenario["gabriel"].post("/api/v1/arenas", json=dados).status_code == 403
    assert cenario["dono"].post("/api/v1/arenas", json=dados).status_code == 201


def test_arena_valida_telefone_e_valor(cenario):
    dono = cenario["dono"]
    base = {"nome": "Quadra", "endereco": "Rua B, 1", "cidade": "Içara"}
    assert dono.post("/api/v1/arenas", json=base | {"valor_hora": "-5"}).status_code == 422
    assert dono.post("/api/v1/arenas", json=base | {"valor_hora": "90", "telefone": "123"}).status_code == 422


def test_filtro_de_arena_por_cidade(cenario):
    assert len(cenario["gabriel"].get("/api/v1/arenas?cidade=crici").json()) == 1
    assert cenario["gabriel"].get("/api/v1/arenas?cidade=Tubarão").json() == []
