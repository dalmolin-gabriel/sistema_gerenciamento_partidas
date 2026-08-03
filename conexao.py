import psycopg2

def conectar():
    conexao = psycopg2.connect(
    host = "localhost",
    database = "app_esportivo",
    user = "postgres",
    password = "123456",
    port = "5433"
    )
    return conexao
