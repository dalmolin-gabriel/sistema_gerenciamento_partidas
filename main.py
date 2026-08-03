from usuario import menu_usuario
from arena import menu_arena
from times import menu_time
from partida import menu_partida

def menu_principal():
    while True:
        print("\n=== Menu Principal ===")
        print("1 - Usuário")
        print("2 - Arena")
        print("3 - Time")
        print("4 - Partida")
        print("0 - Sair")

        opcao = int(input(f"Digite a opção: "))

        if opcao == 1:
            menu_usuario()

        elif opcao == 2:
            menu_arena()

        elif opcao == 3:
            menu_time()

        elif opcao == 4:
            menu_partida()

        elif opcao == 0:
            print("Sessão encerrada!")
            break

        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    menu_principal()
        


    

