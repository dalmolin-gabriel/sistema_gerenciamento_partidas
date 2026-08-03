from conexao import conectar

# cadastrar time

def cadastrar_time():
    nome = input('Time: ')
    idcapitao = int(input(f"ID capitão: "))

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        "insert into times (nome, id_capitao) values (%s, %s)",
        (nome, idcapitao)
    )
    conexao.commit()
    cursor.close()
    conexao.close()
    print(f"Time cadastrado com sucesso!")

def listar_time():

    #conexao com o banco
    conexao = conectar()
    cursor = conexao.cursor()

    # mostrar os times 

    cursor.execute(
        """
            select nome as time
            from times
        """
    )

    times = cursor.fetchall()
    print("Times ativos")
    print(f"-" * 40)
    for time in times:
        print(F"Time: {time[0]}")
     


    cursor.close()
    conexao.close()

def editar_time():

    conexao = conectar()
    cursor = conexao.cursor()

    try:
            
        while True:
            idtime = int(input(F"Digite o ID do seu time: "))

            # verficar se o ID do time existe
            cursor.execute(
                """
                    select id_time
                    from times
                    where id_time = %s
                """,
                (idtime,)
            )
            
            if cursor.fetchone() is None:
                print(f"Time do ID {idtime} não encontrado. Tente novamente")
                continue
            break
        # deseja alterar o nome do seu time?
        alterar_nome = input(f"Deseja alterar o nome do seu time: [S] ou [N]: ").upper()
        if alterar_nome == "S":
            novo_nome = input(f"Digite o novo nome do seu time: ")

            cursor.execute(
                """
                    update times
                    set nome = %s
                    where id_time = %s
                """,
                (novo_nome, idtime)
            )

            conexao.commit()
            print("Nome do time atualizado com sucesso!")
            return
        else:
            return
    
    except Exception as erro:
        print(f"Erro: {erro}")                     


    finally:
        cursor.close()
        conexao.close()

def excluir_time():

    conexao = conectar()
    cursor = conexao.cursor()

    try:
            
        while True:  
            deletetime = input(f"Deseja excluir seu time: [S] ou [N]: ").upper()
            if deletetime == "S":
                idtime = int(input(f"Digite o ID do seu time: "))

                cursor.execute(
                    """
                        select id_time
                        from times
                        where id_time = %s
                    """,
                    (idtime,)
                )
                if cursor.fetchone() is None:
                    print(f"Time não encontrado")
                    continue
                
                cursor.execute(
                    """
                        delete from times
                        where id_time = %s
                    """,
                    (idtime,)

                )

                conexao.commit()
                print(f"Time excluído com sucesso!")
                return
            else:
                print(f"Operação cancelada")
                return


    finally:
        cursor.close()
        conexao.close()


def menu_time():
    while True:
        print(f"\n=== Menu Time ===")
        print("1 - Cadastrar time")
        print("2 - Listar time")
        print("3 - Editar time")
        print("4 - Excluir time")
        print("0 - Sair")

        opcao = int(input(f"Digite a opção: "))

        if opcao == 1:
            cadastrar_time()

        elif opcao == 2:
            listar_time()

        elif opcao == 3:
            editar_time()

        elif opcao == 4:
            excluir_time()

        elif opcao == 0:
            print("Sessão encerrada!")
            break 
        else:
            print("Opção inválida. Tente novamente")