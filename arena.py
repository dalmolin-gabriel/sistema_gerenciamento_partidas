from conexao import conectar

# cadastrar arena

def cadastrar_arena():
    nome = input(f'Nome da arena: ')
    endereco = input(f'Endereço: ')
    cidade = input(f'Cidade: ')
    telefone = input(f'Telefone: ')
    valor_hora = float(input(f'Valor hora: R$'))
    id_proprietario = int(input(f'ID proprietário: '))

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(
        "insert into arenas (nome, endereco, cidade, telefone, valor_hora, id_proprietario) values(%s,%s,%s,%s,%s,%s)",
        (nome, endereco, cidade, telefone, valor_hora, id_proprietario)
    )
    conexao.commit()
    cursor.close()
    conexao.close()
    print(f"Arena cadastrada com sucesso!")

def listar_arena():

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
            select 
                id_arena,
                nome,
                endereco as endereço,
                cidade,
                telefone,
                valor_hora
            from arenas
            """
        )
        arenas = cursor.fetchall()
        for arena in arenas:
            print(f"ID arena: {arena[0]}")
            print(f"Arena: {arena[1]}")
            print(f"Endereço: {arena[2]}")
            print(f"Cidade: {arena[3]}")
            print(f"Telefone: {arena[4]}")
            print(f"Valor da hora: {arena[5]}")
            print("=" * 40)
            
            
    finally:
        cursor.close()
        conexao.close()

def editar_arena():

    conexao = conectar()
    cursor = conexao.cursor()

    try:
        while True:
            editar = input("Editar arena: [S] ou [N]: ").upper()

            if editar == "N":
                return

            elif editar == "S":

                listar_arena()
            
                while True:
                    # primeiro, verificar se arena existe
                    id_arena = int(input(f"ID da arena: "))

                    cursor.execute(
                        """
                            select id_arena
                            from arenas 
                            where id_arena = %s
                        """,
                        (id_arena,)
                    )

                    if cursor.fetchone():
                        break
                    print("Arena não encontrada. Tente novamente.")

            break

        else:
            print("Opção inválida.")

        while True:
            opcao = int(input(
                "\nEscolha uma opção:\n"
                "1 - Nome\n"
                "2 - Endereço\n"
                "3 - Cidade\n"
                "4 - Telefone\n"
                "5 - Valor hora\n"
                "6 - Sair\n"
                "Opção: "
            ))

            if opcao == 1:
                novo_nome = input(f"Digite o novo nome da arena: ")
                cursor.execute(
                    """
                        update arenas
                        set nome = %s
                        where id_arena = %s

                    """,
                    (novo_nome, id_arena)
                )
            elif opcao == 2:
                novo_endereco = input(f"Digite o novo endereço: ")
                cursor.execute(
                    """
                        update arenas
                        set endereco = %s
                        where id_arena = %s

                    """,
                    (novo_endereco, id_arena)
                )
            elif opcao == 3:
                nova_cidade = input(f"Digite a nova cidade: ")
                cursor.execute(
                    """
                        update arenas
                        set cidade = %s
                        where id_arena = %s

                    """,
                    (nova_cidade, id_arena)
                )
            elif opcao == 4:
                novo_telefone = input(f"Digite o novo contato: ")
                cursor.execute(
                    """
                        update arenas
                        set telefone = %s
                        where id_arena = %s

                    """,
                    (novo_telefone, id_arena)
                )
            elif opcao == 5:
                novo_valor = float(input(f"Digite o novo valor hora: "))
                cursor.execute(
                    """
                        update arenas
                        set valor_hora = %s
                        where id_arena = %s

                    """,
                    (novo_valor, id_arena)
                )
            
            elif opcao == 6:
                return

            else:
                print("Opção inválida. Tente novamente.")
                
                
            conexao.commit()
            print("Arena atualizada com sucesso!")
            
    except Exception as erro:
        print("Erro:", erro)
        conexao.rollback()


    finally:

        cursor.close()
        conexao.close()

def excluir_arena():

    conexao = conectar()
    cursor = conexao.cursor()

    try:

        while True:

            excluir = input("Excluir arena: [S] ou [N]: ").upper()

            if excluir == "N":
                print("Exclusão cancelada.")
                return

            elif excluir == "S":

                listar_arena()

                while True:

                    # Verificar se a arena existe
                    id_arena = int(input("ID da arena: "))

                    cursor.execute("""
                        SELECT id_arena
                        FROM arenas
                        WHERE id_arena = %s
                    """, (id_arena,))

                    if cursor.fetchone() is None:
                        print("Arena não encontrada. Tente novamente.")
                        continue

                    # Verificar se existem partidas nesta arena
                    cursor.execute("""
                        SELECT 1
                        FROM partidas
                        WHERE id_arena = %s
                    """, (id_arena,))

                    if cursor.fetchone():
                        print("Não é possível excluir esta arena, pois existem partidas cadastradas.")
                        return

                    # Arena encontrada e sem partidas
                    break

                break

            else:
                print("Opção inválida.")

        # Excluir a arena
        cursor.execute("""
            DELETE FROM arenas
            WHERE id_arena = %s
        """, (id_arena,))

        conexao.commit()
        print("Arena excluída com sucesso!")

    except Exception as erro:
        print(f"Erro: {erro}")
        conexao.rollback()

    finally:
        cursor.close()
        conexao.close()

def menu_arena():
    while True:
        print(f"\n=== Menu Arena ===")
        print("1 - Cadastrar arena")
        print("2 - Listar arena")
        print("3 - Editar arena")
        print("4 - Excluir arena")
        print("0 - Sair")

        opcao = int(input(f"Digite a opção: "))

        if opcao == 1:
            cadastrar_arena()

        elif opcao == 2:
            listar_arena()

        elif opcao == 3:
            editar_arena()

        elif opcao == 4:
            excluir_arena()

        elif opcao == 0:
            print("Sessão encerrada!")
            break 
        else:
            print("Opção inválida. Tente novamente")