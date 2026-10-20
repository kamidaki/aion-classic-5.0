"""Efeitos das skills de ativação da sinergia de encantamento (activation_skill do client_accumulated_enchant_effect, nível 60+).

Em 18/10/2026 os templates estavam vazios, só com <properties>: Enchant_Effect_DRBoost_10/20 (3989/3990),
Enchant_Effect_DRBoost_50_APBoost_5 (3991) e Enchant_Effect_DRBoost_20_APBoost_1..4 (4218-4221). O cliente dá DRBoost e ApBoost
com reserved2 = porcentagem, que no servidor viram <drboost>/<apboost> com <change stat="DR_BOOST"/"AP_BOOST" func="PERCENT">, o
formato dos outros boosts de drop do skill_templates. As skills são passivas, sem duração.

Idempotente: só cria <effects> em template que não tem. Uso: python fix_50_enchant_synergy_skills.py [--dry] [skill_templates.xml ...]
"""
import re
import sys

from fix_50_energia_sp_ep import TEMPLATES, le_cliente

TIPOS = {"drboost": ("drboost", "DR_BOOST"), "apboost": ("apboost", "AP_BOOST")}


def efeitos(c, eol, ind):
    linhas = []
    for n in range(1, 5):
        tipo = c.get("effect%d_type" % n, "").lower()
        if tipo not in TIPOS:
            continue
        tag, stat = TIPOS[tipo]
        linhas.append('%s\t<%s e="%d" noresist="true">' % (ind, tag, n))
        linhas.append('%s\t\t<change stat="%s" func="PERCENT" value="%s"/>' % (ind, stat, c["effect%d_reserved2" % n]))
        linhas.append("%s\t</%s>" % (ind, tag))
    return eol.join(["%s<effects>" % ind] + linhas + ["%s</effects>" % ind])


def main():
    seco = "--dry" in sys.argv
    caminhos = [a for a in sys.argv[1:] if a != "--dry"] or [TEMPLATES]
    cli = le_cliente()
    alvo = {i: c for i, c in cli.items() if re.match(r"enchant_effect_drboost", c["name"].lower())}
    for caminho in caminhos:
        raw = open(caminho, encoding="utf-8", newline="").read()
        criados = []

        def edita(m):
            sid = int(m.group(2))
            if sid not in alvo or "<effects>" in m.group(3):
                return m.group(0)
            eol = "\r\n" if "\r\n" in m.group(3) else "\n"
            prop = re.search(r"([ \t]*)<properties\b[^>]*/>[ \t]*\r?\n", m.group(3))
            if not prop:
                return m.group(0)
            criados.append(sid)
            corpo = m.group(3)[:prop.end()] + efeitos(alvo[sid], eol, prop.group(1)) + eol + m.group(3)[prop.end():]
            return m.group(1) + corpo + m.group(4)

        novo = re.sub(r'(<skill_template skill_id="(\d+)"[^>]*>)(.*?)(</skill_template>)', edita, raw, flags=re.S)
        print(caminho, "criados:", criados or "nada a mudar")
        if novo != raw and not seco:
            with open(caminho, "w", encoding="utf-8", newline="") as f:
                f.write(novo)


if __name__ == "__main__":
    main()
