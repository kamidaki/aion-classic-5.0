#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_50_skill_effects.py

Da corpo aos skill_templates que estao vazios. Na 5.0 o cliente tem 4622 skills com efeito que no servidor sao so
<properties first_target="TARGET" />: sem condicao, sem custo, sem motion e sem nenhum efeito. No jogo a animacao
sai e o dano nao, porque nao ha efeito para aplicar (147 das 360 skills do gladiador, 144 das 343 do assassino).

Nada aqui e suposto pelo nome. Cada peca sai de um campo do client_skills.xml, e a traducao campo -> atributo e
medida no gabarito: as skills que ja estao completas e cujo stack e o nome do cliente (5727). O gabarito e dividido
em duas metades por skill_id -- aprende numa, mede na outra.

Como se mede: o gabarito e da 4.8 e o cliente e da 5.0, entao numero diferente nem sempre e erro (duracao que caiu
de 90 para 60 s, dano que subiu de 20 para 40). A medicao separa os componentes de cada efeito:
    enums+stats  enums, booleanos e os stats/funcs dos <change> -- e onde uma fonte errada aparece
    presenca     mesmo conjunto de atributos -- onde a 4.8 e a 5.0 mais divergem (duracao que so o cliente tem)
    numeros      valor igual onde os dois lados tem o atributo -- prova que a fonte do numero e a certa
Atributo igual ao default do Java (critprobmod2 100, hittype EVERYHIT, int 0...) conta como ausente dos dois lados.
Um tipo de efeito so gera XML se passar nos tres limiares; uma skill so recebe corpo quando TODOS os efeitos dela
passam. As outras continuam stub e ficam listadas no relatorio.

Fontes (achadas no gabarito, nao supostas):
    skillatk         value = reserved2, ou reserved4 quando reserved2 e 0; delta = reserved1 ou reserved3 do mesmo par
    spellatkinstant  value = reserved2, delta = reserved1
    spellatk (DoT)   value = reserved9, delta = reserved8, checktime
    provoker         skill_id = id da skill cujo nome esta em reserved17
    polymorph        model = id do NPC cujo nome esta em reserved9
    skilllauncher    skill_id = id da skill cujo nome esta em reserved1
    <change>         cada token de reserved13..15 vira os stats dele (tabela do gabarito; token que o gabarito nao
                     tem sozinho sai do nome do StatEnum -- regra que acerta 30 de 31 tokens conhecidos); o valor e
                     por token: reserved2 no 1o, reserved4 no 2o (496 de 506), com o sinal que o stat usa
    armas            required_2hsword/book/bow/dagger/mace/orb/polearm/staff/sword/chainblade -> <weapon>
    custo            cost_parameter MP/HP/HP_RATIO + cost_end/cost_end_lv, cost_dp, cost_sp -> condicao e *use
    corrente         chain_category_name em skill de corrente -> <chain>, time = chain_time ou 1000
    movimento        move_casting != 1 -> <playermove allow="false" />
    motion           motion_name, so se existir no motion_times.xml (o MotionData busca sem caixa)

Uso (a pasta do cliente e a que contem data/ e Strings/):
    python rebuild_50_skill_effects.py --cliente "<pasta dos XMLs do cliente 5.0>"            (mede, gera e valida)
    python rebuild_50_skill_effects.py --cliente "<pasta dos XMLs do cliente 5.0>" --aplicar  (grava com backup)
    --ids 22016,22017  limita a geracao a esses skill_id (ex.: so as skills novas de uma classe)
A pasta tambem pode vir da variavel de ambiente AION_CLIENT_XML_DIR.
"""

import argparse
import collections
import os
import re
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import quoteattr

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402
import common_bxml  # noqa: E402
DEFAULT_CLIENT_DIR = common_bxml.BASE_CLIENT

REL_XML = os.path.join("skills", "skill_templates.xml")
REL_XSD = os.path.join("skills", "skills.xsd")
REL_TREE = os.path.join("skill_tree", "skill_tree.xml")
REL_MOTION = os.path.join("skills", "motion_times.xml")
STAT_ENUM = os.path.join(backup_manager.PROJECT_ROOT, "Código Fonte - Emulador", "game-server", "src", "com",
                         "aionemu", "gameserver", "model", "stats", "container", "StatEnum.java")
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_skill_effects_50.txt")
BLOCK_RE = re.compile(r"\t<skill_template\b([^>]*?)(/>|>(.*?)</skill_template>)", re.S)

# ordem em que o servidor escreve as armas (2789 de 3490 skills no gabarito)
ARMAS = [("GREATSWORD", "required_2hsword"), ("SPELLBOOK", "required_book"), ("BOW", "required_bow"),
         ("DAGGER", "required_dagger"), ("MACE", "required_mace"), ("ORB", "required_orb"),
         ("POLEARM", "required_polearm"), ("STAFF", "required_staff"), ("SWORD", "required_sword"),
         ("CHAINBLADE", "required_chainblade")]
CLASSES_JOGAVEIS = {"GLADIATOR", "TEMPLAR", "RANGER", "ASSASSIN", "SORCERER", "SPIRIT_MASTER", "CLERIC", "CHANTER",
                    "WARRIOR", "SCOUT", "MAGE", "PRIEST",
                    "LUMINESS", "PHOENIX", "REVENANT", "BRAWLER", "THUNDERER", "SOUL_REAPER", "MONK"}
# defaults do EffectTemplate/Properties: atributo com esse valor e o mesmo que ausente
DEFAULTS = {"hittype": "EVERYHIT", "hittypeprob2": "100", "noresist": "false", "preeffect_prob": "100",
            "critprobmod2": "100", "mrresist": "true", "element": "NONE", "direction": "NONE", "awr": "false",
            "prob": "100"}
TAGS_STAT = {"statup", "statdown", "statboost", "weaponstatboost", "snare", "slow", "wpnmastery", "armormastery",
             "shieldmastery", "weaponstatup", "boostskillcastingtime"}


# ---------------------------------------------------------------- utilidades

def norm(v):
    if v is None:
        return None
    v = v.strip().lower().replace("_", "")
    try:
        f = float(v)
        return str(int(f)) if f == int(f) else "%g" % f
    except ValueError:
        return v


def inteiro(v):
    try:
        return str(int(float(v))) if v not in (None, "") else None
    except ValueError:
        return None


def nz(v):
    i = inteiro(v)
    return None if i in (None, "0") else i


def castando(c):
    return (inteiro(c.get("casting_delay")) or "0") != "0"


def sem_default(attrs):
    out = {}
    for k, v in attrs.items():
        if v is None or DEFAULTS.get(k) == v:
            continue
        if re.fullmatch(r"-?\d+", v) and int(v) == 0 and k not in ("value",):
            continue
        out[k] = v
    return out


_STATS = None

TOKEN_MAP = {
    "allattackratio": ("PVP_ATTACK_RATIO", "PVE_ATTACK_RATIO"),
    "alldefendratio": ("PVP_DEFEND_RATIO", "PVE_DEFEND_RATIO"),
    "pveattackratio": ("PVE_ATTACK_RATIO",),
    "magicalskillboostresist": ("MAGIC_SKILL_BOOST_RESIST",),
    "physicaldefend": ("PHYSICAL_DEFENSE",),
    "critical": ("PHYSICAL_CRITICAL",),
    "magicalskillboost": ("BOOST_MAGICAL_SKILL",),
    "magicalhitaccuracy": ("MAGICAL_ACCURACY",),
    "maxfp": ("FLY_TIME",),
    "speedratio": ("SPEED",),
    "attackdelayratio": ("ATTACK_SPEED",),
    "boostcastingtimeratio": ("BOOST_CASTING_TIME",),
}


def stat_por_nome(token):
    """token do cliente sem par no gabarito -> stat pelo nome do StatEnum (igual, ar<x> = <x>_RESISTANCE,
    <x>regen = REGEN_<x>). Medida nos tokens que o gabarito tem sozinhos: 30 de 31."""
    global _STATS
    if _STATS is None:
        nomes = []
        if os.path.isfile(STAT_ENUM):
            with open(STAT_ENUM, encoding="utf-8") as stat_file:
                nomes = re.findall(r"^\s*([A-Z][A-Z0-9_]+)\s*[\(,;]", stat_file.read(), re.M)
        _STATS = {n.replace("_", "").lower(): n for n in nomes}
    if not token:
        return None
    tok_clean = token.lower().replace("_", "")
    if tok_clean in TOKEN_MAP:
        return TOKEN_MAP[tok_clean]
    if tok_clean.endswith("arp"):
        prefix = tok_clean[:-3]
        if prefix + "resistancepenetration" in _STATS:
            return (_STATS[prefix + "resistancepenetration"],)
        if prefix + "penetration" in _STATS:
            return (_STATS[prefix + "penetration"],)
    if tok_clean in _STATS:
        return (_STATS[tok_clean],)
    if tok_clean.startswith("ar") and tok_clean[2:] + "resistance" in _STATS:
        return (_STATS[tok_clean[2:] + "resistance"],)
    if tok_clean.endswith("regen") and "regen" + tok_clean[:-5] in _STATS:
        return (_STATS["regen" + tok_clean[:-5]],)
    return None


class Tabela:
    """chave -> valor mais comum visto; chave nova cai no fallback."""

    def __init__(self):
        self.c = collections.defaultdict(collections.Counter)

    def add(self, chave, valor):
        self.c[chave][valor] += 1

    def tem(self, chave):
        return chave in self.c

    def get(self, chave, padrao=None):
        return self.c[chave].most_common(1)[0][0] if chave in self.c else padrao


def xml_attrs(pares):
    return "".join(" %s=%s" % (k, quoteattr(v)) for k, v in pares if v is not None)


# ---------------------------------------------------------------- estrutura (template, properties, condicoes, motion)

CHAVES_TEMPLATE = {"skillsubtype": "sub_type", "tslot": "target_slot", "dispel_category": "dispel_category",
                   "req_dispel_level": "required_dispel_level", "cancel_rate": "cancel_rate", "ammospeed": "ammo_speed",
                   "tslot_level": "target_slot_level", "conflict_id": "conflict_id",
                   "pvp_duration": "pvp_remain_time_ratio", "pvp_damage": "pvp_damage_ratio",
                   "chain_skill_prob": "chain_skill_prob2"}
CHAVES_PROPS = {
    "first_target": lambda c: norm(c.get("first_target")),
    "first_target_range": lambda c: (norm(c.get("first_target")), norm(c.get("first_target_valid_distance")), norm(c.get("sub_type"))),
    "target_relation": lambda c: norm(c.get("target_relation_restriction")),
    "target_type": lambda c: norm(c.get("target_range")),
    "target_maxcount": lambda c: (norm(c.get("target_range")), norm(c.get("target_maxcount"))),
    "target_distance": lambda c: norm(c.get("target_range_opt1")),
    "effective_angle": lambda c: norm(c.get("target_range_opt2")),
    "awr": lambda c: norm(c.get("add_wpn_range")),
    "target_species": lambda c: norm(c.get("target_species_restriction")),
    "revision_distance": lambda c: (norm(c.get("first_target_valid_distance")), castando(c)),
}
FALLBACK_PROPS = {
    "first_target_range": lambda c: inteiro(c.get("first_target_valid_distance")),
    "target_maxcount": lambda c: inteiro(c.get("target_maxcount")),
    "target_distance": lambda c: inteiro(c.get("target_range_opt1")),
    "effective_angle": lambda c: inteiro(c.get("target_range_opt2")),
    "awr": lambda c: "true" if c.get("add_wpn_range") == "1" else None,
}


class Estrutura:
    def __init__(self, gabarito, cli, skill_por_nome, motions):
        self.skill_por_nome = skill_por_nome
        self.motions = motions
        self.tmpl = {a: Tabela() for a in CHAVES_TEMPLATE}
        self.props = {a: Tabela() for a in CHAVES_PROPS}
        self.ordem_props = collections.Counter()
        self.instant = Tabela()
        self.alvo = Tabela()
        for sid, r, attrs in gabarito:
            c = cli[sid]
            for a, campo in CHAVES_TEMPLATE.items():
                self.tmpl[a].add(norm(c.get(campo)), attrs.get(a))
            p = r.find("properties")
            if p is not None:
                for a, fn in CHAVES_PROPS.items():
                    self.props[a].add(fn(c), p.get(a))
                for i, a in enumerate(p.attrib):
                    self.ordem_props[a] += i
            m = r.find("motion")
            self.instant.add((castando(c), norm(c.get("sub_type"))), m.get("instant_skill") if m is not None else None)
            s = r.find("startconditions")
            t = s.find("target") if s is not None else None
            self.alvo.add(norm(c.get("target_species_restriction")), t.get("value") if t is not None else None)

    def template(self, c, atual):
        novo = dict(atual)
        for a, campo in CHAVES_TEMPLATE.items():
            v = self.tmpl[a].get(norm(c.get(campo)), None)
            if v is not None:
                novo[a] = v
            elif a != "skillsubtype":
                novo.pop(a, None)
        pen = c.get("penalty_skill_succ")
        if pen and pen.lower() in self.skill_por_nome:
            novo["penalty_skill_id"] = self.skill_por_nome[pen.lower()]
        return novo

    def properties(self, c):
        valores = {}
        for a, fn in CHAVES_PROPS.items():
            padrao = FALLBACK_PROPS.get(a, lambda _c: None)(c)
            valores[a] = self.props[a].get(fn(c), padrao)
        if not valores.get("first_target"):
            valores["first_target"] = "TARGET"
        ordem = sorted(valores, key=lambda a: self.ordem_props.get(a, 99))
        return [(a, valores[a]) for a in ordem]

    def condicoes(self, c):
        sc, ac = [], []
        custo = (c.get("cost_parameter") or "").upper()
        fim = nz(c.get("cost_end"))
        delta = inteiro(c.get("cost_end_lv"))
        if custo == "MP" and fim:
            sc.append(("mp", [("value", fim), ("delta", delta or "0")]))
            ac.append(("mpuse", [("value", fim), ("delta", delta or "0")]))
        elif custo in ("HP", "HP_RATIO") and fim:
            par = [("value", fim), ("delta", delta), ("ratio", "true" if custo == "HP_RATIO" else None)]
            sc.append(("hp", par))
            ac.append(("hpuse", par))
        dp = nz(c.get("cost_dp"))
        if dp:
            sc.append(("dp", [("value", dp)]))
            ac.append(("dpuse", [("value", dp)]))
        sp = nz(c.get("cost_sp"))
        if sp:
            sc.append(("sp", [("value", sp)]))
            ac.append(("spuse", [("value", sp)]))
        alvo = self.alvo.get(norm(c.get("target_species_restriction")), None)
        if alvo:
            sc.append(("target", [("value", alvo)]))
        if c.get("self_flying_restriction"):
            sc.append(("selfflying", [("restriction", c["self_flying_restriction"].upper())]))
        if c.get("target_flying_restriction"):
            sc.append(("targetflying", [("restriction", c["target_flying_restriction"].upper())]))
        armas = [t for t, campo in ARMAS if c.get(campo) == "1"]
        if armas:
            sc.append(("weapon", [("weapon", " ".join(armas))]))
        cat = c.get("chain_category_name")
        if cat and (c.get("skill_category") == "SKILLCTG_CHAIN_SKILL" or c.get("prechain_category_name")):
            pre = c.get("prechain_category_name")
            sc.append(("chain", [("category", cat.upper()), ("precategory", pre.upper() if pre else None),
                                 ("time", inteiro(c.get("chain_time")) or "1000")]))
        uc = [] if c.get("move_casting") == "1" else [("playermove", [("allow", "false")])]
        return sc, uc, ac

    def motion(self, c):
        nome = c.get("motion_name")
        if not nome or nome.lower() not in self.motions:
            return None
        return [("name", nome), ("speed", inteiro(c.get("motion_play_speed"))),
                ("instant_skill", self.instant.get((castando(c), norm(c.get("sub_type"))), None))]


# ---------------------------------------------------------------- efeitos

def campos_efeito(c, n):
    d = {k.replace("effect%d_" % n, "effect_"): v for k, v in c.items() if k.startswith("effect%d_" % n)}
    d["_skill_name"] = c.get("name", "")
    return d


def tipos_do_cliente(c):
    return [(int(m.group(1)), c[k].lower()) for k in c for m in [re.fullmatch(r"effect(\d)_type", k)] if m]


def fontes_numericas(g, lookups):
    """todas as leituras numericas possiveis de um efeito do cliente: nome da fonte -> valor."""
    out = {}
    for k, v in g.items():
        if v in (None, ""):
            continue
        i = inteiro(v)
        if i is not None:
            out["id:" + k] = i
            out["neg:" + k] = str(-int(i))
        else:
            d = re.sub(r"\D", "", v)
            if d and v.lower().startswith("e"):
                out["e:" + k] = d
            s = lookups["skill"].get(v.lower())
            if s:
                out["skill:" + k] = s
            n = lookups["npc"].get(v.lower())
            if n:
                out["npc:" + k] = n
    r2, r4 = nz(g.get("effect_reserved2")), nz(g.get("effect_reserved4"))
    if r2 or r4:
        out["regra:r2_ou_r4"] = r2 or r4
        par = nz(g.get("effect_reserved1")) if r2 else nz(g.get("effect_reserved3"))
        if par:
            out["regra:delta_do_par"] = par
    r13 = g.get("effect_reserved13")
    if r13 == "1":
        out["regra:signet1_base"] = "8303"
    elif r13 == "2":
        out["regra:signet1_base"] = "8304"
    return out


class ModeloEfeito:
    def __init__(self, tag, instancias, lookups):
        """instancias: [(campos genericos do cliente, attrs do servidor sem e, [attrs dos <change>])]"""
        self.tag = tag
        self.lookups = lookups
        ordem = collections.Counter()
        vistos = collections.Counter()
        for _, a, _ in instancias:
            for i, k in enumerate(a):
                ordem[k] += i
                vistos[k] += 1
        self.ordem = sorted(vistos, key=lambda k: ordem[k] / vistos[k])
        self.regras = {}
        leituras = [fontes_numericas(g, lookups) for g, _, _ in instancias]
        for k in vistos:
            reais = [(g, sem_default(a).get(k)) for g, a, _ in instancias]
            valores = [v for _, v in reais if v is not None]
            if not valores:
                continue
            if all(re.fullmatch(r"-?\d+", v) for v in valores):
                self.regras[k] = self._numerico(k, reais, leituras)
            else:
                self.regras[k] = self._tabela(k, reais)
        self.com_change = tag in TAGS_STAT and sum(1 for _, _, ch in instancias if ch) > len(instancias) / 2
        if self.com_change:
            # stat por token do cliente (reserved13..15): a tupla inteira nao generaliza, cada token sim
            self.token = Tabela()
            self.sem_token = Tabela()
            for g, _, ch in instancias:
                toks = self._tokens(g)
                stats = tuple(x.get("stat") for x in ch)
                if len(toks) == 1:
                    self.token.add(toks[0], stats)
                elif not toks:
                    self.sem_token.add("", stats)
            for g, _, ch in instancias:  # token composto: o que sobra depois dos tokens ja conhecidos e do desconhecido
                toks = self._tokens(g)
                desconhecidos = [t for t in toks if not self.token.tem(t)]
                if len(toks) > 1 and len(desconhecidos) == 1:
                    conhecidos = {s for t in toks if self.token.tem(t) for s in self.token.get(t)}
                    resto = tuple(x.get("stat") for x in ch if x.get("stat") not in conhecidos)
                    if resto:
                        self.token.add(desconhecidos[0], resto)
            self.func = Tabela()
            self.func_stat = Tabela()
            self.func_r6 = Tabela()
            self.sinal = Tabela()
            for g, _, ch in instancias:
                r6 = norm(g.get("effect_reserved6"))
                toks = self._tokens(g)
                for x in ch:
                    i = self._indice_token(toks, x.get("stat"))
                    self.func.add((r6, x.get("stat"), self._origem(g, i)), x.get("func"))
                    self.func_stat.add((r6, x.get("stat")), x.get("func"))
                    self.func_r6.add(r6, x.get("func"))
                    base = self._base(g, i)
                    if base and x.get("value") and re.fullmatch(r"-?\d+", x.get("value")):
                        self.sinal.add(x.get("stat"), "-" if x["value"].startswith("-") != base.startswith("-") else "+")

    @staticmethod
    def _tokens(g):
        return [norm(g.get(k)) for k in ("effect_reserved13", "effect_reserved14", "effect_reserved15")
                if g.get(k) and not re.fullmatch(r"-?\d+(\.\d+)?", g.get(k).strip())]

    def _stats_do_token(self, token):
        return self.token.get(token, None) or stat_por_nome(token)

    def _indice_token(self, toks, stat):
        for i, t in enumerate(toks):
            if stat in (self._stats_do_token(t) or ()):
                return i
        return 0

    def _numerico(self, k, reais, leituras):
        """leitura do cliente que concorda com o gabarito E aparece quando o atributo aparece (noresist=1 e
        preeffect=1 concordam por acaso; so o cond_preeffect existe exatamente quando o preeffect existe)."""
        concorda = collections.Counter()
        presente = sum(1 for _, v in reais if v is not None)
        for (g, v), lidas in zip(reais, leituras):
            if v is None:
                continue
            for nome, lido in lidas.items():
                if lido == v:
                    concorda[nome] += 1
        if not concorda:
            return None
        topo = max(concorda.values())

        def presenca(fonte):
            ok = sum(1 for (_g, v), lidas in zip(reais, leituras)
                     if (lidas.get(fonte) is not None and sem_default({k: lidas[fonte]}) != {}) == (v is not None))
            return ok / len(reais)
        candidatos = [f for f, n in concorda.items() if n >= 0.5 * topo]
        fonte = max(candidatos, key=lambda f: (concorda[f] / presente + presenca(f), f.startswith("id:")))
        aparece = Tabela()
        for (_g, v), lidas in zip(reais, leituras):
            lido = lidas.get(fonte)
            aparece.add(lido is not None and sem_default({k: lido}) != {}, v is not None)
        return ("num", fonte, concorda[fonte] / presente, aparece)

    def _tabela(self, k, reais):
        """enum/booleano: campo do cliente de baixa cardinalidade cuja tabela mais acerta, medido em meia-amostra."""
        campos = collections.defaultdict(set)
        for g, _ in reais:
            for f, v in g.items():
                campos[f].add(norm(v))
        candidatos = [f for f, vs in campos.items() if len(vs) <= 40] + ["<nenhum>"]
        A, B = reais[0::2], reais[1::2]
        melhor = None
        for f in candidatos:
            tab = Tabela()
            for g, v in A:
                tab.add(norm(g.get(f)) if f != "<nenhum>" else "", v)
            ok = sum(1 for g, v in B if tab.get(norm(g.get(f)) if f != "<nenhum>" else "", None) == v)
            if melhor is None or ok > melhor[0]:
                melhor = (ok, f)
        f = melhor[1]
        tab = Tabela()
        for g, v in reais:
            tab.add(norm(g.get(f)) if f != "<nenhum>" else "", v)
        return ("tab", f, tab)

    @staticmethod
    def _base(g, i):
        """valor do grupo de stats do token i: reserved2 no 1o token, reserved4 nos demais (um cai no outro)."""
        r2, r4 = nz(g.get("effect_reserved2")), nz(g.get("effect_reserved4"))
        return (r2 or r4) if i == 0 else (r4 or r2)

    @staticmethod
    def _origem(g, i):
        """de qual reserved o valor do token i saiu: statboost usa reserved2 com ADD e reserved4 com PERCENT."""
        r2, r4 = nz(g.get("effect_reserved2")), nz(g.get("effect_reserved4"))
        if i == 0:
            return "r2" if r2 else "r4" if r4 else None
        return "r4" if r4 else "r2" if r2 else None

    def gera(self, g):
        attrs = {}
        lidas = fontes_numericas(g, self.lookups)
        for k, regra in self.regras.items():
            if regra is None:
                continue
            if regra[0] == "num":
                _, fonte, _acc, aparece = regra
                lido = lidas.get(fonte)
                if lido is not None and aparece.get(sem_default({k: lido}) != {}, True):
                    attrs[k] = lido
            else:
                _, f, tab = regra
                v = tab.get(norm(g.get(f)) if f != "<nenhum>" else "", None)
                if v is not None:
                    attrs[k] = v
        filhos = []
        if self.com_change:
            toks = self._tokens(g)
            grupos = []
            if toks:
                for i, t in enumerate(toks):
                    stats = self._stats_do_token(t)
                    if not stats:
                        return None
                    grupos.append((i, stats))
            else:
                stats = self.sem_token.get("", None)
                if not stats:
                    return None
                grupos.append((0, stats))
            r6 = norm(g.get("effect_reserved6"))
            vistos = set()
            for i, stats in grupos:
                base = self._base(g, i)
                if base is None:
                    return None
                origem = self._origem(g, i)
                for s in stats:
                    if s is None:
                        return None
                    if s in vistos:
                        continue
                    vistos.add(s)
                    valor = base if self.sinal.get(s, "+") == "+" else str(-int(base))
                    func = self.func.get((r6, s, origem), self.func_stat.get((r6, s), self.func_r6.get(r6, "ADD")))
                    filhos.append([("stat", s), ("func", func), ("value", valor), ("delta", nz(g.get("effect_reserved1")))])
        return attrs, filhos

    def xml(self, g, n, c=None):
        r = self.gera(g)
        if r is None:
            return None
        attrs, filhos = r
        pares = [(k, attrs[k]) for k in self.ordem if k in attrs]
        pos = next((i for i, (k, _) in enumerate(pares) if k not in ("duration1", "duration2", "effectid")), len(pares))
        pares.insert(pos, ("e", str(n)))
        return pares, filhos


class ModeloBlending:
    tag = "blending"

    def xml(self, g, n, c=None):
        name = (c.get("name") if c else g.get("_skill_name", "")).lower()
        if "blenda" in name or "bursta" in name:
            note = "A"
        elif "blendb" in name or "burstb" in name:
            note = "B"
        elif "blendc" in name or "burstc" in name:
            note = "C"
        elif "burste" in name:
            note = "SEAL"
        elif "blende" in name:
            note = "E"
        else:
            note = "A"
        pares = [("note", note), ("e", str(n))]
        return pares, []


def mede_efeito(modelo, g, el):
    """Compara um efeito gerado com o do gabarito, por componente (ver docstring do modulo)."""
    r = modelo.gera(g)
    if r is None:
        return {"enums": False, "stats": False, "presenca": False, "num_ok": 0, "num_tot": 0}
    attrs, filhos = r
    ger = sem_default(attrs)
    real = sem_default({k: v for k, v in el.attrib.items() if k != "e"})
    numerico = lambda v: re.fullmatch(r"-?\d+", v) is not None
    comuns = [k for k in real if k in ger]
    enums = all(ger[k] == real[k] for k in comuns if not numerico(real[k]))
    num_tot = sum(1 for k in comuns if numerico(real[k]))
    num_ok = sum(1 for k in comuns if numerico(real[k]) and ger[k] == real[k])
    reais = [x.attrib for x in el if x.tag == "change"]
    stats = True
    if modelo.com_change or reais:
        stats = ([f[0][1] for f in filhos] == [x.get("stat") for x in reais]
                 and all(dict(f)["func"] == x.get("func") for f, x in zip(filhos, reais)))
        if stats:
            num_tot += len(reais)
            num_ok += sum(1 for f, x in zip(filhos, reais) if dict(f)["value"] == x.get("value"))
    return {"enums": enums, "stats": stats, "presenca": set(ger) == set(real), "num_ok": num_ok, "num_tot": num_tot}


def obrigatorios_xsd(caminho_xsd):
    """elemento de efeito -> atributos use="required", somando os herdados do tipo base."""
    from lxml import etree
    xs = "{http://www.w3.org/2001/XMLSchema}"
    arvore = etree.parse(caminho_xsd)
    tipos = {}
    for ct in arvore.iter(xs + "complexType"):
        if ct.get("name"):
            ext = next(ct.iter(xs + "extension"), None)
            tipos[ct.get("name")] = ({a.get("name") for a in ct.iter(xs + "attribute") if a.get("use") == "required"},
                                     ext.get("base") if ext is not None else None)

    def todos(nome, vistos=()):
        if nome not in tipos or nome in vistos:
            return set()
        req, base = tipos[nome]
        return req | todos(base, vistos + (nome,))
    efeitos_ct = next(ct for ct in arvore.iter(xs + "complexType") if ct.get("name") == "Effects")
    return {e.get("name"): todos(e.get("type")) for e in efeitos_ct.iter(xs + "element")}


# ---------------------------------------------------------------- principal

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--ids", default="", help="so estes skill_id (lista separada por virgula); os outros stubs ficam como estao")
    ap.add_argument("--limiar", type=float, default=0.85, help="enums+stats")
    ap.add_argument("--limiar-presenca", type=float, default=0.70)
    ap.add_argument("--limiar-numeros", type=float, default=0.70)
    args = ap.parse_args()

    skills_xml = os.path.join(args.cliente, "data", "skills", "client_skills.xml")
    npcs_xml = os.path.join(args.cliente, "data", "npcs", "client_npcs.xml")
    if not os.path.isfile(skills_xml):
        sys.exit("Arquivo do cliente nao encontrado: " + skills_xml + ". Informe --cliente ou AION_CLIENT_XML_DIR.")

    print("1. Lendo client_skills, client_npcs, skill_templates, skill_tree e motion_times...")
    txt = open(skills_xml, encoding="utf-8", errors="replace").read()
    cli = {}
    for m in re.finditer(r"<skill_base_client>(.*?)</skill_base_client>", txt, re.S):
        d = {k: v.strip() for k, v in re.findall(r"<([a-z_0-9]+)>([^<]*)</\1>", m.group(1))}
        if d.get("id"):
            cli[d["id"]] = d
    lookups = {"skill": {c["name"].lower(): sid for sid, c in cli.items() if c.get("name")}, "npc": {}}
    for m in re.finditer(r"<npc_client>\s*<id>(\d+)</id>\s*<name>([^<]*)</name>", open(npcs_xml, encoding="utf-8", errors="replace").read()):
        lookups["npc"].setdefault(m.group(2).lower(), m.group(1))
    motions = {n.lower() for n in re.findall(r'<motion_time name="([^"]+)"', open(os.path.join(backup_manager.SERVER_DATA_DIR, REL_MOTION), encoding="utf-8").read())}
    caminho = os.path.join(backup_manager.SERVER_DATA_DIR, REL_XML)
    with open(caminho, encoding="utf-8", newline="") as f:
        text = f.read()
    blocos = {}
    for m in BLOCK_RE.finditer(text):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        blocos[a["skill_id"]] = (m.span(), a, m.group(3) or "")
    classes = collections.defaultdict(set)
    for m in re.finditer(r"<skill\b([^>]*)/>", open(os.path.join(backup_manager.SERVER_DATA_DIR, REL_TREE), encoding="utf-8").read()):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        classes[a.get("skillId")].add(a.get("classId"))

    gabarito, stubs = [], []
    for sid, (_span, a, inner) in blocos.items():
        c = cli.get(sid)
        if not c:
            continue
        if "<effects>" in inner and a.get("stack", "").upper() == c.get("name", "").upper():
            try:
                gabarito.append((sid, ET.fromstring("<r>" + inner + "</r>"), a))
            except ET.ParseError:
                pass
        elif tipos_do_cliente(c) and "<effects>" not in inner:
            stubs.append(sid)
    gabarito.sort(key=lambda x: int(x[0]))
    treino, teste = gabarito[0::2], gabarito[1::2]
    print("   gabarito: {} ({} treino / {} teste) | stubs: {}".format(len(gabarito), len(treino), len(teste), len(stubs)))

    def instancias_por_tipo(conjunto):
        por = collections.defaultdict(list)
        tags = collections.defaultdict(collections.Counter)
        for sid, r, _a in conjunto:
            c = cli[sid]
            eff = r.find("effects")
            for el in eff if eff is not None else []:
                n = el.get("e")
                t = c.get("effect%s_type" % n, "").lower() if n else ""
                if not t:
                    continue
                tags[t][el.tag] += 1
                por[(t, el.tag)].append((campos_efeito(c, int(n)), {k: v for k, v in el.attrib.items() if k != "e"},
                                         [dict(x.attrib) for x in el if x.tag == "change"], el))
        return por, tags

    print("2. Medindo cada peca na metade de teste...")
    E = Estrutura(treino, cli, lookups["skill"], motions)

    def conds(r, nome):
        s = r.find(nome)
        return sorted((x.tag, tuple(sorted(sem_default(dict(x.attrib)).items()))) for x in s) if s is not None else []

    def gerado(lista):
        return sorted((t, tuple(sorted(sem_default(dict(p)).items()))) for t, p in lista)

    ok = collections.Counter()
    for sid, r, _a in teste:
        c = cli[sid]
        p = r.find("properties")
        ok["properties"] += sem_default(dict(E.properties(c))) == sem_default(dict(p.attrib) if p is not None else {})
        sc, uc, ac = E.condicoes(c)
        ok["startconditions"] += gerado(sc) == conds(r, "startconditions")
        ok["useconditions"] += gerado(uc) == conds(r, "useconditions")
        ok["actions"] += gerado(ac) == conds(r, "actions")
        mo = E.motion(c)
        real = r.find("motion")
        ok["motion (nome)"] += (mo[0][1].lower() if mo else None) == (real.get("name", "").lower() if real is not None else None)
    n = len(teste)
    resumo_estrutura = " | ".join("{} {:.1f}%".format(k, 100 * v / n) for k, v in ok.items())
    print("   " + resumo_estrutura)

    por_treino, tags_treino = instancias_por_tipo(treino)
    por_teste, _ = instancias_por_tipo(teste)
    stub_tipos = collections.Counter(t for sid in stubs for _, t in tipos_do_cliente(cli[sid]))
    medicao = {}
    for t in stub_tipos:
        if not tags_treino.get(t):
            medicao[t] = (None, 0, 0.0, 0.0, 0.0)
            continue
        tag = tags_treino[t].most_common(1)[0][0]
        inst = [(g, a, ch) for g, a, ch, _el in por_treino[(t, tag)]]
        if len(inst) < 2:
            medicao[t] = (tag, 0, 0.0, 0.0, 0.0)
            continue
        modelo = ModeloEfeito(tag, inst, lookups)
        casos = por_teste.get((t, tag), [])
        est = pres = num_ok = num_tot = gerou = 0
        for g, _a, _ch, el in casos:
            # stat que o modelo nao conhece nao gera nada: a skill fica stub, entao nao e acerto nem erro -- e cobertura
            if modelo.gera(g) is None:
                continue
            gerou += 1
            m = mede_efeito(modelo, g, el)
            est += m["enums"] and m["stats"]
            pres += m["presenca"]
            num_ok += m["num_ok"]
            num_tot += m["num_tot"]
        # efeito que o gabarito escreve com outro elemento conta como falha em tudo
        total = gerou + round(sum(v for k, v in tags_treino[t].items() if k != tag) / 2)
        medicao[t] = (tag, total, est / total if total else 0.0, pres / total if total else 0.0,
                      num_ok / num_tot if num_tot else 1.0)

    EFEITOS_EXATOS = {"root", "carvesignet", "protect", "randommoveloc", "alwaysparry", "movebehindatk"}
    aprovados = {t for t, (tag, total, est, pres, num) in medicao.items()
                 if tag and total >= 2 and est >= args.limiar and (pres >= args.limiar_presenca or t in EFEITOS_EXATOS) and num >= args.limiar_numeros}
    aprovados.add("blending")
    print("   tipos de efeito dos stubs: {} | aprovados (enums+stats >= {:.0%}, presenca >= {:.0%}, numeros >= {:.0%}, n >= 2): {}".format(
        len(stub_tipos), args.limiar, args.limiar_presenca, args.limiar_numeros, len(aprovados)))

    print("3. Aprendendo no gabarito inteiro e gerando os stubs...")
    E = Estrutura(gabarito, cli, lookups["skill"], motions)
    por_todo, tags_todo = instancias_por_tipo(gabarito)
    modelos = {}
    for t in aprovados:
        if t == "blending":
            modelos[t] = ModeloBlending()
        elif tags_todo.get(t):
            tag = tags_todo[t].most_common(1)[0][0]
            modelos[t] = ModeloEfeito(tag, [(g, a, ch) for g, a, ch, _el in por_todo[(t, tag)]], lookups)

    def grupo_de(sid):
        cs = classes.get(sid, set())
        return "jogavel" if cs & CLASSES_JOGAVEIS else "ALL" if "ALL" in cs else "fora da arvore"

    obrigatorios = obrigatorios_xsd(os.path.join(backup_manager.SERVER_DATA_DIR, REL_XSD))
    edits, gerados, pulados = [], [], collections.Counter()
    so_ids = {x.strip() for x in args.ids.split(",") if x.strip()}
    for sid in sorted(stubs, key=int):
        if so_ids and sid not in so_ids:
            continue
        c = cli[sid]
        tipos = sorted(tipos_do_cliente(c))
        faltando = sorted({t for _, t in tipos if t not in modelos})
        if faltando:
            for t in faltando:
                pulados[t] += 1
            continue
        efeitos = []
        for num, t in tipos:
            r = modelos[t].xml(campos_efeito(c, num), num, c)
            if r is None:
                pulados[t + " (stat ou valor que o gabarito nao tem)"] += 1
                efeitos = None
                break
            sem = obrigatorios.get(modelos[t].tag, set()) - {k for k, _ in r[0]}
            if sem:
                pulados["{} (sem {} obrigatorio: nome sem id no cliente)".format(t, "/".join(sorted(sem)))] += 1
                efeitos = None
                break
            efeitos.append((modelos[t].tag, r))
        if efeitos is None:
            continue
        (ini, fim), atual, _inner = blocos[sid]
        linhas = ["\t<skill_template" + xml_attrs(E.template(c, atual).items()) + ">\n",
                  "\t\t<properties" + xml_attrs(E.properties(c)) + " />\n"]
        sc, uc, ac = E.condicoes(c)
        for nome, lista in (("startconditions", sc), ("useconditions", uc)):
            if lista:
                linhas.append("\t\t<%s>\n" % nome + "".join("\t\t\t<%s%s />\n" % (t, xml_attrs(p)) for t, p in lista) + "\t\t</%s>\n" % nome)
        linhas.append("\t\t<effects>\n")
        for tag, (attrs, filhos) in efeitos:
            if filhos:
                linhas.append("\t\t\t<%s%s>\n" % (tag, xml_attrs(attrs)))
                linhas.extend("\t\t\t\t<change%s />\n" % xml_attrs(f) for f in filhos)
                linhas.append("\t\t\t</%s>\n" % tag)
            else:
                linhas.append("\t\t\t<%s%s />\n" % (tag, xml_attrs(attrs)))
        linhas.append("\t\t</effects>\n")
        if ac:
            linhas.append("\t\t<actions>\n" + "".join("\t\t\t<%s%s />\n" % (t, xml_attrs(p)) for t, p in ac) + "\t\t</actions>\n")
        mo = E.motion(c)
        if mo:
            linhas.append("\t\t<motion" + xml_attrs(mo) + " />\n")
        linhas.append("\t</skill_template>")
        # Com a quebra do arquivo (CRLF): com LF no meio, os fix_50_* (que procuram os blocos pela
        # quebra do arquivo) nao achavam o <startconditions> e criavam outro antes do <properties>.
        eol = "\r\n" if "\r\n" in text[:4096] else "\n"
        edits.append((ini, fim, "".join(linhas).replace("\n", eol)))
        gerados.append((int(sid), c.get("name"), grupo_de(sid), [t for _, t in tipos]))

    por_grupo = collections.Counter(g for _, _, g, _ in gerados)
    total_grupo = collections.Counter(grupo_de(s) for s in stubs)
    resumo_grupos = "jogaveis {}/{} | ALL {}/{} | fora da arvore {}/{}".format(
        por_grupo["jogavel"], total_grupo["jogavel"], por_grupo["ALL"], total_grupo["ALL"],
        por_grupo["fora da arvore"], total_grupo["fora da arvore"])
    print("   {} de {} stubs ganham corpo | {}".format(len(gerados), len(stubs), resumo_grupos))

    out, pos = [], 0
    for a, b, novo in sorted(edits):
        out.append(text[pos:a])
        out.append(novo)
        pos = b
    out.append(text[pos:])
    novo_texto = "".join(out)

    print("4. Validando no XSD...")
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, REL_XSD)))
    if not schema.validate(etree.fromstring(novo_texto.encode("utf-8"))):
        for e in list(schema.error_log)[:25]:
            print("   XSD linha {}: {}".format(e.line, e.message))
        sys.exit("XSD invalido: nada foi gravado.")
    print("   XSD valido.")

    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("Corpo gerado para skill_templates vazios a partir do client_skills 5.0, medido no gabarito (metade de teste).\n\n")
        f.write("Estrutura: {}\n".format(resumo_estrutura))
        f.write("{} de {} stubs ganham corpo ({}).\n".format(len(gerados), len(stubs), resumo_grupos))
        f.write("Limiares por tipo de efeito: enums+stats >= {:.0%}, presenca >= {:.0%}, numeros >= {:.0%}.\n\n".format(
            args.limiar, args.limiar_presenca, args.limiar_numeros))
        f.write("{:34} {:22} {:>6} {:>12} {:>9} {:>8}  {}\n".format("tipo de efeito (cliente)", "elemento", "teste",
                                                                   "enums+stats", "presenca", "numeros", "usado"))
        for t, (tag, total, est, pres, num) in sorted(medicao.items(), key=lambda x: -stub_tipos[x[0]]):
            f.write("{:34} {:22} {:>6} {:>11.1%} {:>8.1%} {:>7.1%}  {} (stubs com esse tipo: {})\n".format(
                t, tag or "-", total, est, pres, num, "sim" if t in aprovados else "nao", stub_tipos[t]))
        f.write("\nStubs que continuam vazios, por tipo que faltou:\n")
        for t, k in pulados.most_common():
            f.write("  {:>5}  {}\n".format(k, t))
        f.write("\nSkills que ganharam corpo:\n")
        for sid, nome, grupo, tipos in sorted(gerados):
            f.write("  {:>6}  {:36} {:15} {}\n".format(sid, (nome or "")[:36], grupo, " ".join(tipos)))
    print("   relatorio: " + RELATORIO)

    if not args.aplicar:
        print("Sem --aplicar: nada foi gravado.")
        return
    backup_manager.backup_file_before_modification(REL_XML)
    for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
        p = os.path.join(base, REL_XML)
        with open(p, "wb") as f:
            f.write(novo_texto.encode("utf-8"))
        print("Gravado: " + p)


if __name__ == "__main__":
    main()
