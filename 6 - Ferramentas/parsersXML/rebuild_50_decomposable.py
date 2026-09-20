#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_50_decomposable.py

Caixas, pacotes, baus e bundles (itens de desmontagem) do Classic 5.0 alinhados com o cliente.

Em 2026-09-18, dos 9.467 itens que o cliente marca como caixa (disassembly_item=1 com conteudo no client_disassembly_item):
  7.204 sem a acao <decompose> no item_templates.xml -> o servidor respondia "You cannot use the item" (STR_ITEM_IS_NOT_USABLE)
    361 com <decompose> mas sem conteudo no decomposable_items.xml -> "nao pode ser desembrulhado"
  1.902 com conteudo, mas so 684 com os mesmos itens do cliente: o resto vinha da 4.x (596 davam itens de outra caixa)
  5.901 sem o casting_delay do cliente (1000/1500 ms, o mesmo tempo do S_USE_ITEM nas capturas oficiais)

Fonte (data/items do cliente):
  client_items.xml                         disassembly_item, disassembly_type (1 = janela de escolha), casting_delay
  client_disassembly_item.xml              caixa -> sets: rate_ (em 1000, sorteio independente), apply_race_/apply_class_/apply_level_, onlyone
  client_disassembly_item_SetList.xml      set -> itens: create_, num_, rate_ (peso; a lista soma 10000)
  client_disassembly_item_Customize.xml    (caixa, set, item) -> custom set com encanto e manastones (client_item_custom_set.xml)

Gerado no decomposable_items.xml (formato <set>, lido pelo DecomposeAction): um <decomposable> por caixa do cliente, com os sets na ordem
do cliente. As entradas antigas de itens que o cliente nao tem como caixa ficam como estao. No item_templates.xml: <decompose /> nas caixas
que nao tinham e o casting_delay do cliente (de 1 a 60000 ms). O resto do arquivo fica byte a byte igual.

Uso:
    python rebuild_50_decomposable.py --verificar
    python rebuild_50_decomposable.py --aplicar
A pasta do cliente (a que contem data/) vem de --cliente ou da variavel AION_CLIENT_XML_DIR.
"""

import argparse
import collections
import hashlib
import html
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402

REL_DEC = "decomposable_items/decomposable_items.xml"
REL_ITEMS = "items/item_templates.xml"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos")
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_decomposable_50.txt")

RACE = {"pc_light": "ELYOS", "pc_dark": "ASMODIANS"}
# Nomes de classe do cliente -> PlayerClass (mesma correspondencia do rebuild_50_item_templates / PlayerClass.getPlayerClassByString)
CLASSE = {"warrior": "WARRIOR", "fighter": "GLADIATOR", "knight": "TEMPLAR", "scout": "SCOUT", "assassin": "ASSASSIN", "ranger": "RANGER",
          "mage": "MAGE", "wizard": "SORCERER", "elementalist": "SPIRIT_MASTER", "cleric": "PRIEST", "priest": "CLERIC", "chanter": "CHANTER",
          "monk": "MONK", "thunderer": "REVENANT", "striker": "STRIKER", "battlemaster": "BRAWLER", "orchestrator": "ORCHESTRATOR",
          "lumines": "LUMINESS", "engineer": "ENGINEER", "gunner": "PHOENIX", "runewarrior": "REAPER", "runeblade": "SOUL_REAPER"}
CAST_MAX = 60000

TEMPLATE_RE = re.compile(r"<item_template\s([^>]*?)(/>|>(.*?)</item_template>)", re.S)
DEC_RE = re.compile(r"[ \t]*<decomposable\s+item_id=\"(\d+)\".*?</decomposable>[ \t]*\r?\n", re.S)


def filhos(e):
    return {c.tag: (c.text or "").strip() for c in e}


def le_cliente(pasta):
    base = os.path.join(pasta, "data", "items")
    cli = {}
    for _, e in ET.iterparse(os.path.join(base, "client_items.xml")):
        if e.tag == "client_item":
            d = {k: v for k, v in filhos(e).items() if k in ("id", "name", "disassembly_item", "disassembly_type", "casting_delay")}
            cli[d["id"]] = d
            e.clear()
    sets = {}
    for e in ET.parse(os.path.join(base, "client_disassembly_item.xml")).getroot():
        d = {k: v for k, v in filhos(e).items() if k != "disassemble_set_list"}
        d["sets"] = [filhos(x) for x in e.find("disassemble_set_list")]
        sets[d["name"].lower()] = d
    listas = {}
    for e in ET.parse(os.path.join(base, "client_disassembly_item_SetList.xml")).getroot():
        listas[e.findtext("name").strip().lower()] = [filhos(x) for x in e.find("disassembly_create_item_list")]
    custom = {}
    for e in ET.parse(os.path.join(base, "client_item_custom_set.xml")).getroot():
        d = filhos(e)
        custom[d["name"].lower()] = d
    personaliza = {}
    for e in ET.parse(os.path.join(base, "client_disassembly_item_Customize.xml")).getroot():
        d = filhos(e)
        personaliza[(d["wrap_name"].lower(), d["disassembly_name"].lower(), d["item_name"].lower())] = d["custom_name"].lower()
    return cli, sets, listas, custom, personaliza


def esc(v):
    return html.escape(str(v), quote=True)


def monta(cli, sets, listas, custom, personaliza, srv_ids, rel):
    """Um bloco <decomposable> por caixa do cliente: {item_id: texto}."""
    nome_id = {d["name"].lower(): i for i, d in cli.items()}
    blocos, usados = {}, set()
    for iid, d in cli.items():
        if d.get("disassembly_item") != "1" or d["name"].lower() not in sets:
            continue
        cx = sets[d["name"].lower()]
        if iid not in srv_ids:
            rel["caixa sem template no servidor"].append(iid)
            continue
        attrs = [("item_id", iid)]
        if d.get("disassembly_type") == "1":
            attrs.append(("selectable", "true"))
        if cx.get("onlyone") == "1":
            attrs.append(("only_one", "true"))
        linhas = ["\t<decomposable " + " ".join(f'{k}="{v}"' for k, v in attrs) + ">", f"\t\t<!-- {esc(d['name'])} -->"]
        for s in cx["sets"]:
            lista = s["set_list_name_"].lower()
            sa = []
            if s.get("rate_", "1000") != "1000":
                sa.append(("rate", s["rate_"]))
            raca = s.get("apply_race_", "").strip().lower()
            if raca:
                sa.append(("race", RACE[raca]))
            classes = s.get("apply_class_", "").split()
            if classes:
                sa.append(("player_classes", " ".join(dict.fromkeys(CLASSE[c.lower()] for c in classes))))
            nivel = s.get("apply_level_", "").strip()
            if nivel:
                a, b = nivel.split("-")
                sa += [("minlevel", a), ("maxlevel", b)]
            itens = []
            for cr in listas[lista]:
                nome = cr["create_"].lower()
                cid = nome_id.get(nome)
                if cid is None or cid not in srv_ids:
                    rel["item de dentro sem template"].append(f"{d['name']} -> {cr['create_']}")
                    continue
                ia = [("id", cid)]
                if cr.get("num_", "1") != "1":
                    ia.append(("count", cr["num_"]))
                if cr.get("rate_", "10000") != "10000":
                    ia.append(("rate", cr["rate_"]))
                cs = personaliza.get((d["name"].lower(), lista, nome))
                if cs:
                    usados.add((d["name"].lower(), lista, nome))
                    c = custom[cs]
                    if c.get("custom_enchant_value", "0") != "0":
                        ia.append(("enchant", c["custom_enchant_value"]))
                    pedras = [nome_id.get(c[k].lower()) for k in sorted(c) if k.startswith("custom_option_slot_")]
                    if None in pedras:
                        rel["manastone do custom set sem item"].append(cs)
                    elif pedras:
                        ia.append(("manastones", " ".join(pedras)))
                itens.append("\t\t\t<item " + " ".join(f'{k}="{v}"' for k, v in ia) + " />")
            if not itens:
                rel["set vazio (ignorado)"].append(f"{d['name']} / {s['set_list_name_']}")
                continue
            linhas.append("\t\t<set" + "".join(f' {k}="{v}"' for k, v in sa) + ">")
            linhas += itens
            linhas.append("\t\t</set>")
        if not any(ln.startswith("\t\t<set") for ln in linhas):
            rel["caixa sem nenhum item valido"].append(iid)
            continue
        linhas.append("\t</decomposable>")
        blocos[iid] = "\n".join(linhas) + "\n"
    sobra = set(personaliza) - usados
    if sobra:
        rel["customize que nao casa com caixa/set/item"] += [" / ".join(k) for k in sorted(sobra)]
    return blocos


def novo_decomposable(texto_antigo, blocos, rel):
    antigos = {m.group(1): m.group(0) for m in DEC_RE.finditer(texto_antigo)}
    mantidos = {i: t for i, t in antigos.items() if i not in blocos}
    rel["entradas antigas mantidas (item que o cliente nao tem como caixa)"] += sorted(mantidos)
    todos = dict(mantidos)
    todos.update(blocos)
    cab = texto_antigo[:texto_antigo.index("<decomposable ")]
    cab = cab[:cab.rindex("\n") + 1] if "\n" in cab else cab
    return cab + "".join(todos[i] for i in sorted(todos, key=int)) + "</decomposable_items>\n", antigos


def edita_templates(texto, cli, caixas, rel, cont):
    nl = "\r\n" if "\r\n" in texto[:4000] else "\n"

    def troca(m):
        head, fecho, inner = m.group(1), m.group(2), m.group(3)
        iid = re.search(r'\bid="(\d+)"', head).group(1)
        if iid not in caixas:
            return m.group(0)
        novo_head = head
        cd = cli[iid].get("casting_delay") or "0"
        if cd.isdigit() and 0 < int(cd) <= CAST_MAX:
            atual = re.search(r'\scasting_delay="(\d+)"', head)
            if not atual:
                novo_head = re.sub(r'(\scName="[^"]*")', lambda x: x.group(1) + f' casting_delay="{cd}"', head, count=1)
                cont["casting_delay acrescentado"] += 1
            elif atual.group(1) != cd:
                novo_head = head.replace(atual.group(0), f' casting_delay="{cd}"', 1)
                cont["casting_delay corrigido"] += 1
        elif cd != "0":
            rel["casting_delay do cliente fora do intervalo (mantido o do servidor)"].append(f"{iid} {cli[iid]['name']} {cd}")
        if fecho == "/>":
            corpo = f"{nl}\t\t<actions>{nl}\t\t\t<decompose />{nl}\t\t</actions>{nl}\t"
            cont["<decompose> acrescentado (template sem filhos)"] += 1
            return "<item_template " + novo_head.rstrip() + ">" + corpo + "</item_template>"
        if "<decompose" not in inner:
            if "<actions>" in inner:
                inner = inner.replace("</actions>", f"\t<decompose />{nl}\t\t</actions>", 1)
                cont["<decompose> acrescentado em <actions>"] += 1
            else:
                bloco = f"\t\t<actions>{nl}\t\t\t<decompose />{nl}\t\t</actions>{nl}"
                fim_mod = inner.find("</modifiers>")
                if fim_mod >= 0:
                    p = inner.index(nl, fim_mod) + len(nl)
                    inner = inner[:p] + bloco + inner[p:]
                else:
                    p = inner.index(nl) + len(nl) if inner.startswith(nl) else 0
                    inner = inner[:p] + bloco + inner[p:]
                cont["<decompose> acrescentado (novo <actions>)"] += 1
        return "<item_template " + novo_head + ">" + inner + "</item_template>"

    return TEMPLATE_RE.sub(troca, texto)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    caminhos = {}
    for rel_path in (REL_DEC, REL_ITEMS):
        src = os.path.join(backup_manager.SERVER_DATA_DIR, rel_path)
        prod = os.path.join(backup_manager.PRODUTO_FINAL_DATA_DIR, rel_path)
        if hashlib.sha256(open(src, "rb").read()).digest() != hashlib.sha256(open(prod, "rb").read()).digest():
            sys.exit(f"{rel_path} do fonte e do Produto Final estao diferentes. Sincronize antes de rodar.")
        caminhos[rel_path] = (src, prod)

    print("1. Lendo o cliente...")
    cli, sets, listas, custom, personaliza = le_cliente(args.cliente)
    print(f"   itens: {len(cli)} | caixas: {len(sets)} | listas: {len(listas)} | customize: {len(personaliza)}")

    print("2. Lendo o servidor...")
    texto_itens = open(caminhos[REL_ITEMS][0], encoding="utf-8", newline="").read()
    texto_dec = open(caminhos[REL_DEC][0], encoding="utf-8", newline="").read()
    srv = {}
    for m in TEMPLATE_RE.finditer(texto_itens):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        srv[a["id"]] = a.get("cName", "").lower()
    trocados = [i for i in srv if i in cli and srv[i] != cli[i]["name"].lower()]
    if trocados:
        print(f"   AVISO: {len(trocados)} templates com cName diferente do cliente (ids trocados); as caixas usam o id do cliente")

    rel = collections.defaultdict(list)
    cont = collections.Counter()
    blocos = monta(cli, sets, listas, custom, personaliza, set(srv), rel)
    novo_dec, antigos = novo_decomposable(texto_dec, blocos, rel)
    caixas = set(blocos)
    tipos = collections.Counter(cli[i].get("disassembly_type") for i in caixas)
    print(f"   caixas geradas: {len(caixas)} (escolha: {tipos['1']}, sorteio/garantidas: {len(caixas) - tipos['1']})"
          f" | antigas: {len(antigos)} | mantidas sem caixa no cliente: {len(rel['entradas antigas mantidas (item que o cliente nao tem como caixa)'])}")
    novo_itens = edita_templates(texto_itens, cli, caixas, rel, cont)
    for k, v in sorted(cont.items()):
        print(f"   {k}: {v}")

    print("3. Validando contra o static_data.xsd agregado...")
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "static_data.xsd")))
    for nome, texto in ((REL_DEC, novo_dec), (REL_ITEMS, novo_itens)):
        doc = etree.fromstring(texto.encode("utf-8"), parser=etree.XMLParser(huge_tree=True))
        if not schema.validate(doc):
            print(f"   {nome}: XSD INVALIDO. Primeiros erros:")
            for e in list(schema.error_log)[:20]:
                print(f"     linha {e.line}: {e.message}")
            sys.exit(1)
        print(f"   {nome}: valido")

    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("rebuild_50_decomposable.py\n\n")
        f.write(f"caixas geradas: {len(caixas)} (escolha: {tipos['1']})\n")
        for k, v in sorted(cont.items()):
            f.write(f"{k}: {v}\n")
        for k, v in rel.items():
            f.write(f"\n== {k}: {len(v)}\n")
            f.writelines(f"  {x}\n" for x in v)
    print(f"   relatorio: {RELATORIO}")

    if not args.aplicar:
        print("\nModo --verificar: nada foi gravado.")
        return

    print("4. Gravando (com backup)...")
    for rel_path, texto in ((REL_DEC, novo_dec), (REL_ITEMS, novo_itens)):
        backup_manager.backup_file_before_modification(rel_path)
        for caminho in caminhos[rel_path]:
            with open(caminho, "w", encoding="utf-8", newline="") as f:
                f.write(texto)
            print(f"   Gravado: {caminho}")


if __name__ == "__main__":
    main()
