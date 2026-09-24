"""RandomMoveLoc 5.0 no skill_templates.xml: reserved5, direção e os efeitos que acompanham a RB_OblivionDash, a partir do client_skills.

Medido em 2026-09-14 na captura do Poeta (Soul Reaper nível 5, 4 usos da RB_OblivionDash_G1): o 0x2B oficial traz dash 8, o heading e o destino a
10,00 m exatos na direção do heading, e a skill sai duas vezes seguidas (passo de multicast 1 e 2). O cliente marca essa skill com reserved5 = 2.
LU_FrontDash/BackDash e RB_Oblivion_Dash_Start têm reserved5 = 1 (dash 6 no RandomMoveLocEffect). O gerador não levava o reserved5 e o servidor
mandava dash 1.

Gabarito do reserved3 nos templates herdados da 4.8 (1424, 1463, 1544, 1545, 2278, 2534): 1 = frente (direction 0), 2 = trás (direction 1).

O script, idempotente (rodar de novo não muda nada):
  1. reserved5 no <randommoveloc> onde o cliente tem 1 ou 2
  2. direction="1" onde o cliente tem reserved3 = 2 e o template não diz a direção
  3. nas skills com RandomMoveLoc, <dispel dispeltype="EFFECTTYPE"/> sem <effecttype> ganha os tipos do cliente (reserved2..9)
  4. nas skills com RandomMoveLoc, o <statup> de speed/arRoot/arSnare no formato do cliente: (token, valor, percent) em
     (r13, r2, r6), (r14, r4, r7) e (r18, r16, r17). O gerador tinha deixado ROOT_RESISTANCE PERCENT 1000 e nenhum SNARE_RESISTANCE

Uso: python fix_50_randommoveloc.py [--dry]
"""
import collections
import os
import re
import sys

from fix_50_energia_sp_ep import TEMPLATES, le_cliente

EFFECT_TYPE_JAVA = os.path.join(os.path.dirname(TEMPLATES), "..", "..", "..", "src", "com", "aionemu", "gameserver", "skillengine", "effect", "EffectType.java")
TOKENS = {"speed": "SPEED", "arroot": "ROOT_RESISTANCE", "arsnare": "SNARE_RESISTANCE"}
TRIOS = ((13, 2, 6), (14, 4, 7), (18, 16, 17))


def tipos_de_efeito():
    return set(re.findall(r"^\s*([A-Z_0-9]+),", open(EFFECT_TYPE_JAVA, encoding="utf-8").read(), re.M))


def main():
    seco = "--dry" in sys.argv
    cli = le_cliente()
    validos = tipos_de_efeito()
    raw = open(TEMPLATES, encoding="utf-8", newline="").read()
    eol = "\r\n" if "\r\n" in raw[:5000] else "\n"
    contagem = collections.Counter()
    exemplos = collections.defaultdict(list)

    def edita(m):
        sid = int(m.group(2))
        c = cli.get(sid)
        texto = m.group(0)
        if c is None:
            return texto
        efs = {n: c.get("effect%d_type" % n, "").lower() for n in range(1, 5)}
        if "randommoveloc" not in efs.values():
            return texto

        for n, tipo in efs.items():
            if tipo == "randommoveloc":
                tag = re.search(r'<randommoveloc\b[^>]*\be="%d"[^>]*/>' % n, texto)
                if not tag:
                    continue
                novo = tag.group(0)
                r5 = c.get("effect%d_reserved5" % n, "")
                if r5 in ("1", "2") and 'reserved5="%s"' % r5 not in novo:
                    novo = re.sub(r'\s+reserved5="[^"]*"', "", novo).replace(" />", ' reserved5="%s" />' % r5)
                    contagem["1 reserved5"] += 1
                    exemplos["1"].append(sid)
                if c.get("effect%d_reserved3" % n) == "2" and "direction=" not in novo:
                    novo = novo.replace("<randommoveloc ", '<randommoveloc direction="1" ', 1)
                    contagem["2 direction de ré"] += 1
                    exemplos["2"].append(sid)
                texto = texto.replace(tag.group(0), novo, 1)

            elif tipo == "dispel" and c.get("effect%d_reserved1" % n, "").lower() == "effect_type":
                alvos = [c.get("effect%d_reserved%d" % (n, r), "").upper() for r in range(2, 10)]
                alvos = [x for x in alvos if x and x != "0"]
                if not alvos or any(x not in validos for x in alvos):
                    continue
                for d in re.finditer(r"([ \t]*)<dispel\b([^>]*?)\s*/>", texto):
                    if 'e="%d"' % n in d.group(2) and 'dispeltype="EFFECTTYPE"' in d.group(2):
                        ind = d.group(1)
                        filhos = "".join("%s\t<effecttype>%s</effecttype>%s" % (ind, x, eol) for x in alvos)
                        texto = texto.replace(d.group(0), "%s<dispel%s>%s%s%s</dispel>" % (ind, d.group(2), eol, filhos, ind), 1)
                        contagem["3 dispel com tipos"] += 1
                        exemplos["3"].append(sid)
                        break

            elif tipo == "statup":
                trios = [(c.get("effect%d_reserved%d" % (n, t), ""), c.get("effect%d_reserved%d" % (n, v), "0"), c.get("effect%d_reserved%d" % (n, p), "0"))
                         for t, v, p in TRIOS]
                trios = [x for x in trios if x[0] and x[0] != "0"]
                if not trios or any(x[0].lower() not in TOKENS for x in trios):
                    continue
                bloco = re.search(r'([ \t]*)<statup\b([^>]*\be="%d"[^>]*)>(.*?)</statup>' % n, texto, re.S)
                if not bloco:
                    continue
                ind = bloco.group(1)
                changes = ['<change stat="%s" func="%s" value="%s" />' % (TOKENS[t.lower()], "PERCENT" if p == "1" else "ADD", v) for t, v, p in trios]
                novo = "%s<statup%s>%s" % (ind, bloco.group(2), eol) + "".join("%s\t%s%s" % (ind, x, eol) for x in changes) + ind + "</statup>"
                if novo != bloco.group(0):
                    texto = texto.replace(bloco.group(0), novo, 1)
                    contagem["4 statup speed/arRoot/arSnare"] += 1
                    exemplos["4"].append(sid)
        return texto

    novo = re.sub(r'(<skill_template skill_id="(\d+)"[^>]*>)(.*?)(</skill_template>)', edita, raw, flags=re.S)
    for k in sorted(contagem):
        print("%-34s %5d   %s" % (k, contagem[k], exemplos[k.split()[0]]))
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
