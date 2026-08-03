# ⚽ Sistema de Gerenciamento de Partidas

Sistema desenvolvido como projeto pessoal durante a graduação em Engenharia de Software, com o objetivo de aplicar na prática os conhecimentos adquiridos em programação, banco de dados e desenvolvimento de sistemas.

O projeto permite o gerenciamento de usuários, times, arenas e partidas de futebol suíço, utilizando Python e PostgreSQL.

---

# 📌 Objetivo

Desenvolver uma aplicação completa para colocar em prática conceitos estudados durante a graduação, simulando o desenvolvimento de um sistema real, desde a modelagem do banco de dados até a implementação das funcionalidades.

---

# 🚀 Funcionalidades

## Usuários

- Cadastro de usuários
- Listagem de usuários
- Atualização de usuários
- Exclusão de usuários

---

## Times

- Cadastro de times
- Listagem de times
- Atualização de times
- Exclusão de times

---

## Arenas

- Cadastro de arenas
- Listagem de arenas
- Atualização de arenas
- Exclusão de arenas

---

## Partidas

- Cadastro de partidas
- Listagem de partidas
- Atualização de partidas
- Exclusão de partidas

---

# 🛠 Tecnologias Utilizadas

- Python
- PostgreSQL
- SQL

---

# 💻 Conceitos Aplicados

Durante o desenvolvimento deste projeto foram aplicados conhecimentos de:

- Programação em Python
- Lógica de programação
- Organização do código em módulos
- Banco de dados relacional
- Modelagem de banco de dados
- Chaves primárias e estrangeiras
- Relacionamentos entre tabelas
- Operações CRUD
- Consultas SQL
- Trigger para implementação de regras de negócio

---

# 📂 Estrutura do Projeto

```
app_esportivo
│
├── arena.py
├── conexao.py
├── main.py
├── partida.py
├── times.py
├── usuario.py
└── README.md
```

---

# ▶ Como executar

## 1. Clone o repositório

```bash
git clone https://github.com/gabrieldalmolin06-wq/sistema_gerenciamento_partidas.git
```

---

## 2. Entre na pasta do projeto

```bash
cd sistema_gerenciamento_partidas
```

---

## 3. Configure o banco de dados

Crie o banco de dados PostgreSQL e execute o script SQL utilizado no projeto.

Depois configure as informações de conexão no arquivo:

```
conexao.py
```

---

## 4. Execute a aplicação

```bash
python main.py
```

---

# 🗄 Banco de Dados

O banco foi desenvolvido utilizando PostgreSQL.

A estrutura do sistema é composta por tabelas relacionadas para gerenciamento de:

- Usuários
- Times
- Arenas
- Partidas

Também foi implementada uma **Trigger** para aplicar uma regra de negócio diretamente no banco de dados.

---

# 📖 Aprendizados

Este projeto permitiu colocar em prática conhecimentos importantes da graduação, como:

- Desenvolvimento de aplicações em Python
- Organização de projetos
- Manipulação de banco de dados PostgreSQL
- Escrita de consultas SQL
- Desenvolvimento de operações CRUD
- Relacionamentos entre tabelas
- Implementação de regras de negócio
- Resolução de problemas durante o desenvolvimento

Além do aprendizado técnico, o projeto contribuiu para desenvolver habilidades como organização, persistência, resolução de problemas e busca contínua por novos conhecimentos.

---

# 📌 Próximas melhorias

Algumas funcionalidades poderão ser adicionadas futuramente:

- Sistema de autenticação de usuários
- Interface gráfica
- API para integração com aplicações web
- Melhorias na validação dos dados
- Relatórios e estatísticas das partidas

---

# 👨‍💻 Autor

**Gabriel Dalmolin**

Acadêmico de Engenharia de Software — UNISATC

📍 Criciúma - SC

GitHub:
https://github.com/gabrieldalmolin06-wq
