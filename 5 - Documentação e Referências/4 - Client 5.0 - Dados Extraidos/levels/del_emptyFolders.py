import os
from datetime import datetime

# ============================================================
# CONFIGURAÇÃO
# ============================================================

SOURCE_ROOT = r"D:\AION RUST\AionEMU\AionEMU\Cliente\GFAion\aionclassic\levels"

# Somente pastas cuja última modificação seja esta data
TARGET_DATE = datetime(2026, 8, 25).date()

# ============================================================
# MODO DE OPERAÇÃO
#
# True  = apenas mostra o que seria excluído
# False = EXCLUI REALMENTE as pastas
# ============================================================

DRY_RUN = False


# ============================================================
# FUNÇÃO PARA OBTER DATA DA PASTA
# ============================================================

def get_modified_date(path):
    timestamp = os.path.getmtime(path)
    return datetime.fromtimestamp(timestamp).date()


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def main():

    print("=" * 90)
    print("AION RUST - LIMPEZA DE PASTAS VAZIAS")
    print("=" * 90)

    print(f"ORIGEM     : {SOURCE_ROOT}")
    print(f"DATA ALVO  : {TARGET_DATE.strftime('%d/%m/%Y')}")
    print(f"DRY RUN    : {DRY_RUN}")

    print("=" * 90)
    print()

    if not os.path.isdir(SOURCE_ROOT):

        print("ERRO: A pasta de origem não existe.")
        print(SOURCE_ROOT)

        input("\nPressione ENTER para sair...")
        return

    # --------------------------------------------------------
    # Contadores
    # --------------------------------------------------------

    total_directories = 0
    target_date_directories = 0
    empty_directories = 0
    deleted_directories = 0
    skipped_non_empty = 0
    skipped_other_date = 0
    errors = 0

    # --------------------------------------------------------
    # os.walk com topdown=False
    #
    # Isso é importante:
    #
    # Primeiro processa:
    #
    # levels\a\b\c
    #
    # depois:
    #
    # levels\a\b
    #
    # depois:
    #
    # levels\a
    #
    # Assim podemos remover estruturas que ficaram
    # completamente vazias depois da movimentação.
    # --------------------------------------------------------

    for current_root, dirs, files in os.walk(
        SOURCE_ROOT,
        topdown=False
    ):

        for dirname in dirs:

            total_directories += 1

            directory_path = os.path.join(
                current_root,
                dirname
            )

            # ------------------------------------------------
            # Verificar data da pasta
            # ------------------------------------------------

            try:

                modified_date = get_modified_date(
                    directory_path
                )

            except Exception as e:

                errors += 1

                print()
                print("[ERRO AO LER DATA]")
                print(directory_path)
                print(f"Erro: {e}")

                continue

            # ------------------------------------------------
            # Ignorar pastas com data diferente
            # ------------------------------------------------

            if modified_date != TARGET_DATE:

                skipped_other_date += 1
                continue

            target_date_directories += 1

            # ------------------------------------------------
            # Verificar se está realmente vazia
            # ------------------------------------------------

            try:

                contents = os.listdir(
                    directory_path
                )

            except Exception as e:

                errors += 1

                print()
                print("[ERRO AO LER PASTA]")
                print(directory_path)
                print(f"Erro: {e}")

                continue

            # ------------------------------------------------
            # Pasta ainda possui conteúdo
            # ------------------------------------------------

            if len(contents) > 0:

                skipped_non_empty += 1

                print(
                    f"[MANTIDA - POSSUI CONTEÚDO] "
                    f"{directory_path}"
                )

                continue

            # ------------------------------------------------
            # Pasta vazia encontrada
            # ------------------------------------------------

            empty_directories += 1

            print()
            print("[PASTA VAZIA ENCONTRADA]")
            print(f"  Pasta : {directory_path}")
            print(
                f"  Data  : "
                f"{modified_date.strftime('%d/%m/%Y')}"
            )

            # ------------------------------------------------
            # SIMULAÇÃO
            # ------------------------------------------------

            if DRY_RUN:

                print("  Ação  : SERIA EXCLUÍDA")
                continue

            # ------------------------------------------------
            # EXCLUSÃO REAL
            # ------------------------------------------------

            try:

                os.rmdir(
                    directory_path
                )

                deleted_directories += 1

                print("  Ação  : EXCLUÍDA")

            except Exception as e:

                errors += 1

                print("  Ação  : ERRO AO EXCLUIR")
                print(f"  Erro  : {e}")

    # ========================================================
    # RESUMO
    # ========================================================

    print()
    print("=" * 90)
    print("RESUMO FINAL")
    print("=" * 90)

    print(
        f"Total de pastas analisadas    : "
        f"{total_directories}"
    )

    print(
        f"Pastas com data 25/08/2026    : "
        f"{target_date_directories}"
    )

    print(
        f"Pastas vazias encontradas     : "
        f"{empty_directories}"
    )

    print(
        f"Pastas excluídas              : "
        f"{deleted_directories}"
    )

    print(
        f"Pastas mantidas (com conteúdo): "
        f"{skipped_non_empty}"
    )

    print(
        f"Pastas ignoradas (outra data) : "
        f"{skipped_other_date}"
    )

    print(
        f"Erros                         : "
        f"{errors}"
    )

    print("=" * 90)

    if DRY_RUN:

        print()
        print("MODO SIMULAÇÃO.")
        print("Nenhuma pasta foi excluída.")
        print()
        print("Para executar a limpeza real:")
        print()
        print("    DRY_RUN = False")

    else:

        print()
        print("LIMPEZA REAL CONCLUÍDA.")
        print(
            f"{deleted_directories} "
            f"pastas vazias foram excluídas."
        )

    print("=" * 90)

    input("\nPressione ENTER para sair...")


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()