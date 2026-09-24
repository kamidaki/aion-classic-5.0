import os
import shutil
from datetime import datetime

# ============================================================
# CONFIGURAÇÃO
# ============================================================

SOURCE_ROOT = r"D:\AION RUST\AionEMU\AionEMU\Cliente\GFAion\aionclassic\levels"

DEST_ROOT = r"D:\AION RUST\AionEMU\AionEMU\Produto Final\data\client\levels"

# ============================================================
# DATA DOS ARQUIVOS QUE DEVEM SER MOVIDOS
# ============================================================

TARGET_DATE = datetime(2026, 8, 25).date()

# ============================================================
# MODO DE OPERAÇÃO
#
# True  = apenas analisa, NÃO move e NÃO cria pastas
# False = MOVE REALMENTE os arquivos
# ============================================================

DRY_RUN = False


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def main():

    print("=" * 90)
    print("AION RUST - MIGRAÇÃO DE ARQUIVOS POR DATA")
    print("=" * 90)

    print(f"ORIGEM : {SOURCE_ROOT}")
    print(f"DESTINO: {DEST_ROOT}")
    print(f"DATA   : {TARGET_DATE.strftime('%d/%m/%Y')}")
    print(f"DRY RUN: {DRY_RUN}")

    print("=" * 90)
    print()

    # --------------------------------------------------------
    # Verificar origem
    # --------------------------------------------------------

    if not os.path.isdir(SOURCE_ROOT):
        print("ERRO: A pasta de origem não existe.")
        print(SOURCE_ROOT)
        input("\nPressione ENTER para sair...")
        return

    # --------------------------------------------------------
    # Contadores
    # --------------------------------------------------------

    total_files = 0
    matched_files = 0
    ignored_files = 0
    moved_files = 0
    existing_files = 0
    errors = 0

    # --------------------------------------------------------
    # Percorrer toda a árvore
    # --------------------------------------------------------

    for current_root, dirs, files in os.walk(SOURCE_ROOT):

        for filename in files:

            total_files += 1

            source_file = os.path.join(
                current_root,
                filename
            )

            # ------------------------------------------------
            # Obter data da última modificação
            # ------------------------------------------------

            try:

                modification_timestamp = os.path.getmtime(
                    source_file
                )

                modification_date = datetime.fromtimestamp(
                    modification_timestamp
                ).date()

            except Exception as e:

                errors += 1

                print()
                print("[ERRO AO LER DATA]")
                print(source_file)
                print(f"Erro: {e}")

                continue

            # ------------------------------------------------
            # Ignorar qualquer data diferente
            # ------------------------------------------------

            if modification_date != TARGET_DATE:

                ignored_files += 1
                continue

            matched_files += 1

            # ------------------------------------------------
            # Descobrir caminho relativo
            # ------------------------------------------------

            relative_path = os.path.relpath(
                source_file,
                SOURCE_ROOT
            )

            # ------------------------------------------------
            # Criar caminho equivalente no destino
            # ------------------------------------------------

            destination_file = os.path.join(
                DEST_ROOT,
                relative_path
            )

            destination_directory = os.path.dirname(
                destination_file
            )

            print(f"[{matched_files}] {relative_path}")

            # ------------------------------------------------
            # MODO SIMULAÇÃO
            # ------------------------------------------------

            if DRY_RUN:

                print("      -> SERIA MOVIDO")

                continue

            # ------------------------------------------------
            # Verificar se já existe
            # ------------------------------------------------

            if os.path.exists(destination_file):

                existing_files += 1

                print("      -> JÁ EXISTE NO DESTINO")
                print("      -> NÃO SOBRESCRITO")

                continue

            # ------------------------------------------------
            # Criar somente agora a pasta necessária
            # ------------------------------------------------

            try:

                os.makedirs(
                    destination_directory,
                    exist_ok=True
                )

            except Exception as e:

                errors += 1

                print("      -> ERRO AO CRIAR PASTA")
                print(f"      -> {e}")

                continue

            # ------------------------------------------------
            # MOVER ARQUIVO
            # ------------------------------------------------

            try:

                shutil.move(
                    source_file,
                    destination_file
                )

                moved_files += 1

                print("      -> MOVIDO")

            except Exception as e:

                errors += 1

                print("      -> ERRO AO MOVER")
                print(f"      -> {e}")

    # ========================================================
    # RESUMO
    # ========================================================

    print()
    print("=" * 90)
    print("RESUMO FINAL")
    print("=" * 90)

    print(f"Total de arquivos analisados : {total_files}")
    print(f"Arquivos de 25/08/2026       : {matched_files}")
    print(f"Arquivos ignorados            : {ignored_files}")
    print(f"Arquivos movidos              : {moved_files}")
    print(f"Já existentes no destino      : {existing_files}")
    print(f"Erros                         : {errors}")

    print("=" * 90)

    if DRY_RUN:

        print()
        print("MODO SIMULAÇÃO.")
        print("Nenhum arquivo foi movido.")
        print("Nenhuma pasta nova foi criada.")

    else:

        print()
        print("MODO REAL.")
        print(f"{moved_files} arquivos foram movidos.")

    print("=" * 90)

    input("\nPressione ENTER para sair...")


# ============================================================
# EXECUTAR
# ============================================================

if __name__ == "__main__":
    main()