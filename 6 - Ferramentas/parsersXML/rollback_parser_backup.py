r"""
Script Utilitário de Rollback de Backups de Parsers XML 5.0
Localização: D:\AION CLASSIC 5.0 - EMULADOR\6 - Ferramentas\parsersXML\rollback_parser_backup.py

Uso:
  python rollback_parser_backup.py --list              # Lista todos os backups em ordem cronológica
  python rollback_parser_backup.py --latest            # Restaura o backup mais recente imediatamente
  python rollback_parser_backup.py --restore <NOME>    # Restaura um backup específico pelo nome da pasta
"""

import sys
import os

PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
if PARSERS_DIR not in sys.path:
    sys.path.insert(0, PARSERS_DIR)

import backup_manager


def print_help():
    print("=" * 80)
    print(" FERRAMENTA DE ROLLBACK - PARSERS XML 5.0")
    print("=" * 80)
    print("Comandos disponíveis:")
    print("  python rollback_parser_backup.py --list")
    print("      Lista todos os backups disponíveis ordenados por data e hora.")
    print("")
    print("  python rollback_parser_backup.py --latest")
    print("      Restaura imediatamente o último backup gerado.")
    print("")
    print("  python rollback_parser_backup.py --restore <nome_do_backup>")
    print("      Restaura o backup especificado (ex: backup_2026-09-01_09-15-30).")
    print("=" * 80)


def list_backups_cmd():
    backups = backup_manager.list_all_backups()
    print("=" * 80)
    print(" BACKUPS DISPONÍVEIS (ORDEM CRONOLÓGICA)")
    print("=" * 80)
    if not backups:
        print("  Nenhum backup encontrado em tools/parsersXML/backups/")
        print("=" * 80)
        return

    for idx, b in enumerate(backups, 1):
        name = b.get("dir_name", "N/A")
        dt = b.get("created_at_formatted", "N/A")
        trigger = b.get("trigger", "manual")
        files_count = len(b.get("files", []))
        print(f"  [{idx:02d}] {name:32s} | Data: {dt:19s} | Origem: {trigger:15s} | Arquivos: {files_count:3d}")
    print("=" * 80)


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    arg = sys.argv[1].lower()
    if arg in ("--list", "-l"):
        list_backups_cmd()
    elif arg in ("--latest", "-latest"):
        backup_manager.rollback_backup(None)
    elif arg in ("--restore", "-r"):
        if len(sys.argv) < 3:
            print("[ERRO] Especifique o nome do backup para restaurar. Ex:")
            print("   python rollback_parser_backup.py --restore backup_2026-09-01_09-15-30")
            return
        target = sys.argv[2]
        backup_manager.rollback_backup(target)
    else:
        print_help()


if __name__ == "__main__":
    main()
