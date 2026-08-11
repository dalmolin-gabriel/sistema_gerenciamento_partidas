import psycopg2

def conectar():
    conexao = psycopg2.connect(
    host = "",
    database = "",
    user = "",
    password = "",
    port = ""
    )
    return conexao
