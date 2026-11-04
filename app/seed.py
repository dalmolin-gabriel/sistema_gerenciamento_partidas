"""Popula o banco com dados de demonstração.

Uso:  python -m app.seed
Cria usuários (senha de todos: senha1234), times, arenas e algumas partidas,
incluindo jogos finalizados para a classificação já aparecer preenchida.
Só roda se o banco estiver vazio.
"""

from datetime import timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import Arena, Campo, Partida, StatusPartida, Time, TipoUsuario, Usuario
from app.security import gerar_hash
from app.services import relogio


def main() -> None:
    db = SessionLocal()
    if db.scalar(select(func.count(Usuario.id))):
        print("O banco já tem dados. Nada foi feito.")
        return

    senha = gerar_hash("senha1234")
    gabriel = Usuario(nome="Gabriel Dalmolin", email="gabriel@exemplo.com", senha_hash=senha)
    lucas = Usuario(nome="Lucas Martins", email="lucas@exemplo.com", senha_hash=senha)
    ana = Usuario(nome="Ana Costa", email="ana@exemplo.com", senha_hash=senha)
    dono = Usuario(nome="Roberto Arena", email="arena@exemplo.com", senha_hash=senha,
                   tipo=TipoUsuario.PROPRIETARIO)
    db.add_all([gabriel, lucas, ana, dono])
    db.flush()

    # Gabriel é responsável por dois times: não existe mais limite de um time por pessoa.
    t = {
        "Real Pró-Vida": Time(nome="Real Pró-Vida", cidade="Criciúma", responsavel_id=gabriel.id),
        "Galáticos FC": Time(nome="Galáticos FC", cidade="Criciúma", responsavel_id=gabriel.id),
        "Unidos do Rio Maina": Time(nome="Unidos do Rio Maina", cidade="Criciúma", responsavel_id=lucas.id),
        "Atlético Próspera": Time(nome="Atlético Próspera", cidade="Criciúma", responsavel_id=lucas.id),
        "Içara Futsal Clube": Time(nome="Içara Futsal Clube", cidade="Içara", responsavel_id=ana.id),
    }
    db.add_all(t.values())
    a1 = Arena(nome="Arena Centro", endereco="Rua Henrique Lage, 500", cidade="Criciúma",
               telefone="(48) 3433-0000", valor_hora=Decimal("180.00"), proprietario_id=dono.id)
    a2 = Arena(nome="Society Pinheirinho", endereco="Av. Centenário, 2200", cidade="Criciúma",
               telefone="(48) 99999-1234", valor_hora=Decimal("150.00"), proprietario_id=dono.id)
    # A Arena Centro tem três campos; o Society coberto é mais caro.
    a1.campos = [Campo(nome="Campo 1"), Campo(nome="Campo 2"),
                 Campo(nome="Society coberto", valor_hora=Decimal("220.00"))]
    a2.campos = [Campo(nome="Campo 1")]
    a3 = Arena(nome="Içara Sports", endereco="Rua XV de Novembro, 80", cidade="Içara",
               telefone="(48) 3462-0000", valor_hora=Decimal("130.00"), proprietario_id=dono.id)
    a3.campos = [Campo(nome="Campo 1"), Campo(nome="Campo 2")]
    # A Arena Centro pagou destaque na vitrine da página inicial por 30 dias.
    a1.destaque_ate = (relogio.agora() + timedelta(days=30)).date()
    db.add_all([a1, a2, a3])
    db.flush()

    hoje = relogio.agora().replace(hour=19, minute=0, second=0)

    def jogo(dias, hora, m, v, arena, status, placar=None, duracao=60, campo=0):
        inicio = (hoje + timedelta(days=dias)).replace(hour=hora)
        p = Partida(inicio=inicio, duracao_min=duracao, status=status, mandante_id=t[m].id,
                    visitante_id=t[v].id, arena_id=arena.id, campo_id=arena.campos[campo].id,
                    criado_por_id=t[m].responsavel_id)
        if placar:
            p.gols_mandante, p.gols_visitante = placar
        db.add(p)

    F, C, A = StatusPartida.FINALIZADA, StatusPartida.CONFIRMADA, StatusPartida.AGENDADA
    jogo(-21, 19, "Real Pró-Vida", "Unidos do Rio Maina", a1, F, (4, 2))
    jogo(-20, 20, "Atlético Próspera", "Içara Futsal Clube", a2, F, (1, 1))
    jogo(-14, 19, "Galáticos FC", "Atlético Próspera", a1, F, (2, 3))
    jogo(-13, 21, "Içara Futsal Clube", "Real Pró-Vida", a2, F, (0, 2))
    jogo(-7, 19, "Unidos do Rio Maina", "Galáticos FC", a1, F, (5, 5))
    jogo(-6, 20, "Real Pró-Vida", "Atlético Próspera", a2, F, (3, 1))
    jogo(2, 19, "Real Pró-Vida", "Galáticos FC", a1, C)
    jogo(3, 20, "Unidos do Rio Maina", "Real Pró-Vida", a2, A, duracao=90)
    jogo(2, 19, "Içara Futsal Clube", "Atlético Próspera", a1, C, campo=2)  # mesmo horário, outro campo
    jogo(6, 21, "Atlético Próspera", "Galáticos FC", a2, A)
    jogo(0, 21, "Unidos do Rio Maina", "Içara Futsal Clube", a2, C)  # hoje: ocupa o 21h do Pinheirinho
    db.commit()
    print("Dados de exemplo criados. Entre com gabriel@exemplo.com / senha1234")


if __name__ == "__main__":
    main()
