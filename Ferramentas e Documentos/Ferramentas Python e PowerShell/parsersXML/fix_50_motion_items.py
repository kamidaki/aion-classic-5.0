"""Ações <animation> (motions) e <learnemotion> (emotions) dos itens do item_templates.xml alinhadas com o client_items 5.0.

Em 2026-09-29, todos com template no servidor:
  210 itens com custom_<slot>_anim, só 11 com <animation> (ninja e hovering); os outros 199 eram templates vazios, o item era gasto
      sem dar a motion, e por isso só ninja e hovering apareciam
  198 itens com cash_social, só 72 com <learnemotion> (as danças 64-...); os outros 126 também não ensinavam nada

Mapeamento:
  AnimationAddAction: custom_idle_anim/run/jump/rest/shop_anim -> idle/run/jump/rest/shop = id do animations/custom_animation.xml
                      pelo name; anim_expire_time (minutos) -> minutes (sem o campo, a motion é permanente). O slot do campo tem de
                      bater com o type do custom_animation.xml; se não bater, o item fica sem a ação e é listado.
  EmotionLearnAction: cash_social -> emotionid, cash_available_minute -> minutes (como no titleadd; o 169600009 de teste tem 5 e 5).

O script, idempotente: 1. cria a ação que falta (e o <actions>, no lugar do XSD), 2. corrige a que diverge.
Grava no fonte e no Produto Final (precisam estar iguais) e valida contra o XSD.

Uso: python fix_50_motion_items.py [--dry]
"""
import collections
import os
import re
import sys
import xml.etree.ElementTree as ET

import backup_manager
import rebuild_50_item_templates as rb

SLOTS = ("idle", "run", "jump", "rest", "shop")
REL_XML = "items/item_templates.xml"
# ordem da sequência ItemActions do item_templates.xsd a partir da <learnemotion>: cada ação entra antes da primeira que vem depois
ORDEM = ("learnemotion", "animation", "read", "fireworkact", "instancetimeclear", "cosmetic", "charge", "houseobject", "housedeco",
         "assemble", "adoptpet", "apextract", "remodel", "expextract", "polish", "tuning", "megaphone", "pack", "multireturn")


def tem_animacao(d):
    return any(d.get("custom_%s_anim" % s) for s in SLOTS)


def le_itens(caminho):
    itens = {}
    for _, el in ET.iterparse(caminho, events=("end",)):
        if el.tag == "client_item":
            d = {c.tag: (c.text or "").strip() for c in el}
            if d.get("id") and (d.get("cash_social") or tem_animacao(d)):
                itens[d["id"]] = d
            el.clear()
    return itens


def le_animacoes(cliente):
    t = open(os.path.join(cliente, "data", "animations", "custom_animation.xml"), encoding="utf-8").read()
    anims = {}
    for b in re.findall(r"<custom_animation>(.*?)</custom_animation>", t, re.S):
        d = dict(re.findall(r"<(\w+)>([^<]*)</\1>", b))
        anims[d["name"].lower()] = (d["id"], d["type"].lower())
    return anims


def animacao_do_cliente(d, anims):
    """[(atributo, valor)] da <animation>, ou o motivo da recusa."""
    a = []
    for s in SLOTS:
        nome = d.get("custom_%s_anim" % s)
        if not nome:
            continue
        anim = anims.get(nome.lower())
        if anim is None:
            return "animação %s não existe no custom_animation.xml" % nome
        if anim[1] != s:
            return "%s é %s no custom_animation.xml, não %s" % (nome, anim[1], s)
        a.append((s, anim[0]))
    if (d.get("anim_expire_time") or "0") != "0":
        a.append(("minutes", d["anim_expire_time"]))
    return a


def emocao_do_cliente(d):
    a = [("emotionid", d["cash_social"])]
    if (d.get("cash_available_minute") or "0") != "0":
        a.append(("minutes", d["cash_available_minute"]))
    return a


def poe_acao(bloco, tag, linha, nl):
    """Bloco do template com a ação nova (ou trocada)."""
    velha = re.search(r"\t*<%s\b[^>]*/>" % tag, bloco)
    if velha:
        return bloco.replace(velha.group(0), "\t\t\t" + linha, 1)
    if bloco.endswith("/>"):
        return bloco[:-2].rstrip() + ">" + nl + "\t\t<actions>" + nl + "\t\t\t" + linha + nl + "\t\t</actions>" + nl + "\t</item_template>"
    acoes = re.search(r"(\t\t<actions>)(.*?)(\t\t</actions>)", bloco, re.S)
    if acoes:
        depois = re.search(r"\t*<(%s)\b" % "|".join(ORDEM[ORDEM.index(tag) + 1:]), acoes.group(2))
        pos = acoes.start(2) + (depois.start() if depois else len(acoes.group(2)))
        return bloco[:pos] + "\t\t\t" + linha + nl + bloco[pos:]
    mods = re.search(r"\t\t</modifiers>" + re.escape(nl), bloco)
    pos = mods.end() if mods else bloco.index(">") + 1 + len(nl)
    return bloco[:pos] + "\t\t<actions>" + nl + "\t\t\t" + linha + nl + "\t\t</actions>" + nl + bloco[pos:]


def main():
    seco = "--dry" in sys.argv
    cliente = rb.DEFAULT_CLIENT_DIR
    src = os.path.join(backup_manager.SERVER_DATA_DIR, REL_XML)
    prod = os.path.join(backup_manager.PRODUTO_FINAL_DATA_DIR, REL_XML)
    raw = open(src, "rb").read()
    if raw != open(prod, "rb").read():
        sys.exit("O item_templates.xml do fonte e do Produto Final estão diferentes. Sincronize antes de rodar.")
    text = raw.decode("utf-8")
    nl = "\r\n" if "\r\n" in text[:5000] else "\n"

    cli = le_itens(os.path.join(cliente, "data", "europe", "Items", "client_items.xml"))
    anims = le_animacoes(cliente)
    contagem, exemplos, recusados = collections.Counter(), collections.defaultdict(list), []
    achados = set()

    def edita(m):
        iid = re.search(r'\bid="(\d+)"', m.group(1))
        d = cli.get(iid.group(1)) if iid else None
        if d is None:
            return m.group(0)
        achados.add(d["id"])
        if re.search(r'\bcName="([^"]*)"', m.group(1)).group(1).lower() != d.get("name", "").lower():
            recusados.append((d["id"], "cName do servidor não bate com %s" % d.get("name")))
            return m.group(0)
        acoes = []
        if d.get("cash_social"):
            acoes.append(("learnemotion", emocao_do_cliente(d)))
        if tem_animacao(d):
            quer = animacao_do_cliente(d, anims)
            if isinstance(quer, str):
                recusados.append((d["id"], quer))
            else:
                acoes.append(("animation", quer))
        bloco = m.group(0)
        for tag, quer in acoes:
            tem = re.search(r"<%s\b([^>]*)/>" % tag, bloco)
            if tem and dict(re.findall(r'(\w+)="([^"]*)"', tem.group(1))) == dict(quer):
                continue
            k = "<%s> %s" % (tag, "corrigida" if tem else "criada")
            contagem[k] += 1
            exemplos[k].append(d["id"])
            bloco = poe_acao(bloco, tag, "<%s %s/>" % (tag, " ".join('%s="%s"' % kv for kv in quer)), nl)
        return bloco

    novo = rb.BLOCK_RE.sub(edita, text)
    faltam = sorted(set(cli) - achados, key=int)
    print("itens de motion/emotion no cliente: %d | sem template no servidor: %d %s" % (len(cli), len(faltam), faltam[:10]))
    for k in sorted(contagem):
        print("%-26s %4d   %s%s" % (k, contagem[k], exemplos[k][:10], " ..." if len(exemplos[k]) > 10 else ""))
    for r in recusados:
        print("  recusado", r)
    if novo == text:
        print("nada a mudar")
        return

    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "items", "item_templates.xsd")))
    if not schema.validate(etree.fromstring(novo.encode("utf-8"), parser=etree.XMLParser(huge_tree=True))):
        for e in list(schema.error_log)[:15]:
            print("  XSD linha %d: %s" % (e.line, e.message))
        sys.exit("XSD inválido, nada gravado")
    print("XSD válido")
    if seco:
        print("--dry: nada gravado")
        return
    backup_manager.backup_file_before_modification(REL_XML)
    for p in (src, prod):
        with open(p, "wb") as f:
            f.write(novo.encode("utf-8"))
    print("gravado", src, "e", prod)


if __name__ == "__main__":
    main()
