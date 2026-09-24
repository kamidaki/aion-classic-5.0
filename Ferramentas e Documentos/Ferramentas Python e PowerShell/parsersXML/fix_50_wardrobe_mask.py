"""Bits REMODELABLE (1 << 12) e DYEABLE (1 << 15) do mask do item_templates.xml, a partir do client_items 5.0.

O Wardrobe 5.0 só registra e aplica visual em item que troca de visual (cannot_changeskin = 0 no cliente) e só tinge visual que
aceita tinta (can_dye = 1). O mask do servidor vem de uma base antiga e diverge do cliente em cerca de 1% dos equipamentos: o
capacete classic_cash_BlueDragon01_head_01 (125040369) estava sem os dois bits, e na captura oficial de 2026-09-21 15:16 ele
estava no guarda-roupa tingido de c7af27.

Só mexe nesses dois bits, e só em item com equipment_slots no cliente; o resto do mask fica como está. Idempotente; grava no
fonte e no Produto Final, com backup.

Uso: python fix_50_wardrobe_mask.py [--dry]
"""
import collections
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import backup_manager  # noqa: E402

XMLS = os.path.join(backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos", "data")
REL_XML = os.path.join("items", "item_templates.xml")
RELATORIO = os.path.join(AQUI, "relatorio_wardrobe_mask_50.txt")
REMODELABLE = 1 << 12
DYEABLE = 1 << 15
TEMPLATE = re.compile(r'(<item_template id="(\d+)"[^>]*? mask=")(\d+)(")')


def equipamentos_do_cliente():
    """id -> (troca de visual, aceita tinta) de todo item com equipment_slots."""
    out, bloco = {}, {}
    with open(os.path.join(XMLS, "items", "client_items.xml"), encoding="utf-8", errors="replace") as f:
        for linha in f:
            if "<client_item>" in linha:
                bloco = {}
                continue
            m = re.match(r"\s*<([a-z_0-9]+)>(.*?)</\1>", linha)
            if m:
                bloco[m.group(1)] = m.group(2).strip()
            elif "</client_item>" in linha and bloco.get("id") and bloco.get("equipment_slots", "none") != "none":
                out[int(bloco["id"])] = (bloco.get("cannot_changeskin", "0") == "0", bloco.get("can_dye", "0") == "1")
    return out


def main():
    seco = "--dry" in sys.argv
    cliente = equipamentos_do_cliente()
    caminho = os.path.join(backup_manager.SERVER_DATA_DIR, REL_XML)
    raw = open(caminho, encoding="utf-8", newline="").read()
    mudancas = collections.Counter()
    exemplos = collections.defaultdict(list)

    def edita(m):
        iid = int(m.group(2))
        if iid not in cliente:
            return m.group(0)
        remodel, dye = cliente[iid]
        antes = int(m.group(3))
        depois = antes
        depois = depois | REMODELABLE if remodel else depois & ~REMODELABLE
        depois = depois | DYEABLE if dye else depois & ~DYEABLE
        if depois == antes:
            return m.group(0)
        for bit, nome in ((REMODELABLE, "remodelable"), (DYEABLE, "dyeable")):
            if (antes ^ depois) & bit:
                chave = nome + ("+" if depois & bit else "-")
                mudancas[chave] += 1
                exemplos[chave].append(iid)
        return m.group(1) + str(depois) + m.group(4)

    novo = TEMPLATE.sub(edita, raw)
    print("equipamentos no cliente:", len(cliente))
    for chave in sorted(mudancas):
        print("  %-13s %5d  ex.: %s" % (chave, mudancas[chave], " ".join(map(str, exemplos[chave][:5]))))
    if novo == raw:
        print("nada a mudar")  # o relatório da última correção fica como está
        return
    if seco:
        print("--dry: nada gravado")
        return
    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("Bits do mask corrigidos pelo client_items 5.0 (+ ligado, - desligado)\n")
        for chave in sorted(mudancas):
            f.write("%s (%d): %s\n" % (chave, mudancas[chave], " ".join(map(str, exemplos[chave]))))
    print("   relatorio: " + RELATORIO)
    backup_manager.backup_file_before_modification(REL_XML)
    for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
        p = os.path.join(base, REL_XML)
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(novo)
        print("gravado", p)


if __name__ == "__main__":
    main()
