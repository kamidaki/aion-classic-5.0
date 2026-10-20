"""Sanctification (charge/improve) dos itens do client_items 5.0 que o item_templates.xml não tem.

Em 18/10/2026, 981 itens do cliente têm <charge_level>. Desses, 666 tinham <improve> e os bônus por nível no servidor, e 315 não
tinham nenhum dos dois (os novos do 5.0, como o Elite Guardian Commodore's Breastplate), então a Sanctification não fazia nada
neles. Parte dos 315 é template auto-fechado (<item_template .../>), sem <modifiers>.

Regras medidas nos 666 que já estavam certos (100% em cada uma):
  <improve way="1" level=charge_level burn_attack=burn_on_attack burn_defend=burn_on_defend price1=charge_price1 x 1.000.000
           [price2=charge_price2 x 1.000.000, só quando o cliente tem]/>
  bonus_attr_aN -> modifier com <conditions><charge value="1"/></conditions> ("Sanctification Effect (1)")
  bonus_attr_bN -> o mesmo com <charge value="2"/>; o ItemChargeCondition é cumulativo (nível >= value)
Os nomes de atributo usam o BONUS_MODS/MULTI_BONUS_MODS/NEGATE do rebuild_50_item_templates.py ("X%" vira rate,
attackDelay inverte o sinal). Na sequência do ItemTemplate (item_templates.xsd), <modifiers> é o primeiro filho e <improve> vem
antes de uselimits, inventory e idian.

Só mexe em item que não tem <improve>. Idempotente. Uso: python fix_50_item_improve.py [--dry] [item_templates.xml ...]
"""
import collections
import os
import re
import sys

from fix_50_energia_sp_ep import RAIZ, XMLS
from rebuild_50_item_templates import BONUS_MODS, MULTI_BONUS_MODS, NEGATE

TEMPLATES = os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data", "items", "item_templates.xml")

ATRIBUTOS = r'(?:[^>/]|/(?!>))*'  # atributos do <item_template> sem atravessar o "/>" de um template auto-fechado


def preco(v):
    return int(round(float(v) * 1000000))


def mods_de_nivel(f, prefixo, nivel, faltando):
    out = []
    for k in sorted((k for k in f if re.fullmatch(r"bonus_attr_%s\d+" % prefixo, k)), key=lambda k: int(k[12:])):
        partes = f[k].split()
        if len(partes) < 2:
            continue
        nome, bruto = partes[0].lower(), partes[-1]
        try:
            v = int(float(bruto.rstrip("%")))
        except ValueError:
            continue
        if not v:
            continue
        stats = MULTI_BONUS_MODS.get(nome) or ((BONUS_MODS[nome],) if nome in BONUS_MODS else ())
        if not stats:
            faltando[nome] += 1
            continue
        op = "rate" if bruto.endswith("%") else "add"
        for stat in stats:
            out.append((op, stat, -v if nome in NEGATE else v, nivel))
    return out


def le_cliente():
    cli = {}
    for b in open(os.path.join(XMLS, "items", "client_items.xml"), encoding="utf-8", errors="replace").read().split("<client_item>")[1:]:
        f = dict(re.findall(r"<(\w+)>([^<]*)</\1>", b))
        if f.get("charge_level", "0") not in ("0", ""):
            cli[int(f["id"])] = f
    return cli


def aplica(caminho, cli, seco):
    raw = open(caminho, encoding="utf-8", newline="").read()
    eol = "\r\n" if "\r\n" in raw[:5000] else "\n"
    feitos, faltando, criados_mod = [], collections.Counter(), []

    def abre(m):
        if int(m.group(3)) not in cli:
            return m.group(0)
        return m.group(1) + m.group(2) + ">" + eol + m.group(1) + "</item_template>"

    texto = re.sub(r'(?m)^([ \t]*)(<item_template id="(\d+)"' + ATRIBUTOS + r')\s*/>', abre, raw)

    def edita(m):
        iid = int(m.group(3))
        f = cli.get(iid)
        corpo = m.group(4)
        if f is None or "<improve " in corpo:
            return m.group(0)
        ind_t = m.group(1)
        ind = ind_t + "\t"
        mods = mods_de_nivel(f, "a", 1, faltando) + mods_de_nivel(f, "b", 2, faltando)
        improve = '<improve way="1" level="%s" burn_attack="%s" burn_defend="%s" price1="%d"%s/>' % (
            f["charge_level"], f["burn_on_attack"], f["burn_on_defend"], preco(f["charge_price1"]),
            ' price2="%d"' % preco(f["charge_price2"]) if f.get("charge_price2") else "")
        if mods:
            linhas = []
            for op, stat, v, nivel in mods:
                linhas += ['%s\t<%s name="%s" value="%d" bonus="true">' % (ind, op, stat, v), "%s\t\t<conditions>" % ind,
                           '%s\t\t\t<charge value="%d"/>' % (ind, nivel), "%s\t\t</conditions>" % ind, "%s\t</%s>" % (ind, op)]
            fecha = re.search(r"([ \t]*)</modifiers>", corpo)
            if fecha:
                corpo = corpo[:fecha.start()] + eol.join(linhas) + eol + corpo[fecha.start():]
            else:
                bloco = eol.join([ind + "<modifiers>"] + linhas + [ind + "</modifiers>"])
                corpo = eol + bloco + eol + corpo.lstrip("\r\n")
                criados_mod.append(iid)
        depois = re.search(r"([ \t]*)<(uselimits|inventory|idian)\b", corpo)
        if depois:
            corpo = corpo[:depois.start()] + depois.group(1) + improve + eol + corpo[depois.start():]
        else:
            corpo = corpo.rstrip(" \t\r\n") + eol + ind + improve + eol + ind_t
        feitos.append(iid)
        return m.group(1) + m.group(2) + corpo + m.group(5)

    novo = re.sub(r'(?m)^([ \t]*)(<item_template id="(\d+)"' + ATRIBUTOS + r'>)((?:(?!<item_template ).)*?)(</item_template>)',
                  edita, texto, flags=re.S)
    print(caminho, "itens:", len(feitos), "<modifiers> criado:", len(criados_mod), "atributos sem mapa:", dict(faltando))
    if novo != raw and not seco:
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(novo)


def main():
    seco = "--dry" in sys.argv
    caminhos = [a for a in sys.argv[1:] if a != "--dry"] or [TEMPLATES]
    cli = le_cliente()
    for caminho in caminhos:
        aplica(caminho, cli, seco)


if __name__ == "__main__":
    main()
