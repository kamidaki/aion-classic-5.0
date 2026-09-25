#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_food_candy.py

Acerta food, candy e transformacao pelo client_skills/client_items do Classic 5.0.

Escopo: todo item do client_items com mgrouptag de consumivel de buff (I_Food_All, I_Candy_All, I_Drink_All, I_Jelly_All)
ou cuja activation_skill transforma -- direto ou pela skill que ela dispara (SkillLauncher reserved1, penalty_skill_succ): as
transformacoes de deus/apostolo sao item -> Classic_Item_Skill_Trans_*_02 (SkillLauncher) -> *_01 (ShapeChange). Entram as
skills da cadeia inteira. Em 2026-09-22 eram 1.509 itens e 632 skills.

O que estava errado (medido no inicio):
  - 163 itens sem <skilluse> (117 candies de 160010411 a 160010580 importados so com o cabecalho): usar nao fazia nada.
    Esses tambem vinham sem activate_target/activate_count, com mask generico e quality LEGENDARY.
  - 16 skills sem nenhum efeito (so <properties first_target="TARGET"/>), entre elas o candy invisivel 10813 visto no
    S_POLYMORPH oficial (captura outros2 de 2026-09-22).
  - polymorph com effectid 175 onde o cliente tem 275 (115), duracao da 4.x (6), modelo -1 nos candies invisiveis
    (reserved9 "0" = modelo 0) e 885027 no 10322 (reserved9 Ab1_1011_Boss_Li_1 = NPC 260000).
  - StatUp com o 3o e o 4o stat cortados (o conversor antigo so lia reserved13/14/15) e valores da 4.x.
  - uselimits (usedelay/usedelayid) ausente ou diferente do use_delay/use_delay_type_id do cliente.
  - 35 transformacoes de deus/apostolo/evento (160010497-160010578) tambem so com o cabecalho: sem skilluse, sem as 1.000 cargas
    (activation_count; a carga so consome o item na ultima) e sem a area das de Arena (area_to_use -> usearea).

Traducao cliente -> servidor (medida no gabarito: as skills do escopo que ja tinham corpo):
  ShapeChange -> polymorph  model = NPC cujo nome esta em reserved9 ("0" = modelo 0, invisivel), type = reserved8,
                            panelid = reserved4, duration2 = remain2, effectid, element = reserved10. 314/314 iguais
                            fora as diferencas listadas acima.
  StatUp -> statup          4 grupos (token, valor, delta, flag de %): (r13, r2, r1, r6) (r14, r4, r3, r7)
                            (r18, r16, r15, r17) (r22, r20, r19, r21). SPEED/FLY_SPEED/ATTACK_SPEED/BOOST_CASTING_TIME
                            sao sempre PERCENT; attackdelay entra negativo. 1.061 de 1.078 iguais; os 17 restantes sao
                            o 3o/4o stat que faltava e valores/stats que mudaram na 5.0.
  XPBoost -> xpboost        os 4 BOOST_*_XP_RATE PERCENT reserved2 (como nas skills de GM/evento que ja existem).
  BoostSkillCastingTime     reserved3 none/heal/summontrap -> BOOST_CASTING_TIME[_HEAL/_TRAP] PERCENT reserved2.
Cabecalho, properties e condicoes dos stubs saem da classe Estrutura do rebuild_50_skill_effects.py, treinada so no
gabarito deste escopo (a precisao aparece na saida).

Fica de fora e vai para o relatorio: as 12 Classic_Test_Item_Skill_Trans_Candy_* (o effect3 delas vem com as colunas
deslocadas no client_skills: effect3_type = "1") e efeito cujo elemento no servidor e outro (ex.: nofly, search).

Uso:
    python fix_50_food_candy.py --verificar
    python fix_50_food_candy.py --aplicar
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
import rebuild_50_item_templates as ITENS  # noqa: E402
import rebuild_50_skill_effects as SKILLS  # noqa: E402

REL_ITEMS = "items/item_templates.xml"
REL_SKILLS = "skills/skill_templates.xml"
REL_MOTION = "skills/motion_times.xml"
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos")
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_food_candy_50.txt")

TAGS_ESCOPO = {"I_Food_All", "I_Candy_All", "I_Drink_All", "I_Jelly_All"}
SKILL_RE = re.compile(r"\t<skill_template\b([^>]*?)(/>|>(.*?)</skill_template>)", re.S)
ITEM_RE = re.compile(r"\t<item_template\b([^>]*?)(/>|>(.*?)</item_template>)", re.S)
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')


def attrs_de(txt):
    return [(k, html.unescape(v)) for k, v in ATTR_RE.findall(txt or "")]

# ---------------------------------------------------------------- traducao de efeitos

TIPO = {"pc": "PC", "none": "NONE", "form1": "FORM1", "avatar": "AVATAR"}
GRUPOS = [("reserved13", "reserved2", "reserved1", "reserved6"), ("reserved14", "reserved4", "reserved3", "reserved7"),
          ("reserved18", "reserved16", "reserved15", "reserved17"), ("reserved22", "reserved20", "reserved19", "reserved21")]
TOKEN = {
    "maxfp": ("FLY_TIME",), "magicalskillboost": ("BOOST_MAGICAL_SKILL",), "magicalhitaccuracy": ("MAGICAL_ACCURACY",),
    "speed": ("SPEED",), "attackdelay": ("ATTACK_SPEED",), "phyattack": ("PHYSICAL_ATTACK",), "hitaccuracy": ("PHYSICAL_ACCURACY",),
    "maxhp": ("MAXHP",), "maxmp": ("MAXMP",), "boostcastingtime": ("BOOST_CASTING_TIME",), "dodge": ("EVASION",),
    "magicalresist": ("MAGICAL_RESIST",), "hpregen": ("REGEN_HP",), "mpregen": ("REGEN_MP",), "flyspeed": ("FLY_SPEED",),
    "critical": ("PHYSICAL_CRITICAL",), "physicalcriticalreducerate": ("PHYSICAL_CRITICAL_RESIST",),
    "magicalcriticalreducerate": ("MAGICAL_CRITICAL_RESIST",), "pmdefend": ("PHYSICAL_DEFENSE", "MAGICAL_RESIST"),
    "allspeed": ("SPEED", "FLY_SPEED"),
    "elementaldefendall": ("WATER_RESISTANCE", "WIND_RESISTANCE", "FIRE_RESISTANCE", "EARTH_RESISTANCE"),
    "elementaldefendearth": ("EARTH_RESISTANCE",), "elementaldefendwater": ("WATER_RESISTANCE",),
    "elementaldefendfire": ("FIRE_RESISTANCE",), "elementaldefendair": ("WIND_RESISTANCE",),
    "pvpattackratio": ("PVP_ATTACK_RATIO",), "pveattackratio": ("PVE_ATTACK_RATIO",), "pvedefendratio": ("PVE_DEFEND_RATIO",),
    "pvpdefendratio": ("PVP_DEFEND_RATIO",),
}
NEGATIVO = {"ATTACK_SPEED"}  # cliente "attackdelay 3" = servidor ATTACK_SPEED PERCENT -3
TAXA = {"SPEED", "FLY_SPEED", "ATTACK_SPEED", "BOOST_CASTING_TIME"}  # sempre PERCENT, com ou sem a flag (9875, 9935, 10251)
ELEMENTO = {"fire": "FIRE", "water": "WATER", "earth": "EARTH", "air": "WIND", "wind": "WIND", "light": "LIGHT", "dark": "DARK"}
XP = ("BOOST_CRAFTING_XP_RATE", "BOOST_GATHERING_XP_RATE", "BOOST_GROUP_HUNTING_XP_RATE", "BOOST_HUNTING_XP_RATE")
CAST = {"none": "BOOST_CASTING_TIME", "heal": "BOOST_CASTING_TIME_HEAL", "summontrap": "BOOST_CASTING_TIME_TRAP"}
# atributos que este script decide; o resto do elemento (hoptype, basiclvl do polymorph...) fica como esta
GERIDOS = {"polymorph": {"model", "type", "panelid", "duration1", "duration2", "effectid", "element"},
           "statup": {"duration1", "duration2", "effectid", "element", "preeffect", "preeffect_prob", "basiclvl"},
           "xpboost": {"duration1", "duration2", "effectid", "preeffect", "preeffect_prob", "basiclvl"},
           "boostskillcastingtime": {"duration1", "duration2", "effectid", "preeffect", "preeffect_prob"}}


def inteiro(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def efeito(c, n):
    return {k[len("effect%d_" % n):]: v for k, v in c.items() if k.startswith("effect%d_" % n)}


def comuns(g, n):
    a = []
    r1, r2 = inteiro(g.get("remain1")), inteiro(g.get("remain2"))
    if r1:
        a.append(("duration1", str(r1)))
    if r2:
        a.append(("duration2", str(r2)))
    if inteiro(g.get("effectid")):
        a.append(("effectid", g["effectid"]))
    a.append(("e", str(n)))
    base = inteiro(g.get("basiclv"))
    if base:
        a.append(("basiclvl", str(base)))
    return a


def cauda(g, com_elemento=True):
    a = []
    if g.get("noresist") == "1":
        a.append(("noresist", "true"))
    el = ELEMENTO.get((g.get("reserved10") or "").lower()) if com_elemento else None
    if el:
        a.append(("element", el))
    pre = re.fullmatch(r"e(\d(?:_\d)*)", g.get("cond_preeffect") or "")
    if pre:
        a.append(("preeffect", pre.group(1)))
        prob = inteiro(g.get("cond_preeffect_prob2"))
        if prob is not None:  # sem o campo no cliente fica o default do EffectTemplate (100)
            a.append(("preeffect_prob", str(prob)))
    return a


def polymorph(g, n, npcs):
    r9 = (g.get("reserved9") or "").strip()
    model = 0 if r9 == "0" else npcs.get(r9.lower())
    tipo = TIPO.get((g.get("reserved8") or "").lower())
    if model is None or tipo is None:
        return None
    a = [("model", str(model)), ("type", tipo)]
    painel = inteiro(g.get("reserved4"))
    if painel:
        a.append(("panelid", str(painel)))
    return a + comuns(g, n) + cauda(g), []


def statup(g, n, _npcs):
    changes, vistos = [], set()
    for tok, val, dl, pct in GRUPOS:
        t = (g.get(tok) or "").strip()
        if not t or re.fullmatch(r"-?\d+", t):
            continue
        stats = TOKEN.get(t.lower())
        if not stats:
            return None
        v, d = inteiro(g.get(val)) or 0, inteiro(g.get(dl)) or 0
        for s in stats:
            if s in vistos:
                continue
            vistos.add(s)
            sinal = -1 if s in NEGATIVO else 1
            ch = [("stat", s), ("func", "PERCENT" if g.get(pct) == "1" or s in TAXA else "ADD"), ("value", str(sinal * v))]
            if d:
                ch.append(("delta", str(sinal * d)))
            changes.append(ch)
    if not changes:
        return None
    return comuns(g, n) + cauda(g), changes


def xpboost(g, n, _npcs):
    v = inteiro(g.get("reserved2"))
    if not v:
        return None
    return comuns(g, n) + cauda(g, False), [[("stat", s), ("func", "PERCENT"), ("value", str(v))] for s in XP]


def boostskillcastingtime(g, n, _npcs):
    stat, v = CAST.get((g.get("reserved3") or "").lower()), inteiro(g.get("reserved2"))
    if stat is None or v is None:
        return None
    return comuns(g, n) + cauda(g, False), [[("stat", stat), ("func", "PERCENT"), ("value", str(v))]]


TRADUTORES = {"shapechange": ("polymorph", polymorph), "statup": ("statup", statup), "xpboost": ("xpboost", xpboost),
              "boostskillcastingtime": ("boostskillcastingtime", boostskillcastingtime)}


def traduz(c, n, npcs):
    """(tag, [(attr, valor)], [[(attr, valor)] de cada <change>]) ou None."""
    g = efeito(c, n)
    t = (g.get("type") or "").lower()
    if t not in TRADUTORES:
        return None
    tag, fn = TRADUTORES[t]
    r = fn(g, n, npcs)
    return (tag,) + r if r else None


# ---------------------------------------------------------------- XML em texto (o resto do arquivo fica byte a byte igual)

def esc(v):
    return html.escape(str(v), quote=True)


def attrs_txt(pares):
    return "".join(' %s="%s"' % (k, esc(v)) for k, v in pares)


def render_efeito(tag, attrs, changes, nl, recuo="\t\t\t"):
    if not changes:
        return "%s<%s%s/>" % (recuo, tag, attrs_txt(attrs))
    linhas = ["%s<%s%s>" % (recuo, tag, attrs_txt(attrs))]
    linhas += ["%s\t<change%s/>" % (recuo, attrs_txt(ch)) for ch in changes]
    linhas.append("%s</%s>" % (recuo, tag))
    return nl.join(linhas)


def mescla(existentes, desejados, geridos):
    """Atualiza os atributos geridos mantendo a ordem do arquivo; atributo novo entra depois do vizinho que o precede."""
    quero = dict(desejados)
    out = []
    for k, v in existentes:
        if k in geridos:
            if k in quero:
                out.append((k, quero[k]))
        else:
            out.append((k, v))
    ordem = [k for k, _ in desejados]
    for i, k in enumerate(ordem):
        if k not in geridos or any(x == k for x, _ in out):
            continue
        pos = 0
        for anterior in reversed(ordem[:i]):
            idx = next((j for j, (x, _) in enumerate(out) if x == anterior), None)
            if idx is not None:
                pos = idx + 1
                break
        out.insert(pos, (k, quero[k]))
    return out


def efeito_re(tag, n):
    return re.compile(r"([ \t]*)<%s\b([^>]*?\be=\"%d\"[^>]*?)(/>|>(.*?)</%s>)" % (tag, n, tag), re.S)


def changes_de(inner):
    return [attrs_de(m.group(1)) for m in re.finditer(r"<change\b([^>]*?)/?>", inner or "")]


def so_changes(inner):
    return set(re.findall(r"<(\w+)", inner or "")) <= {"change"}


def normaliza(changes):
    return sorted(tuple(sorted((k, v) for k, v in ch if not (k == "delta" and v == "0"))) for ch in changes)


# ---------------------------------------------------------------- leitura

def le_cliente(pasta):
    txt = open(os.path.join(pasta, "data", "skills", "client_skills.xml"), encoding="utf-8", errors="replace").read()
    skills = {}
    for m in re.finditer(r"<skill_base_client>(.*?)</skill_base_client>", txt, re.S):
        d = {k: v.strip() for k, v in re.findall(r"<([a-z_0-9]+)>([^<]*)</\1>", m.group(1))}
        if d.get("id"):
            skills[d["id"]] = d
    npcs = {}
    txt = open(os.path.join(pasta, "data", "npcs", "client_npcs.xml"), encoding="utf-8", errors="replace").read()
    for m in re.finditer(r"<npc_client>\s*<id>(\d+)</id>\s*<name>([^<]*)</name>", txt):
        npcs.setdefault(m.group(2).strip().lower(), int(m.group(1)))
    campos = ITENS.KEEP | {"use_delay", "use_delay_type_id", "area_to_use"}
    itens = {d["id"]: d for d in ITENS.iter_depth1(os.path.join(pasta, "data", "items", "client_items.xml"),
                                                    lambda t: t in campos) if d.get("id")}
    return skills, npcs, itens


def blocos(texto, rx, chave):
    out = {}
    for m in rx.finditer(texto):
        a = dict(attrs_de(m.group(1)))
        if a.get(chave):
            out[a[chave]] = (m.span(), m.group(1), m.group(3))
    return out


def aplica_edicoes(texto, edicoes):
    out, pos = [], 0
    for a, b, novo in sorted(edicoes):
        if a < pos:
            raise RuntimeError("edicoes sobrepostas em %d" % a)
        out += [texto[pos:a], novo]
        pos = b
    out.append(texto[pos:])
    return "".join(out)


# ---------------------------------------------------------------- skills

def corrige_skills(texto, cli, npcs, alvo, rel):
    nl = "\r\n" if "\r\n" in texto else "\n"
    tpl = blocos(texto, SKILL_RE, "skill_id")
    motions = {n.lower() for n in re.findall(r'<motion_time name="([^"]+)"',
                                             open(os.path.join(backup_manager.SERVER_DATA_DIR, REL_MOTION), encoding="utf-8").read())}
    skill_por_nome = {c["name"].lower(): sid for sid, c in cli.items() if c.get("name")}

    gabarito, stubs = [], []
    for sid in sorted(alvo, key=int):
        if sid not in tpl or sid not in cli:
            rel["skill do escopo sem template no servidor ou no cliente"].append(sid)
            continue
        (_s, cab, inner) = tpl[sid]
        if inner and "<effects>" in inner:
            try:
                gabarito.append((sid, ET.fromstring("<r>" + inner + "</r>"), dict(attrs_de(cab))))
            except ET.ParseError:
                rel["template que nao abre como XML (mantido)"].append(sid)
        else:
            stubs.append(sid)
    est = SKILLS.Estrutura(gabarito, cli, skill_por_nome, motions)
    acerto = collections.Counter()
    for sid, r, a in gabarito:
        c = cli[sid]
        novo = est.template(c, a)
        acerto["cabecalho"] += all(novo.get(k) == a.get(k) for k in SKILLS.CHAVES_TEMPLATE)
        p = r.find("properties")
        acerto["properties"] += SKILLS.sem_default(dict(est.properties(c))) == SKILLS.sem_default(dict(p.attrib) if p is not None else {})
        sc, uc, _ac = est.condicoes(c)
        for nome, lista in (("startconditions", sc), ("useconditions", uc)):
            s = r.find(nome)
            real = sorted((x.tag, tuple(sorted(SKILLS.sem_default(dict(x.attrib)).items()))) for x in s) if s is not None else []
            acerto[nome] += sorted((t, tuple(sorted(SKILLS.sem_default(dict(p)).items()))) for t, p in lista) == real
        acerto["noremoveatdie"] += (a.get("noremoveatdie") == "true") == (c.get("no_remove_at_die") == "1")
    print("   gabarito do escopo: %d skills | stubs: %d" % (len(gabarito), len(stubs)))
    print("   estrutura no gabarito: " + " | ".join("%s %.1f%%" % (k, 100 * v / len(gabarito)) for k, v in acerto.items()))
    rel["_estrutura"] = ["%s %d/%d" % (k, v, len(gabarito)) for k, v in acerto.items()]

    edicoes = []
    # 1. skills com corpo: corrige os efeitos traduziveis
    for sid, _r, _a in gabarito:
        c = cli[sid]
        (ini, fim), cab, inner = tpl[sid]
        bloco = texto[ini:fim]
        novo_bloco = bloco
        for n in range(1, 5):
            tipo = (c.get("effect%d_type" % n) or "").lower()
            if tipo not in TRADUTORES:
                continue
            tr = traduz(c, n, npcs)
            tag = TRADUTORES[tipo][0]
            if tr is None:
                rel["efeito que nao traduz (mantido)"].append("%s %s e%d %s" % (sid, c.get("name"), n, tipo))
                continue
            m = efeito_re(tag, n).search(novo_bloco)
            if m is None:
                rel["efeito do cliente com outro elemento ou ausente no servidor (mantido)"].append(
                    "%s %s e%d %s" % (sid, c.get("name"), n, tipo))
                continue
            _tag, desejados, changes = tr
            existentes = attrs_de(m.group(2))
            geridos = set(GERIDOS[tag])
            # preeffect_prob so conta quando muda o valor efetivo (ausente = 100 no EffectTemplate)
            prob_atual = dict(existentes).get("preeffect_prob", "100")
            if dict(desejados).get("preeffect_prob", "100") == prob_atual:
                geridos.discard("preeffect_prob")
                desejados = [(k, v) for k, v in desejados if k != "preeffect_prob"]
            attrs = mescla(existentes, desejados, geridos)
            atuais = changes_de(m.group(4))
            troca_changes = bool(changes) and normaliza(atuais) != normaliza(changes)
            if troca_changes and not so_changes(m.group(4)):
                rel["efeito com filhos alem de <change> (stats mantidos)"].append("%s %s e%d" % (sid, c.get("name"), n))
                troca_changes = False
            if attrs == existentes and not troca_changes:
                continue
            for (k, v) in existentes:
                if dict(attrs).get(k) != v:
                    rel["%s.%s" % (tag, k)].append("%s %s: %s -> %s" % (sid, c.get("name"), v, dict(attrs).get(k)))
            for k, v in attrs:
                if k not in dict(existentes):
                    rel["%s.%s" % (tag, k)].append("%s %s: (sem) -> %s" % (sid, c.get("name"), v))
            if troca_changes:
                rel["%s <change>" % tag].append("%s %s e%d: %s -> %s" % (
                    sid, c.get("name"), n, [" ".join(v for _, v in ch) for ch in atuais], [" ".join(v for _, v in ch) for ch in changes]))
            if troca_changes:
                novo = render_efeito(tag, attrs, changes, nl, m.group(1))
            else:  # so o cabecalho do elemento muda; os filhos ficam como estao
                fecho = "/>" if m.group(3) == "/>" else ">" + m.group(4) + "</%s>" % tag
                novo = "%s<%s%s%s" % (m.group(1), tag, attrs_txt(attrs), fecho)
            novo_bloco = novo_bloco[:m.start()] + novo + novo_bloco[m.end():]
        if novo_bloco != bloco:
            edicoes.append((ini, fim, novo_bloco))

    # 2. stubs: corpo inteiro
    for sid in stubs:
        c = cli[sid]
        (ini, fim), cab, _inner = tpl[sid]
        tipos = sorted((int(m.group(1)), c[k].lower()) for k in c for m in [re.fullmatch(r"effect(\d)_type", k)] if m)
        efeitos, falta = [], None
        for n, t in tipos:
            tr = traduz(c, n, npcs)
            if tr is None:
                falta = "e%d %s" % (n, c.get("effect%d_type" % n))
                break
            efeitos.append(tr)
        if falta:
            motivo = "client_skills com colunas deslocadas" if (c.get("effect%s_type" % falta[1]) or "").isdigit() else "tipo sem tradutor"
            rel["stub mantido (%s)" % motivo].append("%s %s: %s" % (sid, c.get("name"), falta))
            continue
        atual = dict(attrs_de(cab))
        cabecalho = est.template(c, atual)
        if c.get("no_remove_at_die") == "1":
            cabecalho["noremoveatdie"] = "true"
        linhas = ["\t<skill_template" + attrs_txt(cabecalho.items()) + ">",
                  "\t\t<properties" + attrs_txt((k, v) for k, v in est.properties(c) if v is not None) + "/>"]
        sc, uc, ac = est.condicoes(c)
        for nome, lista in (("startconditions", sc), ("useconditions", uc)):
            if lista:
                linhas.append("\t\t<%s>" % nome)
                linhas += ["\t\t\t<%s%s/>" % (t, attrs_txt((k, v) for k, v in p if v is not None)) for t, p in lista]
                linhas.append("\t\t</%s>" % nome)
        linhas.append("\t\t<effects>")
        linhas += [render_efeito(tag, attrs, changes, nl) for tag, attrs, changes in efeitos]
        linhas.append("\t\t</effects>")
        if ac:
            linhas.append("\t\t<actions>")
            linhas += ["\t\t\t<%s%s/>" % (t, attrs_txt((k, v) for k, v in p if v is not None)) for t, p in ac]
            linhas.append("\t\t</actions>")
        mo = est.motion(c)
        if mo:
            linhas.append("\t\t<motion" + attrs_txt((k, v) for k, v in mo if v is not None) + "/>")
        linhas.append("\t</skill_template>")
        edicoes.append((ini, fim, nl.join(linhas)))
        rel["stub com corpo gerado"].append("%s %s: %s" % (sid, c.get("name"), " ".join(t for t, _, _ in efeitos)))
    return aplica_edicoes(texto, edicoes), len(edicoes)


# ---------------------------------------------------------------- itens

def corrige_itens(texto, cli_itens, skill_id_por_nome, escopo, rel):
    nl = "\r\n" if "\r\n" in texto else "\n"
    tpl = blocos(texto, ITEM_RE, "id")
    edicoes = []
    for iid in sorted(escopo, key=int):
        d = cli_itens[iid]
        if iid not in tpl:
            rel["item do escopo ausente no servidor"].append("%s %s" % (iid, d.get("name")))
            continue
        (ini, fim), cab, inner = tpl[iid]
        attrs = attrs_de(cab)
        skill =skill_id_por_nome.get(ITENS.low(d, "activation_skill"))
        nivel = d.get("activation_level") or "1"
        inner = inner or ""
        novo_inner = inner
        novos_attrs = list(attrs)

        def poe(k, v):
            nonlocal novos_attrs
            if any(x == k for x, _ in novos_attrs):
                novos_attrs = [(x, v if x == k else y) for x, y in novos_attrs]
            else:
                pos = next((i for i, (x, _) in enumerate(novos_attrs) if x in ("client_mask",)), len(novos_attrs))
                novos_attrs.insert(pos, (k, v))

        su = re.search(r'<skilluse\b([^>]*?)/>', inner)
        if su is None:
            if not skill:
                rel["item sem skill no cliente"].append("%s %s" % (iid, d.get("name")))
                continue
            if "<actions>" in inner:
                rel["item com <actions> sem skilluse (mantido)"].append("%s %s" % (iid, d.get("name")))
                continue
            # item importado so com o cabecalho: completa pelo cliente (regras do rebuild_50_item_templates)
            tgt = (d.get("activate_target") or "").upper()
            if tgt:
                poe("activate_target", tgt)
            cnt = ITENS.num(d.get("activation_count"))
            if cnt:
                poe("activate_count", str(cnt))
            poe("mask", str(ITENS.gen_mask(d)))
            q = ITENS.QUALITY.get(ITENS.low(d, "quality"))
            if q:
                poe("quality", q)
            acoes = "\t\t<actions>%s\t\t\t<skilluse skillid=\"%s\" level=\"%s\"/>%s\t\t</actions>" % (nl, skill, nivel, nl)
            m = re.search(r"<(modifiers)\b.*?</modifiers>", novo_inner, re.S)
            if m:
                novo_inner = novo_inner[:m.end()] + nl + acoes + novo_inner[m.end():]
            else:
                novo_inner = nl + acoes + (novo_inner if novo_inner.strip() else nl + "\t")
            rel["item completado (skilluse, activate_*, mask, quality)"].append("%s %s -> skill %s nivel %s" % (iid, d.get("name"), skill, nivel))
        else:
            sa = dict(attrs_de(su.group(1)))
            if skill and sa.get("skillid") == skill and sa.get("level") != nivel:
                novo_su = re.sub(r'\blevel="[^"]*"', 'level="%s"' % nivel, su.group(0))
                novo_inner = novo_inner.replace(su.group(0), novo_su, 1)
                rel["skilluse.level"].append("%s %s: %s -> %s" % (iid, d.get("name"), sa.get("level"), nivel))
            elif skill and sa.get("skillid") != skill:
                rel["skilluse de outra skill (mantido; ver fix_50_item_activation_skill.py)"].append(
                    "%s %s: servidor %s, cliente %s" % (iid, d.get("name"), sa.get("skillid"), skill))

        # uselimits: usedelay/usedelayid = use_delay/use_delay_type_id do cliente; usearea = area_to_use em maiusculas (como os
        # 23 IDARENA_PVP_ITEMUSEAREA_ALL que ja existiam). O ItemUseLimits so guarda uma area: lista no cliente vai para o relatorio.
        atraso, grupo = ITENS.num(d.get("use_delay")) or 0, ITENS.num(d.get("use_delay_type_id")) or 0
        area = (d.get("area_to_use") or "").strip()
        if "," in area:
            rel["area_to_use com varias areas (usearea mantido)"].append("%s %s: %s" % (iid, d.get("name"), area))
            area = ""
        ul = re.search(r"<uselimits\b([^>]*?)/>", novo_inner)
        if ul:
            ua = attrs_de(ul.group(1))
            quero = [("usedelay", str(atraso)), ("usedelayid", str(grupo))] if atraso else []
            nua = mescla(ua, quero, {"usedelay", "usedelayid"})
            if area and "usearea" not in dict(nua):
                nua.append(("usearea", area.upper()))
            if nua != ua:
                novo_ul = "<uselimits%s/>" % attrs_txt(nua) if nua else ""
                if not nua:
                    novo_inner = re.sub(r"[ \t]*<uselimits\b[^>]*?/>\r?\n?", "", novo_inner, count=1)
                else:
                    novo_inner = novo_inner.replace(ul.group(0), novo_ul, 1)
                rel["uselimits"].append("%s %s: %s -> %s" % (iid, d.get("name"), dict(ua), dict(nua)))
        elif atraso or area:
            pares = ([("usedelay", str(atraso)), ("usedelayid", str(grupo))] if atraso else []) + ([("usearea", area.upper())] if area else [])
            linha = "\t\t<uselimits%s/>" % attrs_txt(pares)
            m = re.search(r"[ \t]*<(inventory|idian)\b", novo_inner)
            if m:
                novo_inner = novo_inner[:m.start()] + linha + nl + novo_inner[m.start():]
            else:
                novo_inner = novo_inner.rstrip("\t") + linha + nl + "\t"
            rel["uselimits (novo)"].append("%s %s: %s" % (iid, d.get("name"), dict(pares)))

        if novo_inner == inner and novos_attrs == attrs:
            continue
        if not novo_inner.startswith(nl):
            novo_inner = nl + novo_inner.lstrip("\r\n")
        if not novo_inner.endswith(nl + "\t"):
            novo_inner = novo_inner.rstrip("\r\n\t ") + nl + "\t"
        edicoes.append((ini, fim, "\t<item_template%s>%s</item_template>" % (attrs_txt(novos_attrs), novo_inner)))
    return aplica_edicoes(texto, edicoes), len(edicoes)


# ---------------------------------------------------------------- principal

def valida(texto, rel_xsd):
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "static_data.xsd")))
    doc = etree.fromstring(texto.encode("utf-8"), parser=etree.XMLParser(huge_tree=True))
    if not schema.validate(doc):
        for e in list(schema.error_log)[:20]:
            print("   linha %d: %s" % (e.line, e.message))
        sys.exit("   XSD INVALIDO (%s): nada foi gravado." % rel_xsd)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    for rel_xml in (REL_ITEMS, REL_SKILLS):
        a, b = (open(os.path.join(base, rel_xml), "rb").read() for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR))
        if hashlib.sha256(a).digest() != hashlib.sha256(b).digest():
            sys.exit("%s do fonte e do Produto Final estao diferentes. Sincronize antes de rodar." % rel_xml)

    print("1. Lendo o cliente (skills, npcs, itens)...")
    cli, npcs, cli_itens = le_cliente(args.cliente)
    skill_id_por_nome = {}
    for sid, c in cli.items():
        skill_id_por_nome.setdefault(c.get("name", "").lower(), sid)
    def cadeia(sid, visto=()):
        """a skill e as que ela dispara: SkillLauncher (reserved1 = nome; item -> _02 -> _01 com o ShapeChange) e
        penalty_skill_succ (20738 Item_Skill_Trans_Ariel_02 -> 10680 com o ShapeChange)"""
        out = [sid]
        nomes = [cli[sid].get("effect%d_reserved1" % n) for n in range(1, 5)
                 if (cli[sid].get("effect%d_type" % n) or "").lower() == "skilllauncher"]
        nomes.append(cli[sid].get("penalty_skill_succ"))
        for nome in nomes:
            alvo_l = skill_id_por_nome.get((nome or "").lower())
            if alvo_l and alvo_l not in visto and alvo_l != sid:
                out += cadeia(alvo_l, visto + (sid,))
        return out

    escopo_itens, alvo = set(), set()
    for iid, d in cli_itens.items():
        sid = skill_id_por_nome.get(ITENS.low(d, "activation_skill"))
        if not sid:
            continue
        tags = {t.strip() for t in (d.get("mgrouptag") or "").split(",")}
        skills_item = cadeia(sid)
        transforma = any((cli[s].get("effect%d_type" % n) or "").lower() == "shapechange" for s in skills_item for n in range(1, 5))
        if tags & TAGS_ESCOPO or transforma:
            escopo_itens.add(iid)
            alvo.update(skills_item)
    print("   escopo: %d itens, %d skills" % (len(escopo_itens), len(alvo)))

    rel = collections.defaultdict(list)
    print("2. Skills...")
    caminho = os.path.join(backup_manager.SERVER_DATA_DIR, REL_SKILLS)
    texto_skills = open(caminho, encoding="utf-8", newline="").read()
    novo_skills, n_skills = corrige_skills(texto_skills, cli, npcs, alvo, rel)
    print("   templates alterados: %d" % n_skills)

    print("3. Itens...")
    caminho = os.path.join(backup_manager.SERVER_DATA_DIR, REL_ITEMS)
    texto_itens = open(caminho, encoding="utf-8", newline="").read()
    novo_itens, n_itens = corrige_itens(texto_itens, cli_itens, skill_id_por_nome, escopo_itens, rel)
    print("   templates alterados: %d" % n_itens)

    for k in sorted(rel):
        if not k.startswith("_"):
            print("   %-70s %d" % (k, len(rel[k])))

    print("4. Validando contra o static_data.xsd agregado...")
    valida(novo_skills, REL_SKILLS)
    valida(novo_itens, REL_ITEMS)
    print("   valido")

    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("fix_50_food_candy.py -- escopo: %d itens, %d skills\n" % (len(escopo_itens), len(alvo)))
        f.write("estrutura dos stubs medida no gabarito: %s\n" % ", ".join(rel.pop("_estrutura", [])))
        for k in sorted(rel):
            f.write("\n== %s: %d\n" % (k, len(rel[k])))
            f.writelines("  %s\n" % x for x in rel[k])
    print("   relatorio: " + RELATORIO)

    if not args.aplicar:
        print("\nModo --verificar: nada foi gravado.")
        return
    print("5. Gravando (com backup)...")
    for rel_xml, novo, antigo in ((REL_SKILLS, novo_skills, texto_skills), (REL_ITEMS, novo_itens, texto_itens)):
        if novo == antigo:
            continue
        backup_manager.backup_file_before_modification(rel_xml)
        for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
            p = os.path.join(base, rel_xml)
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(novo)
            print("   Gravado: " + p)


if __name__ == "__main__":
    main()
