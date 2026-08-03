from conexao import conectar

def cadastrar_partida():
    data = input("Digite a data (dd/mm/aaaa): ")
    horario = input("Digite o horário (HH:MM): ")
    status = input("Status: ")
    id_time_mandante = int(input("ID time mandante: "))
    id_time_visitante = int(input("ID time visitante: "))
    id_arena = int(input("ID arena: "))

    conexao = conectar()
    cursor = conexao.cursor()

    try:
    # regra de negócio
        if id_time_mandante == id_time_visitante:
            print(f"Erro: um time não jogar contra ele mesmo.")
            return


        # verifica se o time mandante existe
        cursor.execute(
            """
            SELECT id_time, nome
            FROM times
            WHERE id_time = %s
            """,
            (id_time_mandante,)
        )
        
        if cursor.fetchone() is None:
            print("Time mandante com ID {id_time_mandante} não encontrado")
            return
        
        #verificar se o time visitante existe
        cursor.execute(
            """
            SELECT id_time, nome
            FROM times
            WHERE id_time = %s
            """,
            (id_time_visitante,)
        )

        if cursor.fetchone() is None:
            print(f"Time visitante com ID {id_time_visitante} não encontrado")
            return
        
        #verificar se arena existe
        cursor.execute(
            """
            SELECT id_arena, nome
            FROM arenas
            WHERE id_arena = %s
            """,
            (id_arena,)
        )

        if cursor.fetchone() is None:
            print(f"Arena não encontrada")
            return

        #verificar se a arena já está ocupada
        cursor.execute(
                """
                SELECT id_partida
                FROM partidas
                WHERE data = %s
                AND horario = %s
                AND id_arena = %s
                """,
                (data, horario, id_arena)
            )
        if cursor.fetchone():
            print(f"Já existe uma partida cadastrada nessa arena nesse horário")
            return
        
        #cadastra a partida
        cursor.execute(
            "insert into partidas (data, horario,  status,  id_time_mandante,  id_time_visitante,   id_arena) values (%s, %s, %s, %s, %s, %s)",
            (data, horario, status, id_time_mandante, id_time_visitante, id_arena)
        )
        conexao. commit()
        print("Partida cadastrada com sucesso!")

    finally:
        cursor.close()
        conexao.close()

def listar_partidas():
    conexao = conectar()
    cursor = conexao.cursor()

    # mostrar as partidas cadatradas
    cursor.execute("""
        select 
            p.id_partida,
            tm.nome as time_mandante,
            tv.nome as time_visitante,
            p.data,
            p.horario,
            p.status,
            a.nome as arena
        from partidas p
        join times tm
            on tm.id_time = p.id_time_mandante
        join times tv
            on tv.id_time = p.id_time_visitante
        join arenas a
            on a.id_arena = p.id_arena """
    )

    partidas = cursor.fetchall()
    if not partidas:
        print("Nenhuma partida cadastrada")
        cursor.close()
        conexao.close()
        return False

    for partida in partidas:
        print(f"ID partida: {partida[0]}")
        print(f"Time mandante: {partida[1]}")
        print(f"Time visitante: {partida[2]}")
        print(f"Data: {partida[3]}")
        print(f"Horário: {partida[4]}")
        print(f"Status: {partida[5]}")
        print(f"Arena: {partida[6]}")
        print('-' * 40)
       
    cursor.close()
    conexao.close()
    return True

def editar_partida():

    # Chamar a função listar_partidas()
    listar_partidas()

    # Conexão com o banco
    conexao = conectar()
    cursor = conexao.cursor()

    try:

        # Verificar se o ID existe
        while True:

            id_partida = int(input("ID da partida: "))

            cursor.execute(
                """
                SELECT id_partida
                FROM partidas
                WHERE id_partida = %s
                """,
                (id_partida,)
            )

            if cursor.fetchone() is None:
                print(f"ID {id_partida} da partida não encontrado. Tente novamente.")
                continue

            break

        # Escolher o que deseja alterar
        opcao = int(input(
            "\nEscolha uma opção:\n"
            "1 - Novo horário\n"
            "2 - Nova data\n"
            "3 - Cancelar partida\n"
            "Opção: "
        ))

        # Alterar horário
        if opcao == 1:

            novo_horario = input("Novo horário: ")

            cursor.execute(
                """
                UPDATE partidas
                SET horario = %s
                WHERE id_partida = %s
                """,
                (novo_horario, id_partida)
            )

        # Alterar data
        elif opcao == 2:

            nova_data = input("Nova data: ")

            cursor.execute(
                """
                UPDATE partidas
                SET data = %s
                WHERE id_partida = %s
                """,
                (nova_data, id_partida)
            )

        # Cancelar partida
        elif opcao == 3:

            cursor.execute(
                """
                UPDATE partidas
                SET status = %s
                WHERE id_partida = %s
                """,
                ("Cancelada", id_partida)
            )


            respota = input("Deseja excluir está partida: [S] ou [N]: ").upper()

            if respota == "S":
            
                cursor.execute(
                """
                    delete from partidas
                    where id_partida = %s
                
                """,
                (id_partida,)
            )
            
                conexao.commit()
                print("Partida excluída com sucesso!")
                return

            else:
                print("Registrado no histórico")
            
        else:
            print("Opção inválida.")
            return
        
        conexao.commit()
        print("Partida atualizada com sucesso!")

    except Exception as erro:
        print(f"Erro: {erro}")

    finally:
        cursor.close()
        conexao.close()

def excluir_partida():

    conexao = conectar()
    cursor = conexao.cursor()


    try:
        while True:
            deletar = input(f"Excluir partida [S] ou [N]: ").upper()
            if deletar == "N":
                print("Cancelamento encerrado.")
                return

            elif deletar == "S":
                if not listar_partidas():
                    return

                id_partida = int(input(f"ID partida: "))
                        
                cursor.execute("""
                        select 
                            id_partida
                        from partidas
                        where id_partida = %s
                    """,
                (id_partida,)
                )
                if cursor.fetchone() is None:
                    print(f"Partida {id_partida} não encontrada. Tente Novamente.")
                    continue
                cursor.execute(
                        """
                            delete
                            from partidas
                            where id_partida = %s
                        """,
                        (id_partida,)
                    )
                conexao.commit()
                print(f"Partida excluída com sucesso!")
                return
            else:
                print("Opção inválida. Tente novamente.")
                
    finally:
        cursor.close()
        conexao.close()

def menu_partida():
    while True:
        print(f"\n=== Menu Usuário ===")
        print("1 - Cadastrar partida")
        print("2 - Listar partida")
        print("3 - Editar partida")
        print("4 - Excluir partida")
        print("0 - Sair")

        opcao = int(input(f"Digite a opção: "))

        if opcao == 1:
            cadastrar_partida()

        elif opcao == 2:
            listar_partidas()

        elif opcao == 3:
            editar_partida()

        elif opcao == 4:
            excluir_partida()

        elif opcao == 0:
            print("Sessão encerrada!")
            break 
        else:
            print("Opção inválida. Tente novamente")