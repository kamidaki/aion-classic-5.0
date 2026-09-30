"""Corrige no skill_templates.xml o que a energia do Revenant (SP) e do Brawler (EP/Ki) precisa, a partir do client_skills 5.0.

Medido nas capturas oficiais de 2026-09-14 (Revenant nível 28 e Brawler nível 61, asmodianos):

  SP   ganho pelo penalty_skill_succ EX_SP_Recover_10/20/30 (SpHeal_Instant) e pela TH_ElectricCharge; custo pelo cost_sp
  EP   ganho pelo penalty_skill_succ EP_Recover_10..50 (ClassPointHeal_Instant, reserved3=EP); ao chegar a 100 entra o
       Fever_Check (3148, BoostContextSkill FeverCondition, 20 s), que libera as skills _high do client_context_skill_info
  MP   nenhuma skill de corrente MO_/TH_ cobrou MP; o cliente só cobra MP onde cost_parameter=MP
  flash ST_tele_G1 e ALL_teleport são MoveLocation (para a 1,6 m do alvo)

O que o script faz, sempre idempotente (rodar de novo não muda nada):

  1. <sphealinstant value=r2> nos stubs só com SpHeal e troca procsphealinstant/sphealinstant com valor errado
  2. <classpointhealinstant value=r2> nos stubs só com ClassPointHeal (EP_Recover_*, ST_recover, ST_SuperRecover)
  3. Fever_Check com <boostcontextskill> e tslot BUFF (o cliente só troca as skills se o ícone chegar no 0x31)
  4. <contextskill condition="FeverCondition"/> nas skills _high, que o oficial ignora em silêncio fora do Fever
  5. tira <mp>/<mpuse> das MO_/TH_ cujo cliente não cobra MP
  6. troca <skillatkdraininstant sp=...> (invenção do gerador 4.x) por <skillatk> onde o cliente tem SkillATK_Instant
  7. penalty_skill_id dos EX_SP_Recover/EP_Recover que faltam
  8. ST_tele_G1 e ALL_teleport com <movelocation> e properties do cliente
  9. buffs das skills _high (ST_upper_high_buff, ST_gigong_high_buff), BM_Reset_lowleg, ST_upperhit_sys e TH_ElectricBurst_sys:
     StatUp (stat pelo gabarito, r6/r7 = PERCENT do 1º/2º stat) e <skillcooltimereset> por Delay_ID (lista) ou
     Delay_ID_Range (faixa), com delta = reserved11 (100 zera). 5.0 oficial: o upper_high zerou jab e straight no 0x33,
     o lowleg_high zerou flyingkick, kickR, kickL e spinK_high, só as que estavam em recarga
 10. skills _high sem efeito (ST_gigong_high_G1..G5): copia a normal da mesma graduação e troca cadeia, target_maxcount,
     value/delta do ataque e acrescenta o <root> do cliente
 11. ST_flyingkick e ST_smallkick sem efeito (G1..G7 e _Start): <dash value=r4 delta=r3> e <root> do cliente, com cadeia,
     playermove e DEBUFF_PHYSICAL. 5.0 oficial: dash 2 no 0x2B, o Brawler para a 1,6 m do alvo

Uso: python fix_50_energia_sp_ep.py [--dry]
"""
import os
import re
import sys
import collections
from xml.sax.saxutils import quoteattr

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
XMLS = r"G:\Projetos AION\XMLS AION CLASSIC\data"
TEMPLATES = os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data", "skills", "skill_templates.xml")

FEVER_ID = 3148
FLASH = (2943, 2706)
PREFIXOS_SP = ("TH_", "MO_", "EN_TH_")
RESET_ALVOS = re.compile(r"^(ST_\w+_high_buff_G\d+|BM_Reset_\w+|ST_upperhit_sys|TH_ElectricBurst_sys)$", re.I)
TIPOS_RESET = {"statup", "skillcooltimereset", "spheal_instant"}


def aprende_tokens(cli, blocos):
    """token de stat do cliente -> StatEnum, pelos StatUp/StatDown/StatBoost do gabarito com um token e um <change> só."""
    tab = collections.defaultdict(collections.Counter)
    for i, c in cli.items():
        texto = blocos.get(i)
        if not texto or "<effects>" not in texto:
            continue
        for n, tipo in efeitos_cliente(c):
            if tipo.lower() not in ("statup", "statdown", "statboost"):
                continue
            toks = [c.get("effect%d_reserved%d" % (n, r), "") for r in (13, 14, 15)]
            toks = [x for x in toks if x and x != "0"]
            if len(toks) != 1:
                continue
            m = re.search(r'<(statup|statdown|statboost)\b[^>]*\be="%d".*?</\1>' % n, texto, re.S)
            if not m:
                continue
            stats = re.findall(r'<change stat="([A-Z_]+)"', m.group(0))
            if len(stats) == 1:
                tab[toks[0].lower()][stats[0]] += 1
    return {k: v.most_common(1)[0][0] for k, v in tab.items()}


def pre_efeito(c, n):
    if c.get("effect%d_cond_preeffect" % n, "").lower() == "e1":
        return ' preeffect="1" preeffect_prob="%s"' % (c.get("effect%d_cond_preeffect_prob2" % n) or "100")
    return ""


def gera_statup(c, n, tokens):
    changes = []
    for k, r in enumerate((13, 14, 15)):
        tok = c.get("effect%d_reserved%d" % (n, r), "")
        if not tok or tok == "0":
            continue
        stat = tokens.get(tok.lower())
        if not stat:
            return None
        valor = c.get("effect%d_reserved%d" % (n, 2 if k == 0 else 4), "0")
        pct = c.get("effect%d_reserved%d" % (n, 6 + k), "0") == "1"
        changes.append('<change stat="%s" func="%s" value="%s" />' % (stat, "PERCENT" if pct else "ADD", valor))
    if not changes:
        return None
    attrs = ' duration2="%s"' % c.get("effect%d_remain2" % n, "0")
    if c.get("effect%d_effectid" % n):
        attrs += ' effectid="%s"' % c["effect%d_effectid" % n]
    attrs += ' e="%d"' % n
    if c.get("effect%d_basiclv" % n, "0") != "0":
        attrs += ' basiclvl="%s"' % c["effect%d_basiclv" % n]
    attrs += ' noresist="true"' + pre_efeito(c, n)
    if c.get("effect%d_hop_type" % n, "").lower() == "skilllv":
        attrs += ' hoptype="SKILLLV" hopb="%s" hopa="%s"' % (c.get("effect%d_hop_b" % n, "0"), c.get("effect%d_hop_a" % n, "0"))
    return ["<statup%s>" % attrs] + ["\t" + x for x in changes] + ["</statup>"]


def gera_reset(c, n):
    tipo = c.get("effect%d_reserved1" % n, "").lower()
    if tipo == "delay_id":
        ids = [c.get("effect%d_reserved%d" % (n, r), "") for r in range(2, 9)]
        alvo = 'delay_ids="%s"' % " ".join(x for x in ids if x and x != "0")
    elif tipo == "delay_id_range":
        alvo = 'first_cd="%s" last_cd="%s"' % (c.get("effect%d_reserved2" % n), c.get("effect%d_reserved3" % n))
    else:
        return None
    return ['<skillcooltimereset %s delta="%s" e="%d" noresist="true"%s />' % (alvo, c.get("effect%d_reserved11" % n) or "100", n, pre_efeito(c, n))]


ELEMENTOS = {"air": "WIND", "water": "WATER", "fire": "FIRE", "earth": "EARTH", "light": "LIGHT", "dark": "DARK"}


def linha_root(c, n):
    """Root do cliente -> <root>, no formato que o gabarito usa (FI_KneeCrash, FI_AnkleGrab)."""
    s = '<root duration2="%s" effectid="%s" e="%d"' % (c.get("effect%d_remain2" % n, "0"), c.get("effect%d_effectid" % n, "0"), n)
    if c.get("effect%d_acc_mod2" % n):
        s += ' accmod2="%s"' % c["effect%d_acc_mod2" % n]
    if c.get("effect%d_critical_prob_mod2" % n):
        s += ' critprobmod2="%s"' % c["effect%d_critical_prob_mod2" % n]
    elem = ELEMENTOS.get(c.get("effect%d_reserved10" % n, "").lower())
    if elem:
        s += ' element="%s"' % elem
    s += pre_efeito(c, n)
    if c.get("effect%d_hop_type" % n, "").lower() == "skilllv" and c.get("effect%d_hop_b" % n, "0") != "0":
        s += ' hoptype="SKILLLV" hopb="%s"' % c["effect%d_hop_b" % n]
    return s + " />"


def linha_dash(c, n):
    """DashATK do cliente -> <dash>: value = r4, delta = r3 (gabarito FI_JumpAttack, AS_DashAttack, AS_SpiralStab)."""
    s = '<dash value="%s" delta="%s" e="%d"' % (c.get("effect%d_reserved4" % n, "0"), c.get("effect%d_reserved3" % n, "0"), n)
    if c.get("effect%d_noresist" % n) == "1":
        s += ' noresist="true"'
    if c.get("effect%d_critical_prob_mod2" % n):
        s += ' critprobmod2="%s"' % c["effect%d_critical_prob_mod2" % n]
    if c.get("effect%d_hop_type" % n, "").lower() == "damage":
        s += ' hoptype="DAMAGE"'
    return s + " />"


def motions_do_servidor():
    caminho = os.path.join(os.path.dirname(TEMPLATES), "motion_times.xml")
    if not os.path.isfile(caminho):
        return set()
    return {n.lower(): n for n in re.findall(r'<motion_time name="([^"]+)"', open(caminho, encoding="utf-8", errors="replace").read())}


def le_cliente():
    t = open(os.path.join(XMLS, "skills", "client_skills.xml"), encoding="utf-8", errors="replace").read()
    cli = {}
    for b in t.split("<skill_base_client>")[1:]:
        d = dict(re.findall(r"<([a-z_0-9]+)>([^<]*)</\1>", b))
        if "id" in d:
            cli[int(d["id"])] = d
    return cli


def efeitos_cliente(c):
    return [(int(n), c["effect%s_type" % n]) for n in sorted({k.split("_")[0][6:] for k in c if re.fullmatch(r"effect\d+_type", k)}, key=int)]


def contexto_fever(por_nome):
    t = open(os.path.join(XMLS, "PC", "client_context_skill_info.xml"), encoding="utf-8", errors="replace").read()
    ids = set()
    for m in re.finditer(r"<context_skill>([^<]+)</context_skill>\s*<context_skill_condition>FeverCondition</context_skill_condition>", t):
        i = por_nome.get(m.group(1).lower())
        if i:
            ids.add(i)
    return ids


class Template:
    """Um <skill_template> do arquivo, editado como texto para não mexer no resto do XML."""

    def __init__(self, cabeca, corpo, eol):
        self.cabeca = cabeca
        self.corpo = corpo
        self.eol = eol

    def tem_efeitos(self):
        return "<effects>" in self.corpo

    def attr(self, nome, valor):
        if re.search(r'\s%s="[^"]*"' % nome, self.cabeca):
            self.cabeca = re.sub(r'(\s%s=)"[^"]*"' % nome, r'\1"%s"' % valor, self.cabeca)
        else:
            self.cabeca = self.cabeca[:-1] + ' %s="%s">' % (nome, valor)

    def get_attr(self, nome):
        m = re.search(r'\s%s="([^"]*)"' % nome, self.cabeca)
        return m.group(1) if m else None

    def bloco(self, nome):
        return re.search(r"(\t\t<%s>)(.*?)(\t\t</%s>%s)" % (nome, nome, re.escape(self.eol)), self.corpo, re.S)

    def poe_no_bloco(self, nome, linha, depois_de=("properties",)):
        """Acrescenta uma linha dentro de <nome>, criando o bloco depois do primeiro irmão que existir."""
        b = self.bloco(nome)
        if b:
            self.corpo = self.corpo[:b.end(2)] + "\t\t\t" + linha + self.eol + self.corpo[b.end(2):]
            return
        novo = "\t\t<%s>%s\t\t\t%s%s\t\t</%s>%s" % (nome, self.eol, linha, self.eol, nome, self.eol)
        for irmao in depois_de:
            # o irmão inteiro: <x .../> numa linha ou <x>...</x>; parar no primeiro "/>" caía dentro de <useconditions><playermove/></useconditions>
            e = re.escape(self.eol)
            m = (re.search(r"\t\t<%s\b[^>\n]*/>%s" % (irmao, e), self.corpo)
                 or re.search(r"\t\t<%s>.*?\t\t</%s>%s" % (irmao, irmao, e), self.corpo, re.S))
            if m:
                self.corpo = self.corpo[:m.end()] + novo + self.corpo[m.end():]
                return
        self.corpo = self.eol + novo + self.corpo.lstrip("\r\n")

    def tira_linhas(self, padrao):
        antes = self.corpo
        self.corpo = re.sub(r"\t+%s[^\n]*\n" % padrao, "", self.corpo)
        for nome in ("startconditions", "actions"):
            self.corpo = re.sub(r"\t\t<%s>%s\t\t</%s>%s" % (nome, re.escape(self.eol), nome, re.escape(self.eol)), "", self.corpo)
        return antes != self.corpo

    def texto(self):
        return self.cabeca + self.corpo


def main():
    seco = "--dry" in sys.argv
    cli = le_cliente()
    por_nome = {d["name"].lower(): i for i, d in cli.items()}
    fever_ctx = contexto_fever(por_nome)

    raw = open(TEMPLATES, encoding="utf-8", newline="").read()
    eol = "\r\n" if "\r\n" in raw[:5000] else "\n"
    blocos = {int(m.group(1)): m.group(0) for m in re.finditer(r'<skill_template skill_id="(\d+)".*?</skill_template>', raw, re.S)}
    tokens = aprende_tokens(cli, blocos)
    contagem = collections.Counter()
    exemplos = collections.defaultdict(list)

    def edita(m):
        sid = int(m.group(2))
        c = cli.get(sid)
        if c is None:
            return m.group(0)
        tp = Template(m.group(1), m.group(3), eol)
        nome = c.get("name", "")
        efs = efeitos_cliente(c)
        tipos = [t.lower() for _, t in efs]
        original = tp.texto()

        # 1. SP heal
        if tipos and tipos[0] == "spheal_instant":
            r2 = c.get("effect1_reserved2", "0")
            achado = re.search(r"<(proc)?sphealinstant\b[^>]*/>", tp.corpo)
            linha = '<sphealinstant value="%s" e="1" noresist="true" />' % r2
            if achado and achado.group(0) != linha:
                tp.corpo = tp.corpo.replace(achado.group(0), linha)
                contagem["1 sphealinstant corrigido"] += 1
                exemplos["1"].append(sid)
            elif not tp.tem_efeitos() and tipos == ["spheal_instant"]:
                tp.poe_no_bloco("effects", linha, ("actions", "useconditions", "startconditions", "properties"))
                contagem["1 sphealinstant em stub"] += 1
                exemplos["1"].append(sid)

        # 2. ClassPointHeal (EP)
        if tipos == ["classpointheal_instant"] and c.get("effect1_reserved3", "").upper() == "EP" and not tp.tem_efeitos():
            tp.poe_no_bloco("effects", '<classpointhealinstant value="%s" e="1" noresist="true" />' % c.get("effect1_reserved2", "0"),
                            ("actions", "useconditions", "startconditions", "properties"))
            if c.get("first_target", "").lower() == "me" and '<properties first_target="TARGET" />' in tp.corpo:
                tp.corpo = tp.corpo.replace('<properties first_target="TARGET" />',
                                            '<properties first_target="ME" first_target_range="1" target_relation="FRIEND" target_type="ONLYONE" />')
            contagem["2 classpointhealinstant"] += 1
            exemplos["2"].append(sid)

        # 3. Fever
        if sid == FEVER_ID and not tp.tem_efeitos() and tipos == ["boostcontextskill"]:
            tp.poe_no_bloco("effects", '<boostcontextskill duration2="%s" condition=%s e="1" noresist="true" />'
                            % (c.get("effect1_remain2", "20000"), quoteattr(c.get("effect1_reserved3", "FeverCondition"))),
                            ("actions", "useconditions", "startconditions", "properties"))
            tp.attr("tslot", "BUFF")
            contagem["3 fever"] += 1

        # 9. buffs e reset de recarga das skills _high (e dos _sys de reset)
        if RESET_ALVOS.match(nome) and not tp.tem_efeitos() and "skillcooltimereset" in tipos and set(tipos) <= TIPOS_RESET:
            linhas = []
            for n, tipo in efs:
                t = tipo.lower()
                if t == "statup":
                    gerado = gera_statup(c, n, tokens)
                elif t == "skillcooltimereset":
                    gerado = gera_reset(c, n)
                else:
                    gerado = ['<sphealinstant value="%s" e="%d" noresist="true"%s />' % (c.get("effect%d_reserved2" % n, "0"), n, pre_efeito(c, n))]
                if gerado is None:
                    linhas = None
                    break
                linhas += gerado
            if linhas is None:
                contagem["9 sem gerar (token ou reserved desconhecido)"] += 1
                exemplos["9 sem gerar"].append(sid)
            else:
                bloco = "\t\t<effects>" + eol + "".join("\t\t\t" + x + eol for x in linhas) + "\t\t</effects>" + eol
                props = re.search(r"\t\t<properties\b[^>\n]*/>" + re.escape(eol), tp.corpo)
                if "statup" in tipos:
                    tp.attr("tslot", "BUFF")
                    tp.attr("skillsubtype", "BUFF")
                    if c.get("dispel_category", "").lower() == "buff":
                        tp.attr("dispel_category", "BUFF")
                    if props and props.group(0).strip() == '<properties first_target="TARGET" />':
                        novo_p = '\t\t<properties first_target="TARGET" first_target_range="1" target_relation="FRIEND" target_type="ONLYONE" />' + eol
                        tp.corpo = tp.corpo.replace(props.group(0), novo_p)
                        props = re.search(r"\t\t<properties\b[^>\n]*/>" + re.escape(eol), tp.corpo)
                if props:
                    tp.corpo = tp.corpo[:props.end()] + bloco + tp.corpo[props.end():]
                else:
                    tp.corpo = eol + bloco + tp.corpo.lstrip("\r\n")
                contagem["9 buff/reset"] += 1
                exemplos["9"].append(sid)

        # 10. skill _high sem efeito: copia a normal da mesma graduação (ST_gigong_G5 -> ST_gigong_high_G5) com os valores do cliente
        alta = re.match(r"^(ST_\w+)_high_(G\d+)$", nome)
        modelo_id = por_nome.get(("%s_%s" % alta.groups()).lower()) if alta else None
        if modelo_id and not tp.tem_efeitos() and "<effects>" in blocos.get(modelo_id, ""):
            mc = cli[modelo_id]
            tipos_m = [t.lower() for _, t in efeitos_cliente(mc)]
            extra = tipos[len(tipos_m):]
            if tipos[:len(tipos_m)] == tipos_m and extra in ([], ["root"]):
                m_modelo = re.match(r'(<skill_template skill_id="\d+"[^>]*>)(.*)</skill_template>', blocos[modelo_id], re.S)
                cab_m, corpo = m_modelo.group(1), m_modelo.group(2)
                for a in ("skilltype", "skillsubtype", "tslot", "cancel_rate", "chain_skill_prob"):
                    v = re.search(r'\s%s="([^"]*)"' % a, cab_m)
                    if v:
                        tp.attr(a, v.group(1))
                if c.get("target_maxcount"):
                    corpo = re.sub(r'target_maxcount="\d+"', 'target_maxcount="%s"' % c["target_maxcount"], corpo)
                cat, pre = c.get("chain_category_name", ""), c.get("prechain_category_name", "")
                if cat:
                    corpo = re.sub(r'(<chain category=)"[^"]*"', r'\1"%s"' % cat.upper(), corpo)
                if pre:
                    corpo = re.sub(r'(precategory=)"[^"]*"', r'\1"%s"' % pre.upper(), corpo)
                # primeiro efeito: mesmo elemento do modelo, value/delta do cliente (spellatkinstant: value=r2, delta=r1; skillatk: value=r4, delta=r3)
                t1 = tipos[0]
                val, dlt = (c.get("effect1_reserved2"), c.get("effect1_reserved1")) if t1.startswith("spellatk") else (c.get("effect1_reserved4"), c.get("effect1_reserved3"))
                ef1 = re.search(r'\t\t\t<\w+[^>]*\be="1"[^>]*/>', corpo)
                if ef1 and val:
                    linha = re.sub(r'\bvalue="\d+"', 'value="%s"' % val, ef1.group(0))
                    linha = re.sub(r'\bdelta="\d+"', 'delta="%s"' % (dlt or "0"), linha)
                    corpo = corpo.replace(ef1.group(0), linha)
                if extra == ["root"]:
                    n = len(tipos_m) + 1
                    corpo = corpo.replace("\t\t</effects>", "\t\t\t" + linha_root(c, n) + eol + "\t\t</effects>", 1)
                    if c.get("target_slot", "").lower() == "debuff":
                        tp.attr("tslot", "DEBUFF")
                    if c.get("dispel_category", "").lower() == "debuffphy":
                        tp.attr("dispel_category", "DEBUFF_PHYSICAL")
                        tp.attr("req_dispel_level", c.get("required_dispel_level") or "1")
                # a condição de contexto do stub vai de novo pelo passo 4
                tp.corpo = corpo
                contagem["10 _high a partir da normal"] += 1
                exemplos["10"].append(sid)

        # 11. ST_flyingkick / ST_smallkick sem efeito: DashATK + Root do cliente. 5.0 oficial: dash 2 no 0x2B e o Brawler para a 1,6 m do alvo
        if re.match(r"^ST_(flyingkick|smallkick)(_Start)?_G\d+$", nome) and not tp.tem_efeitos() and tipos == ["dashatk", "root"]:
            props = '<properties first_target="TARGET"%s first_target_range="%s" target_relation="ENEMY" target_type="ONLYONE" />' % (
                ' awr="true"' if c.get("add_wpn_range") == "1" else "", c.get("first_target_valid_distance", "20"))
            corpo = eol + "\t\t" + props + eol
            cat = c.get("chain_category_name")
            if cat and c.get("skill_category") == "SKILLCTG_CHAIN_SKILL":
                pre = c.get("prechain_category_name")
                corpo += "\t\t<startconditions>" + eol + '\t\t\t<chain category="%s"%s time="%s" />' % (
                    cat.upper(), ' precategory="%s"' % pre.upper() if pre else "", c.get("chain_time") or "1000") + eol + "\t\t</startconditions>" + eol
            if c.get("move_casting") != "1":
                corpo += "\t\t<useconditions>" + eol + '\t\t\t<playermove allow="false" />' + eol + "\t\t</useconditions>" + eol
            corpo += "\t\t<effects>" + eol + "\t\t\t" + linha_dash(c, 1) + eol + "\t\t\t" + linha_root(c, 2) + eol + "\t\t</effects>" + eol
            motion = motions_do_servidor().get(c.get("motion_name", "").lower())
            if motion:
                corpo += '\t\t<motion name="%s" />' % motion + eol
            tp.corpo = corpo + "\t"
            tp.attr("skilltype", c.get("type", "Physical").upper())
            tp.attr("skillsubtype", "ATTACK")
            tp.attr("tslot", "DEBUFF")
            tp.attr("dispel_category", "DEBUFF_PHYSICAL")
            tp.attr("req_dispel_level", c.get("required_dispel_level") or "1")
            tp.attr("cancel_rate", c.get("cancel_rate") or "10")
            if c.get("chain_skill_prob2"):
                tp.attr("chain_skill_prob", c["chain_skill_prob2"])
            contagem["11 kick (dash + root)"] += 1
            exemplos["11"].append(sid)

        # 4. skill de contexto do Fever
        if sid in fever_ctx and 'contextskill condition="FeverCondition"' not in tp.corpo:
            tp.poe_no_bloco("startconditions", '<contextskill condition="FeverCondition" />')
            contagem["4 contextskill"] += 1
            exemplos["4"].append(sid)

        if nome.startswith(PREFIXOS_SP):
            # 5. MP que o cliente não cobra
            if (c.get("cost_parameter") or "").upper() != "MP" and ("<mp " in tp.corpo or "<mpuse " in tp.corpo):
                tp.tira_linhas(r"<mp ")
                tp.tira_linhas(r"<mpuse ")
                contagem["5 mp retirado"] += 1
                exemplos["5"].append(sid)
            # 6. dreno inventado
            for dreno in re.finditer(r'<skillatkdraininstant sp="\d+"([^>]*?)(/?)>', tp.corpo):
                e = re.search(r'\be="(\d+)"', dreno.group(1))
                n = int(e.group(1)) if e else 1
                tipo_cli = dict(efs).get(n, "").lower()
                if tipo_cli == "skillatk_instant" and "hp_percent" not in dreno.group(1) and "mp_percent" not in dreno.group(1):
                    tp.corpo = tp.corpo.replace(dreno.group(0), "<skillatk%s%s>" % (dreno.group(1), dreno.group(2)), 1)
                    tp.corpo = tp.corpo.replace("</skillatkdraininstant>", "</skillatk>", 1)
                    contagem["6 dreno -> skillatk"] += 1
                    exemplos["6"].append(sid)

        # 7. penalty de SP/EP
        pen = c.get("penalty_skill_succ", "")
        if (pen.lower().startswith(("ex_sp_recover", "ep_recover")) or RESET_ALVOS.match(pen)) and pen.lower() in por_nome:
            quer = str(por_nome[pen.lower()])
            if tp.get_attr("penalty_skill_id") != quer:
                tp.attr("penalty_skill_id", quer)
                contagem["7 penalty"] += 1
                exemplos["7"].append(sid)

        # 8. flash
        if sid in FLASH and not tp.tem_efeitos() and tipos == ["movelocation"]:
            rel = {"enemy": "ENEMY", "friend": "FRIEND"}.get(c.get("target_relation_restriction", "").lower(), "ALL")
            props = '<properties first_target="TARGET" first_target_range="%s" target_relation="%s" target_type="ONLYONE" />' % (
                c.get("first_target_valid_distance", "20"), rel)
            tp.corpo = tp.corpo.replace('<properties first_target="TARGET" />', props)
            if (c.get("cost_parameter") or "").upper() == "MP" and c.get("cost_end"):
                tp.poe_no_bloco("startconditions", '<mp value="%s" delta="0" />' % c["cost_end"])
                tp.poe_no_bloco("actions", '<mpuse value="%s" delta="0" />' % c["cost_end"], ("effects", "useconditions", "startconditions", "properties"))
            tp.poe_no_bloco("effects", '<movelocation distance="%s" e="1" noresist="true" />' % c.get("effect1_reserved2", "20"),
                            ("useconditions", "startconditions", "properties"))
            if "<actions>" in tp.corpo and tp.corpo.index("<actions>") < tp.corpo.index("<effects>"):
                a = tp.bloco("actions")
                bloco_a = tp.corpo[a.start():a.end()]
                tp.corpo = tp.corpo.replace(bloco_a, "")
                ef = tp.bloco("effects")
                tp.corpo = tp.corpo[:ef.end()] + bloco_a + tp.corpo[ef.end():]
            if "<motion" not in tp.corpo and c.get("instant_skill") == "1":
                tp.corpo = tp.corpo.rstrip("\t") + "\t\t<motion instant_skill=\"true\" />" + eol + "\t"
            contagem["8 flash"] += 1
            exemplos["8"].append(sid)

        return tp.texto() + m.group(4) if tp.texto() != original else m.group(0)

    novo = re.sub(r'(\t<skill_template skill_id="(\d+)"[^>]*>)(.*?)(</skill_template>)', edita, raw, flags=re.S)
    for k in sorted(contagem):
        print("%-34s %5d" % (k, contagem[k]))
    for k in sorted(exemplos):
        print("   ", k, exemplos[k][:20], "..." if len(exemplos[k]) > 20 else "")
    if novo == raw:
        print("nada a mudar")
        return
    if seco:
        print("--dry: nada gravado")
        return
    with open(TEMPLATES, "w", encoding="utf-8", newline="") as f:
        f.write(novo)
    print("gravado", TEMPLATES)


if __name__ == "__main__":
    main()
