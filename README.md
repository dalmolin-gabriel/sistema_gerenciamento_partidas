# ⚽ Partidas — Gestão de Futebol Suíço

Aplicação web para organizar partidas de futebol suíço: responsáveis de time marcam jogos, donos de arena
cadastram suas quadras, o sistema impede conflito de horário e a classificação se atualiza a cada placar.

Começou como um projeto de terminal na graduação em Engenharia de Software (UNISATC) e evoluiu para uma
aplicação web completa, com login, API REST documentada, banco versionado por migrações, testes
automatizados e Docker.

---

## Funcionalidades

**Contas e acesso**
- Cadastro e login com senha protegida por hash (bcrypt). A senha nunca é guardada nem exibida.
- Dois perfis: **jogador/responsável de time** e **dono de arena** (que também pode ter times).

**Times**
- Qualquer usuário pode criar e ser responsável por **quantos times quiser**.
- Nome de time único (sem diferenciar maiúsculas/minúsculas).
- Só o responsável edita ou exclui o time. Times com histórico de partidas não podem ser excluídos.
- Página do time com próximos jogos, histórico e desempenho na tabela.

**Arenas**
- Cadastradas por contas de proprietário, com endereço, cidade, telefone e valor da hora.
- Busca por cidade e agenda de horários reservados.

**Partidas**
- Ciclo de vida: `agendada → confirmada → finalizada`, podendo ser `cancelada` antes de finalizar.
- O responsável marca uma partida para o seu time contra qualquer adversário.
- O responsável pelo time visitante recebe o convite no painel e confirma.
  Se a mesma pessoa cuida dos dois times, a partida já nasce confirmada.
- **Sem conflito de horário**: a arena não pode ter dois jogos sobrepostos, e nenhum time pode estar em
  dois jogos ao mesmo tempo, mesmo em arenas diferentes. A verificação considera a duração do jogo.
- Regras de agenda: só datas futuras (até 1 ano), início em intervalos de 15 minutos, duração de 30 a 180 min.
- Remarcar exige nova confirmação do adversário. Cancelar libera o horário.
- Placar lançado pelo mandante ou pelo dono da arena, só depois do início do jogo.
- Valor da reserva calculado pela duração × valor da hora.

**Classificação**
- Vitória 3 pontos, empate 1. Desempate por vitórias, saldo de gols e gols pró.

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12, FastAPI |
| Banco de dados | PostgreSQL 16, SQLAlchemy 2, Alembic (migrações) |
| Telas | HTML renderizado no servidor (Jinja2) + CSS próprio, responsivo e com modo escuro |
| Validação | Pydantic, com mensagens de erro em português |
| Testes | pytest (40 testes, rodam em SQLite e PostgreSQL) |
| Infra | Docker, Docker Compose, GitHub Actions |

---

## Como executar

### Opção 1 — Docker (mais simples)

```bash
docker compose up --build
```

Acesse **http://localhost:8000**. As migrações do banco rodam sozinhas.

Para carregar dados de demonstração (times, arenas, jogos e tabela preenchida):

```bash
docker compose exec app python -m app.seed
```

Entre com `gabriel@exemplo.com` / `senha1234`. Outras contas: `lucas@`, `ana@` e `arena@exemplo.com` (dono de arena), todas com a mesma senha.

### Opção 2 — Local, com seu PostgreSQL

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

cp .env.example .env               # ajuste DATABASE_URL e SECRET_KEY
alembic upgrade head               # cria as tabelas
python -m app.seed                 # opcional: dados de exemplo
uvicorn app.main:app --reload
```

---

## API REST

A documentação interativa fica em **http://localhost:8000/docs** (Swagger).

Principais rotas (prefixo `/api/v1`):

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/cadastro`, `/auth/login`, `/auth/logout` | Conta e sessão |
| GET | `/auth/eu` | Usuário logado |
| GET/POST | `/times` | Listar (com `?busca=`) / criar |
| PUT/DELETE | `/times/{id}` | Editar / excluir |
| GET/POST | `/arenas` | Listar (com `?cidade=`) / criar |
| GET/POST | `/partidas` | Listar (filtros `status`, `time_id`, `arena_id`, `futuras`) / marcar |
| POST | `/partidas/{id}/confirmar` | Visitante aceita |
| POST | `/partidas/{id}/remarcar` | Novo horário |
| POST | `/partidas/{id}/cancelar` | Cancela |
| POST | `/partidas/{id}/placar` | Finaliza com placar |
| GET | `/classificacao` | Tabela |

Erros de regra de negócio retornam uma mensagem clara em `detail`, com o status adequado:
`401` sem login, `403` sem permissão, `404` não encontrado, `409` conflito (horário ocupado, nome repetido),
`422` dado inválido.

---

## Testes

```bash
pytest                       # SQLite em memória, sem configurar nada
TEST_DATABASE_URL=postgresql+psycopg://partidas:partidas@localhost/partidas_teste pytest
```

Os testes cobrem as regras de negócio (conflitos de horário, permissões, ciclo de vida da partida,
classificação) e as telas (formulários, mensagens de erro, redirecionamentos). O GitHub Actions roda tudo
em PostgreSQL a cada push.

---

## Estrutura

```
app/
├── main.py              # cria a aplicação e trata os erros
├── config.py            # configurações via .env
├── database.py          # conexão SQLAlchemy
├── models.py            # tabelas
├── schemas.py           # validação de entrada e saída
├── security.py          # hash de senha
├── deps.py              # usuário logado
├── errors.py            # erros de domínio
├── seed.py              # dados de demonstração
├── services/            # regras de negócio (independentes de web)
│   ├── usuarios.py  times.py  arenas.py  partidas.py  classificacao.py
├── api/routes.py        # API REST (JSON)
├── web/                 # telas
│   ├── routes.py  ui.py
├── templates/           # HTML (Jinja2)
└── static/              # CSS e ícone
alembic/                 # migrações do banco
tests/                   # testes automatizados
```

A regra de negócio vive só em `services/`. A API e as telas apenas chamam esses serviços, então uma regra
nova vale automaticamente para os dois.

---

## Produção

- Defina `SECRET_KEY` com um valor aleatório e longo.
- Com HTTPS, use `COOKIE_SEGURO=true`.
- Reserva simultânea do mesmo horário é protegida por trava na linha da arena (`SELECT ... FOR UPDATE`).

---

## Autor

**Gabriel Dalmolin** — Acadêmico de Engenharia de Software, UNISATC · Criciúma, SC
GitHub: [dalmolin-gabriel](https://github.com/dalmolin-gabriel)
