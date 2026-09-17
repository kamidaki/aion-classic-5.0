#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_npc_equipamento_cliente.py

Poe no <equipment> do npc_template os itens que o client_npcs.xml manda vestir (<visible_equipments>), para NPC que a
captura nao mostrou -- por exemplo o guarda de torre de um dono que nunca foi visto.

A regra e a do oficial: o S_PUT_NPC manda exatamente os ids dos itens cujo <name> no client_items.xml e o valor de cada
slot do <visible_equipments> (406 de 406 NPCs em 2026-09-13; 350 de 350 em 2026-09-16), e NPC sem visible_equipments
vai sem equipamento (mascara 0, 379 de 379). wing_mesh e wing_always nao sao item e ficam de fora.

So muda template cujo equipamento difere do cliente, e so quando todo item existe no item_templates da arvore (o
NpcEquippedGear pula item que nao existe, e o NPC sairia pelado do mesmo jeito). Cada arvore e gravada separadamente.

Uso:
    python fix_50_npc_equipamento_cliente.py                               (NPCs dos spawns de Tiamaranta Mesa, mostra)
    python fix_50_npc_equipamento_cliente.py --spawn Bases/800040000_Tiamaranta.xml --aplicar
    python fix_50_npc_equipamento_cliente.py --npc 274291-274305 --aplicar
"""

import argparse
import collections
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import backup_manager  # noqa: E402
import fix_50_npc_captura as captura  # noqa: E402

CLIENTE = os.path.join(captura.RAIZ, "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos", "data")
SPAWNS_PADRAO = ("Bases/800040000_Tiamaranta.xml", "Npcs/800040000_Tiamaranta_Mesa.xml")
NAO_ITEM = ("wing_mesh", "wing_always")
BLOCO = re.compile(r'\t?<npc_template npc_id="(\d+)"[ >].*?</npc_template>', re.S)


def visiveis(ids):
    """npcId -> [nomes de item] do <visible_equipments>, na ordem do cliente ([] = sem equipamento)."""
    out, buf, dentro = {}, [], False
    for linha in open(os.path.join(CLIENTE, "npcs", "client_npcs.xml"), encoding="utf-8", errors="replace"):
        if "<npc_client>" in linha:
            buf, dentro = [], True
            continue
        if not dentro:
            continue
        if "</npc_client>" not in linha:
            buf.append(linha)
            continue
        dentro, b = False, "".join(buf)
        m = re.search(r"<id>(\d+)</id>", b)
        if not m or int(m.group(1)) not in ids:
            continue
        ve = re.search(r"<visible_equipments>(.*?)</visible_equipments>", b, re.S)
        out[int(m.group(1))] = [v.strip() for k, v in re.findall(r"<(\w+)>([^<]*)</\1>", ve.group(1)) if k not in NAO_ITEM] if ve else []
    return out


def itens_do_cliente():
    texto = open(os.path.join(CLIENTE, "items", "client_items.xml"), encoding="utf-8", errors="replace").read()
    out = {}
    for m in re.finditer(r"<id>(\d+)</id>\s*<name>([^<]+)</name>", texto):
        out.setdefault(m.group(2).strip().lower(), int(m.group(1)))
    return out


def ids_de(argumentos):
    out = set()
    for a in argumentos:
        if "-" in a:
            i, f = map(int, a.split("-"))
            out.update(range(i, f + 1))
        else:
            out.add(int(a))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--npc", nargs="*", default=[], help="npcIds ou faixas")
    ap.add_argument("--spawn", nargs="*", default=[], help="arquivos de spawn relativos a static_data/spawns")
    ap.add_argument("--aplicar", action="store_true", help="grava as duas arvores (com backup)")
    args = ap.parse_args()
    arquivos = args.spawn or ([] if args.npc else list(SPAWNS_PADRAO))

    for nome, base in captura.ARVORES:
        alvos = ids_de(args.npc)
        for rel in arquivos:
            alvos |= {int(i) for i in re.findall(r'npc_id="(\d+)"', open(os.path.join(base, "spawns", rel), encoding="utf-8").read())}
        cliente = visiveis(alvos)
        por_nome = itens_do_cliente()
        existentes = set()
        for f in glob.glob(os.path.join(glob.escape(base), "items", "*.xml")):
            existentes |= {int(i) for i in re.findall(r'<item_template id="(\d+)"', open(f, encoding="utf-8", errors="replace").read())}
        caminho = os.path.join(base, captura.REL_XML)
        texto = open(caminho, encoding="utf-8", newline="").read()
        pedacos, ultimo, contagem, fora = [], 0, collections.Counter(), []
        for m in BLOCO.finditer(texto):
            n = int(m.group(1))
            if n not in cliente:
                continue
            itens = tuple(por_nome.get(v.lower()) for v in cliente[n])
            if None in itens or any(i not in existentes for i in itens):
                fora.append("%d (%s)" % (n, ", ".join(v for v, i in zip(cliente[n], itens) if i is None or i not in existentes)))
                continue
            medida = dict({c: collections.Counter() for c in captura.CAMPOS}, tipos=set())
            medida["itens"][itens] += 1
            ajustado, mudancas = captura.ajusta(m.group(0), medida, {}, set())
            if not mudancas:
                continue
            pedacos += [texto[ultimo:m.start()], ajustado]
            ultimo = m.end()
            contagem["com equipamento" if itens else "sem equipamento"] += 1
        novo = "".join(pedacos) + texto[ultimo:]
        if novo.count("<npc_template ") != texto.count("<npc_template "):
            sys.exit("ABORTADO: contagem de templates mudou em %s" % caminho)
        print("%s: %d NPCs do cliente, templates corrigidos %s, item faltando %d %s" % (
            nome, len(cliente), dict(contagem), len(fora), fora[:5]))
        if novo != texto:
            from lxml import etree
            xsd = etree.XMLSchema(etree.parse(os.path.join(base, "npcs", "npcs.xsd")))
            if not xsd.validate(etree.fromstring(novo.encode("utf-8"))):
                sys.exit("ABORTADO: %s nao valida no npcs.xsd: %s" % (caminho, xsd.error_log.last_error))
            if args.aplicar:
                backup_manager.backup_file_before_modification(caminho)
                open(caminho, "w", encoding="utf-8", newline="").write(novo)
                print("   gravado")
    if not args.aplicar:
        print("Simulacao: nada gravado. Rode com --aplicar para gravar.")


if __name__ == "__main__":
    main()
