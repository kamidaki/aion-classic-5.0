#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_50_npc_templates_arvores.py

Completa cada npc_templates.xml com os templates que so a outra arvore tem, sem sobrescrever nenhum bloco existente.

As duas arvores nao sao copias: em 2026-09-16 (HEAD 802118f43) a fonte tinha 434 templates que o Produto Final nao
tinha -- 275 deles usados pelo spawn de Tiamaranta Mesa, que por isso nao nascia no servidor -- e o Produto Final tinha
os 55 NPCs de housing (810002-810056) que a fonte tinha perdido. Dos 38.453 em comum, so 1.970 sao iguais, entao
copiar um arquivo por cima do outro apagaria dado dos dois lados. Aqui cada bloco que falta entra na posicao do seu
npc_id, e o que ja existe fica como esta.

Uso:
    python sync_50_npc_templates_arvores.py            (mostra o que entraria em cada arvore)
    python sync_50_npc_templates_arvores.py --aplicar  (grava as duas, com backup e validacao pelo npcs.xsd)
"""

import argparse
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
sys.path.insert(0, AQUI)
import backup_manager  # noqa: E402

ARVORES = (("fonte", os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data")),
           ("produto", os.path.join(RAIZ, "Emulador - Produto Final", "GameServer", "data", "static_data")))
REL_XML = os.path.join("npcs", "npc_templates.xml")
REL_XSD = os.path.join("npcs", "npcs.xsd")
BLOCO = re.compile(r'\t?<npc_template npc_id="(\d+)"[ >].*?</npc_template>', re.S)


def blocos(texto):
    return {int(m.group(1)): m.group(0) for m in BLOCO.finditer(texto)}


def insere(texto, novos):
    """Texto com os blocos de `novos` ({npc_id: bloco}) inseridos antes do primeiro npc_id maior, numa passada."""
    pendentes = sorted(novos)
    saida, ultimo, i = [], 0, 0
    for m in BLOCO.finditer(texto):
        n = int(m.group(1))
        inicio = texto.rfind("\n", 0, m.start()) + 1          # comeco da linha, para o bloco entrar inteiro antes
        while i < len(pendentes) and pendentes[i] < n:
            saida += [texto[ultimo:inicio], "\t" + novos[pendentes[i]].lstrip("\t"), "\n"]
            ultimo = inicio
            i += 1
    fim = texto.rindex("</npc_templates>")
    saida.append(texto[ultimo:fim])
    saida += ["\t" + novos[n].lstrip("\t") + "\n" for n in pendentes[i:]]
    saida.append(texto[fim:])
    return "".join(saida)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true", help="grava as duas arvores (com backup)")
    args = ap.parse_args()

    textos = {nome: open(os.path.join(base, REL_XML), encoding="utf-8", newline="").read() for nome, base in ARVORES}
    todos = {nome: blocos(t) for nome, t in textos.items()}
    for nome, base in ARVORES:
        outra = next(o for o, _ in ARVORES if o != nome)
        faltam = {n: todos[outra][n] for n in set(todos[outra]) - set(todos[nome])}
        print("%s: %d templates, recebe %d da %s" % (nome, len(todos[nome]), len(faltam), outra))
        if faltam:
            print("   ids: %s" % " ".join(map(str, sorted(faltam)[:40])) + (" ..." if len(faltam) > 40 else ""))
        if not faltam:
            continue
        novo = insere(textos[nome], faltam)
        esperado = len(todos[nome]) + len(faltam)
        if len(blocos(novo)) != esperado or novo.count("<npc_template ") != textos[nome].count("<npc_template ") + len(faltam):
            sys.exit("ABORTADO: %s ficaria com %d templates (esperado %d)" % (nome, len(blocos(novo)), esperado))
        from lxml import etree
        xsd = etree.XMLSchema(etree.parse(os.path.join(base, REL_XSD)))
        doc = etree.fromstring(novo.encode("utf-8"), base_url=os.path.join(base, REL_XML))
        if not xsd.validate(doc):
            sys.exit("ABORTADO: %s nao valida no npcs.xsd: %s" % (nome, xsd.error_log.last_error))
        print("   valida no npcs.xsd")
        if args.aplicar:
            caminho = os.path.join(base, REL_XML)
            backup_manager.backup_file_before_modification(caminho)
            open(caminho, "w", encoding="utf-8", newline="").write(novo)
            print("   gravado")
    if not args.aplicar:
        print("Simulacao: nada gravado. Rode com --aplicar para gravar.")


if __name__ == "__main__":
    main()
