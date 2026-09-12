#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_50_npc_dialogs.py

Conserta o func_dialogs do talk_info: o menu de funcoes do NPC. Ele e herdado da 4.8 e, com os ids reaproveitados
pela NCSoft, esta pendurado no NPC errado -- 849 npcs oferecem "comprar" sem ter loja nenhuma e 345 que viraram
lojistas na 5.0 nao oferecem nada.

Nao e cosmetico: CM_DIALOG_SELECT recusa a acao e loga tentativa de abuso quando o codigo nao esta no func_dialogs
do NPC (o conjunto de "dialogos de funcao" e a uniao do que todos os templates declaram). Sem o bit 2, o
tradelist_template canonizado nao abre loja nenhuma; sem o 78 e o 103, Npc.canTradeIn e canPurchase sao falsos.

Como se sabe o que cada NPC faz: o proprio client_npcs.xml tem um campo por funcao (recovery, remove_item_option,
airlines_name, func_itemcharge, ...). As regras abaixo foram medidas contra o gabarito -- os npcs cujo id NAO
mudou de dono na 5.0, listados por exclusao no relatorio do rebuild_50_npc_templates -- e reproduzem 99,1% do
func_dialogs que o servidor ja tem hoje nesse gabarito. E so dai que elas saem; nada e suposto pelo nome.

Codigos governados (o cliente decide, tanto para por quanto para tirar):
      2 BUY / 78 TRADE_IN / 103 TRADE_SELL_LIST   tem o template correspondente no npc_trade_list.xml
      3 SELL                                      trade_info (loja de kinah; coin_merchant so compra)
    4+125 estigma                                 npc_function_type Stigma_master, ou o titulo Stigma_Master
     26 deposito pessoal                          extendcharwarehouse_start
     53 deposito da legiao                        npc_function_type warehouse sem o campo acima
     35 recuperacao        41 dar item            recovery / give_item_proc
     42 tirar manastone    43 trocar aparencia     remove_item_option / change_item_skin
     44 voo                                      airlines_name
     45 subir coleta / 46 subir oficio            gather_skill_levelup, pelo valor (gathering vs armorsmith...)
  58+79+80 tarefas e desistir de oficio           func_giveup_craftskill
     47 expandir inventario                       extendinventory_start
     61 mudar visual       62 mudar genero        edit_character_all / edit_character_gender
     63 casamenteiro       66+67 fusao de armas   match_maker / compound_weapon
    71+72 pets            75+76 recarga de item   func_pet_manage / func_itemcharge

Fora do alcance do cliente e por isso preservados como estao: 5, 6, 7, 50, 52 (legiao), 33, 36, 37, 59, 65, 68,
69, 94, 95, 107. Para esses o client_npcs nao tem campo que separe quem tem de quem nao tem -- medido, nao
chutado: a melhor condicao que achei erra em mais da metade dos casos do gabarito.

Uso (a pasta do cliente e a que contem data/ e Strings/):
    python rebuild_50_npc_dialogs.py --cliente "<pasta dos XMLs do cliente 5.0>"            (mostra e gera relatorio)
    python rebuild_50_npc_dialogs.py --cliente "<pasta dos XMLs do cliente 5.0>" --aplicar  (grava com backup)
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
from rebuild_50_item_templates import DEFAULT_CLIENT_DIR  # noqa: E402

REL_XML = os.path.join("npcs", "npc_templates.xml")
REL_XSD = os.path.join("npcs", "npcs.xsd")
REL_TRADE = "npc_trade_list.xml"
RELATORIO_TEMPLATES = os.path.join(PARSERS_DIR, "relatorio_npc_templates_50.txt")
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_npc_dialogs_50.txt")
BLOCK_RE = re.compile(r"\t<npc_template\b([^>]*?)(/>|>(.*?)</npc_template>)", re.S)
TALK_RE = re.compile(r"([ \t]*)<talk_info\b([^>]*)/>[ \t]*\n?")

# campo do cliente -> codigos que ele liga. So entra aqui o que o gabarito confirma (ver docstring).
CAMPO_CODIGOS = {
    "recovery": (35,), "give_item_proc": (41,), "remove_item_option": (42,), "change_item_skin": (43,),
    "airlines_name": (44,), "extendinventory_start": (47,), "edit_character_all": (61,),
    "edit_character_gender": (62,), "match_maker": (63,), "func_giveup_craftskill": (58, 79, 80),
    "compound_weapon": (66, 67), "func_pet_manage": (71, 72), "func_itemcharge": (75, 76),
}
# gather_skill_levelup serve as duas escolas e o valor diz qual: coleta sobe com 45, oficio com 46
COLETA = ("gathering", "aerial_gathering")
GOVERNADOS = {2, 3, 4, 26, 45, 46, 53, 125, 78, 103} | {c for cs in CAMPO_CODIGOS.values() for c in cs}
WAREHOUSE = ("warehouse",)  # npc_function_type, comparado em minusculas


def le_cliente(path):
    """npc_id -> campos presentes, npc_function_type, titulo e talking_distance."""
    txt = open(path, encoding="utf-8", errors="replace").read()
    out = {}
    for m in re.finditer(r"<npc_client>(.*?)</npc_client>", txt, re.S):
        b = m.group(1)
        i = re.search(r"<id>(\d+)</id>", b)
        if not i:
            continue

        def campo(nome):
            v = re.search(r"<" + nome + r">(.*?)</" + nome + r">", b)
            return v.group(1).strip() if v else ""

        out[i.group(1)] = {"campos": set(re.findall(r"<([a-z_0-9]+)>", b)), "ft": campo("npc_function_type").lower(),
                           "titulo": campo("npc_title").lower(), "distancia": campo("talking_distance"),
                           "escola": campo("gather_skill_levelup").lower()}
    return out


def ids_trocados(path):
    """Os npcs cujo id mudou de dono na 5.0, do relatorio do rebuild_50_npc_templates: o resto e o gabarito."""
    if not os.path.isfile(path):
        return set()
    return {m.group(1) for l in open(path, encoding="utf-8") if (m := re.match(r"\s*(\d+)\s+(SIM|-)\s", l))}


def le_servidor(path):
    text = open(path, encoding="utf-8").read()
    srv = {}
    for m in BLOCK_RE.finditer(text):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        if not a.get("npc_id"):
            continue
        inner = m.group(3) or ""
        talk = TALK_RE.search(inner)
        fd = re.search(r'func_dialogs="([^"]*)"', talk.group(2)) if talk else None
        srv[a["npc_id"]] = {"span": m.span(3) if m.group(3) is not None else None, "inner": inner,
                            "talk": talk, "codigos": {int(x) for x in fd.group(1).split()} if fd else set()}
    return text, srv


def le_trade(path):
    raiz = ET.parse(path).getroot()
    return {codigo: {el.get("npc_id") for el in raiz.findall(tag)}
            for tag, codigo in (("tradelist_template", 2), ("trade_in_list_template", 78), ("purchase_template", 103))}


def codigos_do_cliente(npc, d, trade):
    """O que o cliente prova que esse NPC faz."""
    out = set()
    for codigo, ids in trade.items():
        if npc in ids:
            out.add(codigo)
    if "trade_info" in d["campos"]:
        out.add(3)
    if d["ft"] == "stigma_master" or "stigma_master" in d["titulo"]:
        out |= {4, 125}
    if "extendcharwarehouse_start" in d["campos"]:
        out.add(26)
    elif d["ft"] in WAREHOUSE:
        out.add(53)
    if d["escola"]:
        out.add(45 if d["escola"].startswith(COLETA) else 46)
    for campo, codigos in CAMPO_CODIGOS.items():
        if campo in d["campos"]:
            out.update(codigos)
    return out


def render_talk(talk, codigos):
    """Troca so o func_dialogs do talk_info que ja existe; quem passa a ter funcao ganha is_dialog junto."""
    attrs = talk.group(2)
    valor = " ".join(str(c) for c in sorted(codigos))
    if re.search(r'func_dialogs="[^"]*"', attrs):
        attrs = re.sub(r'\s*func_dialogs="[^"]*"', (' func_dialogs="' + valor + '"') if codigos else "", attrs)
    elif codigos:
        alvo = re.search(r'\s(subdialog_type|can_talk_invisible)=', attrs)
        pos = alvo.start() if alvo else len(attrs.rstrip())
        attrs = attrs[:pos] + ' func_dialogs="' + valor + '"' + attrs[pos:]
    if codigos and 'is_dialog="true"' not in attrs:  # sem isso o cliente nao abre a janela de dialogo
        attrs = re.sub(r'\s*is_dialog="[^"]*"', "", attrs)
        alvo = re.search(r'\sfunc_dialogs=', attrs)
        attrs = attrs[:alvo.start()] + ' is_dialog="true"' + attrs[alvo.start():]
    return talk.group(1) + "<talk_info" + attrs + "/>\n"


def novo_inner(s, codigos, distancia):
    inner = s["inner"]
    if s["talk"]:
        t = s["talk"]
        return inner[:t.start()] + render_talk(t, codigos) + inner[t.end():]
    if not codigos:
        return inner
    # nao tinha talk_info: sem ele NpcTemplate.canInteract() e falso e o NPC nao conversa. O xsd exige que ele
    # venha depois de bound_radius e antes de massive_loot.
    # talking_distance do cliente; o servidor nunca escreveu 0 e o alcance de conversa e distancia+1, entao
    # cliente sem valor (ou com 0) cai no 5, que e o que 7449 dos talk_info ja usam
    dist = int(float(distancia)) if distancia else 0
    dist = str(dist if dist > 0 else 5)
    novo = '\t\t<talk_info distance="{}" is_dialog="true" func_dialogs="{}" can_talk_invisible="false" />\n'.format(
        dist, " ".join(str(c) for c in sorted(codigos)))
    ml = re.search(r"[ \t]*<massive_loot\b", inner)
    if ml:
        return inner[:ml.start()] + novo + inner[ml.start():]
    return inner.rstrip("\t") + novo + "\t"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    npcs_xml = os.path.join(args.cliente, "data", "npcs", "client_npcs.xml")
    if not os.path.isfile(npcs_xml):
        sys.exit("Arquivo do cliente nao encontrado: " + npcs_xml + ". Informe --cliente ou AION_CLIENT_XML_DIR.")

    print("1. Lendo cliente, npc_trade_list e npc_templates...")
    cli = le_cliente(npcs_xml)
    trade = le_trade(os.path.join(backup_manager.SERVER_DATA_DIR, REL_TRADE))
    text, srv = le_servidor(os.path.join(backup_manager.SERVER_DATA_DIR, REL_XML))
    trocados = ids_trocados(RELATORIO_TEMPLATES)
    gabarito = [i for i in srv if i in cli and i not in trocados]
    print("   cliente: {} | servidor: {} | gabarito (id nao trocado): {}".format(len(cli), len(srv), len(gabarito)))

    print("2. Conferindo as regras contra o gabarito...")
    ok = sum(1 for i in gabarito if (srv[i]["codigos"] & GOVERNADOS) == codigos_do_cliente(i, cli[i], trade))
    print("   {} de {} batem sem mudar nada ({:.1f}%)".format(ok, len(gabarito), 100 * ok / max(len(gabarito), 1)))

    print("3. Reescrevendo o func_dialogs...")
    edits, posto, tirado, linhas = [], collections.Counter(), collections.Counter(), []
    novos_talk = 0
    for npc in sorted(srv, key=int):
        if npc not in cli:  # o cliente 5.0 nao conhece esse npc: nao ha o que provar, fica como esta
            continue
        s, d = srv[npc], cli[npc]
        atual = s["codigos"]
        codigos = codigos_do_cliente(npc, d, trade) | (atual - GOVERNADOS)
        if codigos == atual:
            continue
        if not s["talk"] and codigos:
            novos_talk += 1
        for c in codigos - atual:
            posto[c] += 1
        for c in atual - codigos:
            tirado[c] += 1
        inner = novo_inner(s, codigos, d["distancia"])
        if s["span"]:
            edits.append((s["span"][0], s["span"][1], inner))
        linhas.append((npc, npc in trocados, sorted(atual), sorted(codigos)))
    print("   {} npcs mudam | {} ganham talk_info novo".format(len(linhas), novos_talk))
    print("   posto : {}".format(dict(posto.most_common())))
    print("   tirado: {}".format(dict(tirado.most_common())))

    out, pos = [], 0
    for a, b, novo in sorted(edits):
        out.append(text[pos:a])
        out.append(novo)
        pos = b
    out.append(text[pos:])
    novo_texto = "".join(out)

    # o ponto de tudo: sem o bit, CM_DIALOG_SELECT barra a acao e o template de comercio nao serve para nada
    print("4. Conferindo que todo template de comercio ficou com o bit que o destrava...")
    final = {}
    for m in BLOCK_RE.finditer(novo_texto):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        if not a.get("npc_id"):
            continue
        fd = re.search(r'func_dialogs="([^"]*)"', m.group(3) or "")
        final[a["npc_id"]] = {int(x) for x in fd.group(1).split()} if fd else set()
    sem_template = sorted({i for ids in trade.values() for i in ids if i not in final}, key=int)
    faltando = {c: sorted((i for i in ids if i in final and c not in final[i]), key=int) for c, ids in trade.items()}
    for c, ids in sorted(faltando.items()):
        if ids:
            sys.exit("codigo {} ficou faltando em {} npcs ({}): nada foi gravado.".format(c, len(ids), ids[:10]))
    print("   todos destravados. {} npcs que negociam na 5.0 nao tem npc_template no servidor (ficam no relatorio).".format(
        len(sem_template)))

    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, REL_XSD)))
    if not schema.validate(etree.fromstring(novo_texto.encode("utf-8"))):
        for e in list(schema.error_log)[:20]:
            print("   XSD linha {}: {}".format(e.line, e.message))
        sys.exit("XSD invalido: nada foi gravado.")
    print("   XSD valido.")

    if linhas:
        relatorio(linhas, posto, tirado, novos_talk, ok, len(gabarito), novo_texto, sem_template, cli)
    else:  # rodar de novo depois de aplicar nao acha mais nada: nao apagar o relatorio bom
        print("   nada a mudar; relatorio anterior mantido.")

    if not args.aplicar:
        print("Sem --aplicar: nada foi gravado.")
        return
    backup_manager.backup_file_before_modification(REL_XML)
    for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
        p = os.path.join(base, REL_XML)
        with open(p, "wb") as f:
            f.write(novo_texto.encode("utf-8"))
        print("Gravado: " + p)


def relatorio(linhas, posto, tirado, novos_talk, ok, total_gab, novo_texto, sem_template, cli):
    from collections import Counter
    nomes = {}
    for m in BLOCK_RE.finditer(novo_texto):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        if a.get("npc_id"):
            nomes[a["npc_id"]] = a.get("name", "")
    # um codigo que some do arquivo inteiro deixa de ser "dialogo de funcao" e passa a nao ser mais barrado
    restantes = Counter()
    for v in re.findall(r'func_dialogs="([^"]*)"', novo_texto):
        restantes.update(int(x) for x in v.split())
    sumiram = sorted(c for c in tirado if not restantes[c])

    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("func_dialogs canonizado pelo cliente 5.0. As regras reproduzem {} de {} ({:.1f}%) do gabarito\n".format(
            ok, total_gab, 100 * ok / max(total_gab, 1)))
        f.write("-- os npcs cujo id nao mudou de dono --, que e de onde elas saem.\n\n")
        f.write("{} npcs mudam, {} deles ganham um talk_info que nao existia.\n\n".format(len(linhas), novos_talk))
        f.write("{:>6}  {:>5}  {:>5}  codigo\n".format("posto", "tirado", "saldo"))
        for c in sorted(set(posto) | set(tirado)):
            f.write("{:>6}  {:>5}  {:>+5}  {}\n".format(posto[c], tirado[c], posto[c] - tirado[c], c))
        if sumiram:
            f.write("\nATENCAO: os codigos {} sumiram de todos os templates. Um codigo que nao aparece em npc\n".format(sumiram))
            f.write("nenhum deixa de ser dialogo de funcao e para de ser barrado pelo CM_DIALOG_SELECT.\n")

        # o npc_teleporter.xml e 4.8 como o resto e nao entra neste passo: vale saber quantos ficaram orfaos
        tele = set()
        for m in re.finditer(r'npc_ids="([^"]*)"',
                             open(os.path.join(backup_manager.SERVER_DATA_DIR, "npc_teleporter.xml"),
                                  encoding="utf-8", errors="replace").read()):
            tele.update(m.group(1).split())
        perderam_voo = sorted((npc for npc, _t, antes, depois in linhas
                               if 44 in antes and 44 not in depois and npc in tele), key=int)
        if perderam_voo:
            f.write("\n{} npcs perderam o voo (44) e continuam no npc_teleporter.xml, que ainda e 4.8:\n".format(
                len(perderam_voo)))
            f.write("a rota deles fica pendurada em NPC que nao voa mais. {}\n".format(" ".join(perderam_voo)))

        if sem_template:
            f.write("\n{} npcs negociam no cliente 5.0 e nao tem npc_template no servidor, entao o template de\n".format(
                len(sem_template)))
            f.write("comercio deles fica sem dono. Criar o NPC precisa de level e maxHp, que o cliente nao tem\n")
            f.write("(mesmo motivo do rebuild_50_npc_templates): e tarefa a parte.\n")
            for i in sem_template:
                f.write("  {:>8}  {}\n".format(i, cli.get(i, {}).get("titulo", "")))

        trocados = [r for r in linhas if r[1]]
        f.write("\n{} das mudancas sao em npc cujo id mudou de dono na 5.0 (o menu era do NPC antigo);\n".format(len(trocados)))
        f.write("{} sao em npc de identidade preservada, que e onde vale olhar duas vezes:\n\n".format(len(linhas) - len(trocados)))
        f.write("{:>8}  {:24}  {:22}  {}\n".format("npc_id", "nome", "antes", "depois"))
        for npc, troc, antes, depois in linhas:
            if troc:
                continue
            f.write("{:>8}  {:24}  {:22}  {}\n".format(npc, nomes.get(npc, "")[:24],
                                                       " ".join(map(str, antes)) or "-",
                                                       " ".join(map(str, depois)) or "-"))
    print("   relatorio: " + RELATORIO)


if __name__ == "__main__":
    main()
