# importa conexao com o banco
from conexao import conectar        

# cadastrar usuario
def cadastrar_usuario():
    nome = input(f"Nome: ")
    email = input(f"Email: ")
    senha = input(f"Senha: ")
  

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        while True:
            tipo = input(f"Tipo do usuário: [Capitao] or [Proprietário]: ")
            if tipo not in ("Capitao","Proprietário"):
                print("Tipo de usuário inválido. Tente Novamente")
                continue
            break
        
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo_usuario) VALUES (%s, %s, %s, %s)",
                (nome, email, senha, tipo)
        )           
        conexao.commit()
        print("Usuário cadastrado com sucesso!")

    finally:
            cursor.close()
            conexao.close()


def listar_usuario():

    conexao = conectar()
    cursor = conexao.cursor()

    try:

        cursor.execute("""
            select 
                id_usuario,
                nome,
                email,
                senha,
                tipo_usuario
            from usuarios
        """)

        usuarios = cursor.fetchall()
        for usuario in usuarios:
             print(f"\nID usuário: {usuario[0]}")
             print(f"Nome: {usuario[1]}")
             print(f"Email: {usuario[2]}")
             print(f"Senha: {usuario[3]}")
             print(f"Tipo do usuário: {usuario[4]}")
             print("=" * 40)

    finally:
        cursor.close()
        conexao.close()

def editar_usuario():

    conexao = conectar()
    cursor = conexao.cursor()


    try:
        while True:        
                editar = input(f"Editar o usuário: [S] ou [N]: ").upper()
                if editar == "N":
                           return
                elif editar == "S":
                       listar_usuario()
                       break
                else:
                    print("Tipo inválido. Tente novamente")

        while True:
            idusuario = int(input(f"ID do usuário: "))
            cursor.execute("""
                select 
                    id_usuario
                from usuarios
                where id_usuario = %s
            """,
            (idusuario,)
            )
            
            if cursor.fetchone() is None:
                print("Usuário não encontrado. Tente novamente")
                continue
            break
        while True:
            opcao = int(input(
                "\nEscolha uma opção:\n"
                "1 - Novo nome\n"
                "2 - Novo email\n"
                "3 - Nova senha\n"
                "Opção: "
            ))

            if opcao == 1:
                novo_nome = input("Novo nome: ")
                cursor.execute(
                    """
                        update usuarios
                        set nome = %s
                        where id_usuario = %s
                    """,
                    (novo_nome, idusuario)
                )
                print("Nome atualizado com sucesso!")
                break

            elif opcao == 2:
                novo_email = input("Novo email: ")
                cursor.execute("""
                        update usuarios
                        set email = %s
                        where id_usuario = %s     
                    """,
                    (novo_email, idusuario)
                ) 
                print("Email atualizado com sucesso!")
                break

            elif opcao == 3:
                nova_senha = input("Nova senha: ")
                cursor.execute("""
                        update usuarios
                        set senha = %s
                        where id_usuario = %s     
                    """,
                    (nova_senha, idusuario)
                ) 
                print("Senha atualizado com sucesso!")
                break
            else:
                print("Opção inválida. Tente novamente.")
        conexao.commit()
    finally:
       cursor.close()
       conexao.close()

def excluir_usuario():



    conexao = conectar()
    cursor = conexao.cursor()

    try:
        while True:
            deletar = input("Excluir usuário [S] ou [N]: ").upper()
            if deletar == "N":
                return
            elif deletar == "S":

                cursor.execute("""
                    select
	                    id_usuario,
	                    nome,
	                    tipo_usuario
                    from usuarios
                """)
                usuarios = cursor.fetchall()
                for usuario in usuarios:
                     print(f"\nID: {usuario[0]} ")
                     print(f"Nome: {usuario[1]} ")
                     print(f"Tipo: {usuario[2]} ")
                     print("=" * 40)
                 
                # ver se existe o ID do usuario
                id_usuario = int(input("ID do usuário: "))
                cursor.execute("""
                    select
                        id_usuario
                    from usuarios
                    where id_usuario = %s
                """,
                (id_usuario,)
                 )
                if cursor.fetchone() is None:
                    print("ID do usuário não encontrado. Tente novamente.")
                    continue

                #  id para deletar o usuario
                
                cursor.execute(
                      """
                        delete from usuarios
                        where id_usuario = %s
                      """,    
                        (id_usuario,)
                    )
                conexao.commit()
                print(f"{usuario[2]} excluído com sucesso!")
                
                break
            
            else:   
                print("Opção inválida! Tente novamente.")

    finally:
         cursor.close()
         conexao.close()


def menu_usuario():
    while True:
        print(f"\n=== Menu Usuário ===")
        print("1 - Cadastrar usuário")
        print("2 - Listar usuário")
        print("3 - Editar usuário")
        print("4 - Excluir usuário")
        print("0 - Sair")

        opcao = int(input(f"Digite a opção: "))

        if opcao == 1:
            cadastrar_usuario()

        elif opcao == 2:
            listar_usuario()

        elif opcao == 3:
            editar_usuario()

        elif opcao == 4:
            excluir_usuario()

        elif opcao == 0:
            print("Sessão encerrada!")
            break 
        else:
            print("Opção inválida. Tente novamente")
