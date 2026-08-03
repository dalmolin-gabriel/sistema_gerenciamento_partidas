CREATE DATABASE app_esportivo_mvp;

\c app_esportivo_mvp;

-- =========================
-- TABELA USUÁRIOS
-- =========================
CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    tipo_usuario VARCHAR(20) NOT NULL
);

-- =========================
-- TABELA TIMES
-- =========================
CREATE TABLE times (
    id_time SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    id_capitao INT NOT NULL UNIQUE,
    
    CONSTRAINT fk_capitao
        FOREIGN KEY (id_capitao)
        REFERENCES usuarios(id_usuario)
);

-- =========================
-- TABELA ARENAS
-- =========================
CREATE TABLE arenas (
    id_arena SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    endereco VARCHAR(200) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    telefone VARCHAR(20),
    valor_hora NUMERIC(10,2) NOT NULL,
    id_proprietario INT NOT NULL,

    CONSTRAINT fk_proprietario
        FOREIGN KEY (id_proprietario)
        REFERENCES usuarios(id_usuario)
);

-- =========================
-- TABELA PARTIDAS
-- =========================
CREATE TABLE partidas (
    id_partida SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    horario TIME NOT NULL,
    status VARCHAR(20) NOT NULL,

    id_time_mandante INT NOT NULL,
    id_time_visitante INT NOT NULL,
    id_arena INT NOT NULL,

    CONSTRAINT fk_time_mandante
        FOREIGN KEY (id_time_mandante)
        REFERENCES times(id_time),

    CONSTRAINT fk_time_visitante
        FOREIGN KEY (id_time_visitante)
        REFERENCES times(id_time),

    CONSTRAINT fk_arena
        FOREIGN KEY (id_arena)
        REFERENCES arenas(id_arena)
);