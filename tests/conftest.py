import os
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.database import Base, criar_engine, get_db
from app.main import create_app
from app.services import relogio

# Por padrão os testes usam SQLite em memória. Para testar no PostgreSQL:
#   TEST_DATABASE_URL=postgresql+psycopg://usuario:senha@localhost/partidas_teste pytest
URL = os.getenv("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")
AGORA = datetime(2026, 10, 28, 12, 0)


@pytest.fixture
def engine():
    if URL.startswith("sqlite"):
        from sqlalchemy.pool import StaticPool
        from sqlalchemy import create_engine

        eng = create_engine(URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    else:
        eng = criar_engine(URL)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db(engine):
    sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    yield sessao
    sessao.close()


@pytest.fixture(autouse=True)
def relogio_fixo(monkeypatch):
    estado = {"agora": AGORA}
    monkeypatch.setattr(relogio, "agora", lambda: estado["agora"])
    return estado


@pytest.fixture
def app(engine):
    aplicacao = create_app()
    Sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def _db():
        s = Sessao()
        try:
            yield s
        finally:
            s.close()

    aplicacao.dependency_overrides[get_db] = _db
    return aplicacao


@pytest.fixture
def cliente(app):
    return TestClient(app)


def novo_cliente(app, nome="Gabriel", email="gabriel@teste.com", tipo="jogador") -> TestClient:
    c = TestClient(app)
    r = c.post("/api/v1/auth/cadastro", json={"nome": nome, "email": email, "senha": "senha1234", "tipo": tipo})
    assert r.status_code == 201, r.text
    c.usuario = r.json()
    return c


@pytest.fixture
def cenario(app):
    """Dois responsáveis de time, um dono de arena, dois times e uma arena."""
    gabriel = novo_cliente(app, "Gabriel", "gabriel@teste.com")
    lucas = novo_cliente(app, "Lucas", "lucas@teste.com")
    dono = novo_cliente(app, "Roberto", "arena@teste.com", tipo="proprietario")
    real = gabriel.post("/api/v1/times", json={"nome": "Real Pró-Vida", "cidade": "Criciúma"}).json()
    unidos = lucas.post("/api/v1/times", json={"nome": "Unidos FC"}).json()
    arena = dono.post("/api/v1/arenas", json={
        "nome": "Arena Centro", "endereco": "Rua A, 10", "cidade": "Criciúma",
        "telefone": "(48) 3433-0000", "valor_hora": "180.00",
    }).json()
    return dict(gabriel=gabriel, lucas=lucas, dono=dono, real=real, unidos=unidos, arena=arena)
