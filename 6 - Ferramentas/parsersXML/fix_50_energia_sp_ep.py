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

Uso: python fix_50_energia_sp_ep.py [--dry]
"""
import os
import re
import sys
import collections
from xml.sax.saxutils import quoteattr

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
XMLS = r"G:\Projetos AION\XMLS AION CLASSIC\data"
TEMPLATES = os.path.join(RAIZ, "1 - Código Fonte [Emulador]", "game-server", "data", "static_data", "skills", "skill_templates.xml")

FEVER_ID = 3148
FLASH = (2943, 2706)
PREFIXOS_SP = ("TH_", "MO_", "EN_TH_")


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
        if pen.lower().startswith(("ex_sp_recover", "ep_recover")) and pen.lower() in por_nome:
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
