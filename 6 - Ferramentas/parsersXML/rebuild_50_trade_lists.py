#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_50_trade_lists.py

Reconstroi a cadeia de comercio inteira a partir do cliente 5.0: quem vende (npc_trade_list.xml) e o que cada
lista contem (goodslists/goodslists.xml). Os dois arquivos sao herdados da 4.8 e a NCSoft renumerou as listas e
reaproveitou npc_ids, entao hoje o servidor manda ao cliente ids que significam outra loja -- e valida a compra
contra um conteudo que nao e o que o jogador esta vendo.

Por que os dois no mesmo passo: o id da goodslist e a unica coisa que o SM_TRADELIST manda, e o cliente desenha
a aba com o conteudo que ELE tem para esse id. Corrigir so o npc_trade_list faria a aba certa abrir e a compra
falhar em validateBuyItems; corrigir so o goodslists faria a lista certa ficar pendurada no NPC errado.

Fontes (nomes -> ids, tudo do cliente):
    client_npcs.xml             trade_info/abyss_trade_info/extra_currency_trade_info/coupon_trade_info -> venda
                                trade_in_trade_info -> troca | abyss_trade_buy_info -> compra pelo NPC
    client_npc_goodslist.xml    nome da aba -> id da lista, itens, limites, salestime, guild_level, msgs
    client_npc_trade_in_list.xml / client_npc_purchase_list.xml   idem para troca e compra
    client_items.xml            nome do item -> item id      Strings/  nome da string -> string id

Conversoes medidas (nao inventadas):
    npc_type      trade_info -> NORMAL | abyss_trade_info -> ABYSS | extra_currency_trade_info -> REWARD
                  coupon_trade_info -> NORMAL. Nenhum NPC tem duas tags de venda, entao o tipo e unico.
    sell_price_rate   cliente / 10  (72000->7200, 1500->150, 60000->6000 no que o servidor ja tinha certo)
    buy_price_rate    do cliente, direto (inerte no tradelist_template; no purchase_template e o que o NPC paga)
    salestime         salestime_table_name -> cron, tabela aprendida das listas que hoje ja batem item a item;
                      dois nomes nao tem gabarito limpo e saem no relatorio.

O que fica de fora: func_dialogs no npc_templates.xml. canTradeIn() e canPurchase() exigem o bit de dialogo
(78 e 103) alem do template, e o bit esta tao trocado quanto o resto -- mas mexer nele e canonizar o menu do NPC
inteiro (quest, deposito, teleporte), outro eixo. O relatorio lista quais NPCs ficam nessa pendencia.

Uso (a pasta do cliente e a que contem data/ e Strings/):
    python rebuild_50_trade_lists.py --cliente "<pasta dos XMLs do cliente 5.0>"            (mostra e gera relatorio)
    python rebuild_50_trade_lists.py --cliente "<pasta dos XMLs do cliente 5.0>" --aplicar  (grava com backup)
A pasta tambem pode vir da variavel de ambiente AION_CLIENT_XML_DIR.
"""

import argparse
import collections
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402
from rebuild_50_item_templates import DEFAULT_CLIENT_DIR, load_strings  # noqa: E402

REL_GOODS = os.path.join("goodslists", "goodslists.xml")
REL_TRADE = "npc_trade_list.xml"
# O XmlMerger troca todo <import file="X.xml"> por X_<regiao>.xml quando esse arquivo existe, conforme o
# gameserver.country.code (1 usa, 2 europe, 4 japan, 5 china, 6 taiwan, 7 russia). Gravar so o goodslists.xml
# nao adianta nada num servidor europeu: quem vale e o goodslists_europe.xml. Cada sufixo aqui sai da pasta
# correspondente do cliente; o que o cliente nao tem (purchase_list do europe) cai na pasta base.
REGIOES = (("", os.path.join("npcs")), ("_europe", os.path.join("europe", "Npcs")))
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_trade_lists_50.txt")
XSI = "http://www.w3.org/2001/XMLSchema-instance"

# tag do cliente -> (nome do sub-elemento de cada aba, npc_type do servidor)
VENDA = (("trade_info", "tab", "NORMAL"), ("abyss_trade_info", "atab", "ABYSS"),
         ("extra_currency_trade_info", "etab", "REWARD"), ("coupon_trade_info", "ctab", "NORMAL"))
TROCA = ("trade_in_trade_info", "ttab")
COMPRA = ("abyss_trade_buy_info", "buy_atab")


def blocos(path, tag):
    """Cada <tag>...</tag> de um xml do cliente, como texto -- os arquivos sao grandes e planos."""
    txt = open(path, encoding="utf-8", errors="replace").read()
    return re.findall(r"<" + tag + r">(.*?)</" + tag + r">", txt, re.S)


def campo(bloco, nome):
    m = re.search(r"<" + nome + r">(.*?)</" + nome + r">", bloco, re.S)
    return m.group(1).strip() if m else None


def le_listas(path, tag):
    """id -> nome, itens com limites, salestime, guild_level e as mensagens da loja."""
    out = {}
    for b in blocos(path, tag):
        i = campo(b, "id")
        if not i:
            continue
        itens = []
        for d in re.findall(r"<data>(.*?)</data>", b, re.S):
            n = campo(d, "item")
            if n:
                itens.append((n, campo(d, "sell_limit"), campo(d, "buy_limit")))
        out[int(i)] = {"nome": campo(b, "name") or "", "itens": itens,
                       "salestime": campo(b, "salestime_table_name"), "guild_level": campo(b, "guild_level"),
                       "advertise": campo(b, "advertise_msg"), "gossip": campo(b, "gossip_msg")}
    return out


def le_npcs(path):
    """npc_id -> o que o cliente diz que ele negocia."""
    txt = open(path, encoding="utf-8", errors="replace").read()
    out = {}
    for m in re.finditer(r"<npc_client>(.*?)</npc_client>", txt, re.S):
        b = m.group(1)
        i = campo(b, "id")
        if not i:
            continue
        d = {"nome": campo(b, "name") or "", "save": campo(b, "save_trade_count")}
        for tag, sub in [(t, s) for t, s, _tp in VENDA] + [TROCA, COMPRA]:
            mm = re.search(r"<" + tag + r">(.*?)</" + tag + r">", b, re.S)
            if not mm:
                continue
            d[tag] = {"abas": re.findall(r"<" + sub + r">(.*?)</" + sub + r">", mm.group(1)),
                      "buy": campo(mm.group(1), "buy_price_rate"), "sell": campo(mm.group(1), "sell_price_rate"),
                      "ap": campo(mm.group(1), "ap_buy_price_rate2")}
        if len(d) > 2:
            out[i] = d
    return out


def le_regiao(cdir, sub, item_id):
    """As tres listas de uma regiao do cliente, com os nomes de item ja resolvidos para id."""
    fontes = (("list", "client_npc_goodslist"), ("in_list", "client_npc_trade_in_list"),
              ("purchase_list", "client_npc_purchase_list"))
    out = {}
    for secao, arq in fontes:
        p = os.path.join(cdir, sub, arq + ".xml")
        if not os.path.isfile(p):  # o europe nao tem purchase_list proprio, usa o mesmo do base
            p = os.path.join(cdir, "npcs", arq + ".xml")
        out[secao] = le_listas(p, arq)
        for d in out[secao].values():
            d["ids_por_nome"] = {n.lower(): item_id.get(n.lower()) for n, _s, _b in d["itens"]}
            d["ids"] = [item_id[n.lower()] for n, _s, _b in d["itens"] if item_id.get(n.lower())]
    return out


def le_goodslists_servidor(path):
    """Por secao, id -> itens e salestime atuais: serve de gabarito para aprender o cron."""
    raiz = ET.parse(path).getroot()
    return {secao: {int(el.get("id")): {"itens": [int(i.get("id")) for i in el.findall("item")],
                                        "salestime": el.findtext("salestime")}
                    for el in raiz.findall(secao)}
            for secao in ("list", "in_list", "purchase_list")}


def aprende_salestime(cli, srv):
    """salestime_table_name -> cron. So aprende de lista cujo conteudo hoje ja e identico ao do cliente:
    aprender do arquivo inteiro mistura o cron de listas cujo id mudou de dono e o resultado fica ambiguo."""
    limpo, sujo = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    for i, d in cli.items():
        s = srv.get(i)
        if not d["salestime"] or not s or not s["salestime"]:
            continue
        (limpo if d["ids"] == s["itens"] else sujo)[d["salestime"]][s["salestime"]] += 1
    tab = {k: v.most_common(1)[0][0] for k, v in limpo.items()}
    estimados = {}
    for k, v in sujo.items():
        if k not in tab:
            tab[k] = estimados[k] = v.most_common(1)[0][0]
    return tab, estimados


def secao_goodslists(pai, secao, listas, cron, n2id, sem_item):
    for i in sorted(listas):
        d = listas[i]
        el = ET.SubElement(pai, secao, {"id": str(i)})
        if d["advertise"] and n2id.get(d["advertise"].upper()):
            el.set("advertise", n2id[d["advertise"].upper()])
        if d["gossip"] and n2id.get(d["gossip"].upper()):
            el.set("gossip", n2id[d["gossip"].upper()])
        if d["guild_level"]:
            el.set("legion_lvl", d["guild_level"])
        if d["salestime"] and cron.get(d["salestime"]):
            ET.SubElement(el, "salestime").text = cron[d["salestime"]]
        for nome, sell, buy in d["itens"]:
            iid = d["ids_por_nome"].get(nome.lower())
            if iid is None:
                sem_item.append((secao, i, nome))
                continue
            attrs = {}
            if buy is not None:
                attrs["buy_limit"] = buy
            if sell is not None:
                attrs["sell_limit"] = sell
            attrs["id"] = str(iid)
            ET.SubElement(el, "item", attrs)


def grava(rel, root, aplicar):
    ET.indent(root, space="\t")
    if not aplicar:
        return
    backup_manager.backup_file_before_modification(rel)
    for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
        p = os.path.join(base, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        ET.ElementTree(root).write(p, encoding="utf-8", xml_declaration=True)
        print("Gravado: " + p)


def valida(root, xsd_path):
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(xsd_path))
    if not schema.validate(etree.fromstring(ET.tostring(root, encoding="utf-8"))):
        for e in list(schema.error_log)[:20]:
            print("   XSD linha {}: {}".format(e.line, e.message))
        sys.exit("XSD invalido ({}): nada foi gravado.".format(os.path.basename(xsd_path)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    cdir = os.path.join(args.cliente, "data")
    npcs_xml = os.path.join(cdir, "npcs", "client_npcs.xml")
    if not os.path.isfile(npcs_xml):
        sys.exit("Arquivo do cliente nao encontrado: " + npcs_xml + ". Informe --cliente ou AION_CLIENT_XML_DIR.")

    print("1. Lendo cliente...")
    n2id, _ = load_strings(args.cliente)
    item_id = {}
    for b in blocos(os.path.join(cdir, "items", "client_items.xml"), "client_item"):
        n, i = campo(b, "name"), campo(b, "id")
        if n and i:
            item_id[n.lower()] = int(i)
    regioes = {suf: le_regiao(cdir, sub, item_id) for suf, sub in REGIOES
               if os.path.isdir(os.path.join(cdir, sub))}
    listas = regioes[""]
    cli = le_npcs(npcs_xml)
    nome_id = {secao: {d["nome"].lower(): i for i, d in listas[secao].items()} for secao in listas}
    print("   listas: {} de venda, {} de troca, {} de compra | npcs que negociam: {}".format(
        len(listas["list"]), len(listas["in_list"]), len(listas["purchase_list"]), len(cli)))

    print("2. Aprendendo o cron do salestime do que ja bate...")
    srv_goods = le_goodslists_servidor(os.path.join(backup_manager.SERVER_DATA_DIR, REL_GOODS))
    cron, estimados = aprende_salestime(listas["list"], srv_goods["list"])
    print("   {} nomes de salestime, {} sem gabarito limpo{}".format(
        len(cron), len(estimados), (": " + ", ".join(sorted(estimados))) if estimados else ""))

    print("3. Montando goodslists.xml...")
    sem_item = []
    arvores = {}
    for suf, regiao in regioes.items():
        raiz = ET.Element("goodslists")
        for secao in ("list", "in_list", "purchase_list"):
            secao_goodslists(raiz, secao, regiao[secao], cron, n2id, sem_item)
        valida(raiz, os.path.join(backup_manager.SERVER_DATA_DIR, "goodslists", "goodslists.xsd"))
        arvores[suf] = raiz
        print("   goodslists{}.xml: {} listas".format(suf, len(raiz)))
    goods = arvores[""]
    print("   {} itens que o client_items nao conhece ficaram de fora".format(len(sem_item)))

    print("4. Montando npc_trade_list.xml...")
    trade = ET.Element("npc_trade_list")
    trade.set("xmlns:xsi", XSI)
    trade.set("xsi:noNamespaceSchemaLocation", "npc_trade_list.xsd")
    sem_aba, sem_loja = [], []

    def abas(npc, tag, secao):
        ids = []
        for nome in cli[npc][tag]["abas"]:
            i = nome_id[secao].get(nome.lower())
            if i is None:
                sem_aba.append((npc, tag, nome))
            elif i not in ids:
                ids.append(i)
        return ids

    gerados = collections.Counter()
    for grupo, nome_el, secao in (("venda", "tradelist_template", "list"),
                                  ("troca", "trade_in_list_template", "in_list"),
                                  ("compra", "purchase_template", "purchase_list")):
        for npc in sorted(cli, key=int):
            d = cli[npc]
            if grupo == "venda":
                tag = next((t for t, _s, _tp in VENDA if t in d), None)
                if not tag:
                    continue
                tipo = next(tp for t, _s, tp in VENDA if t == tag)
                attrs = {}
                if d[tag]["buy"]:
                    attrs["buy_price_rate"] = d[tag]["buy"]
                if d[tag]["sell"]:
                    attrs["sell_price_rate"] = str(int(d[tag]["sell"]) // 10)
                if tipo != "NORMAL":
                    attrs["npc_type"] = tipo
                if (d["save"] or "").upper() == "TRUE":
                    attrs["save_count"] = "true"
            else:
                tag = TROCA[0] if grupo == "troca" else COMPRA[0]
                if tag not in d:
                    continue
                attrs = {}
                if grupo == "compra":
                    if d[tag]["ap"]:
                        attrs["buy_price_rate"] = str(int(d[tag]["ap"]) // 10)
                    attrs["npc_type"] = "ABYSS"
            ids = abas(npc, tag, secao)
            if not ids:  # nenhuma aba resolveu: o NPC negocia no cliente e fica sem template nenhum
                sem_loja.append((npc, d["nome"], grupo))
                continue
            el = ET.SubElement(trade, nome_el, dict({"npc_id": npc}, **attrs))
            for i in ids:
                ET.SubElement(el, "tradelist", {"id": str(i)})
            gerados[grupo] += 1
    valida(trade, os.path.join(backup_manager.SERVER_DATA_DIR, "npc_trade_list.xsd"))
    print("   {} de venda, {} de troca, {} de compra | {} abas sem lista correspondente".format(
        gerados["venda"], gerados["troca"], gerados["compra"], len(sem_aba)))

    # o XSD nao amarra os dois arquivos: id pendurado em NPC sem lista do outro lado e a falha que se quer
    # evitar. Vale para cada variante regional, porque o npc_trade_list e um so para todas.
    print("5. Conferindo que todo id apontado existe do outro lado...")
    vazias = collections.Counter()
    for suf, raiz in arvores.items():
        for nome_el, secao in (("tradelist_template", "list"), ("trade_in_list_template", "in_list"),
                               ("purchase_template", "purchase_list")):
            tem = {int(el.get("id")): len(el.findall("item")) for el in raiz.findall(secao)}
            for el in trade.findall(nome_el):
                for t in el:
                    i = int(t.get("id"))
                    if i not in tem:
                        sys.exit("npc {} aponta {} #{}, que nao existe em goodslists{}.xml: nada foi gravado.".format(
                            el.get("npc_id"), secao, i, suf))
                    if not tem[i] and not suf:
                        vazias[secao] += 1
    print("   todos existem nas {} variantes | abas que abrem vazias (a lista do cliente nao tem item): {}".format(
        len(arvores), dict(vazias) or "nenhuma"))

    relatorio(cli, trade, goods, sem_item, sem_aba, sem_loja, estimados, listas, srv_goods)
    for suf, raiz in arvores.items():
        grava(os.path.join("goodslists", "goodslists{}.xml".format(suf)), raiz, args.aplicar)
    grava(REL_TRADE, trade, args.aplicar)
    if not args.aplicar:
        print("Sem --aplicar: nada foi gravado.")


def relatorio(cli, trade, goods, sem_item, sem_aba, sem_loja, estimados, listas, srv_goods):
    """O que mudou e o que sobra. A pendencia de func_dialogs sai com nome e numero: e acionavel."""
    SRVD = backup_manager.SERVER_DATA_DIR
    antigo = ET.parse(os.path.join(SRVD, REL_TRADE)).getroot()
    ant, novo = {}, {}
    for tag in ("tradelist_template", "trade_in_list_template", "purchase_template"):
        ant[tag] = {el.get("npc_id"): [int(t.get("id")) for t in el] for el in antigo.findall(tag)}
        novo[tag] = {el.get("npc_id"): [int(t.get("id")) for t in el] for el in trade.findall(tag)}

    fd, nomes = {}, {}
    txt = open(os.path.join(SRVD, "npcs", "npc_templates.xml"), encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"<npc_template\b([^>]*?)(/>|>(.*?)</npc_template>)", txt, re.S):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        if not a.get("npc_id"):
            continue
        g = re.search(r'func_dialogs="([^"]*)"', m.group(3) or "")
        fd[a["npc_id"]] = {int(x) for x in g.group(1).split()} if g else set()
        nomes[a["npc_id"]] = a.get("name", "")

    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("Cadeia de comercio canonizada pelo cliente 5.0: goodslists.xml (o que cada lista tem) e\n")
        f.write("npc_trade_list.xml (quem vende o que). Os dois vao juntos: o id da lista e a unica coisa que o\n")
        f.write("servidor manda, e o cliente desenha a aba com o conteudo que ele mesmo tem para esse id.\n\n")
        f.write("== npc_trade_list ==\n")
        for tag, rotulo in (("tradelist_template", "venda"), ("trade_in_list_template", "troca"),
                            ("purchase_template", "compra")):
            a, n = ant[tag], novo[tag]
            iguais = sum(1 for i in set(a) & set(n) if a[i] == n[i])
            f.write("{:7}: {} -> {} | criados {} | removidos {} | ids corrigidos {} | ja estavam certos {}\n".format(
                rotulo, len(a), len(n), len(set(n) - set(a)), len(set(a) - set(n)),
                len(set(a) & set(n)) - iguais, iguais))
        f.write("\n== goodslists ==\n")
        for secao in ("list", "in_list", "purchase_list"):
            a = srv_goods[secao]
            n = {int(el.get("id")): [int(i.get("id")) for i in el.findall("item")] for el in goods.findall(secao)}
            iguais = sum(1 for i in set(a) & set(n) if a[i]["itens"] == n[i])
            f.write("{:14}: {} -> {} | criadas {} | removidas {} | conteudo corrigido {} | ja estavam certas {}\n".format(
                secao, len(a), len(n), len(set(n) - set(a)), len(set(a) - set(n)),
                len(set(a) & set(n)) - iguais, iguais))

        f.write("\n== pendencias ==\n")
        if estimados:
            f.write("salestime sem gabarito limpo, cron pela moda do arquivo antigo: {}\n".format(
                ", ".join("{} -> '{}' em {} listas".format(k, v, sum(
                    1 for d in listas["list"].values() if d["salestime"] == k)) for k, v in sorted(estimados.items()))))
        if sem_item:
            f.write("itens que o client_items.xml nao conhece e ficaram de fora ({}): {}\n".format(
                len(sem_item), ", ".join("{} #{} {}".format(s, i, n) for s, i, n in sem_item[:15])))
        if sem_aba:
            f.write("abas que o proprio client_npc_goodslist nao tem ({}): {}\n".format(
                len(sem_aba), ", ".join("{} {}".format(i, n) for i, _t, n in sem_aba)))
        for i, nome, grupo in sem_loja:
            f.write("npc {} ({}) faz {} no cliente e ficou sem template: nenhuma aba dele existe\n".format(i, nome, grupo))

        for tag, codigo, rotulo in (("trade_in_list_template", 78, "TRADE_IN"),
                                    ("purchase_template", 103, "TRADE_SELL_LIST")):
            falta = sorted((i for i in novo[tag] if codigo not in fd.get(i, set())), key=int)
            if not falta:
                continue
            f.write("\n{} npcs com {} novo mas sem o dialogo {} ({}) no func_dialogs do npc_templates.\n".format(
                len(falta), tag, rotulo, codigo))
            f.write("Npc.canTradeIn e Npc.canPurchase exigem os dois, entao o template fica inerte ate o menu do\n")
            f.write("NPC ser canonizado -- outro eixo, que mexe tambem em quest, deposito e teleporte.\n")
            for i in falta:
                f.write("  {:>8}  {}\n".format(i, nomes.get(i) or cli.get(i, {}).get("nome", "")))
    print("   relatorio: " + RELATORIO)


if __name__ == "__main__":
    main()
