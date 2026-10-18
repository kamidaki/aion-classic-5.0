"""alter="true" no <chain> das skills com alterchain_use = 1 no client_skills 5.0.

Tooltip do cliente: "Chain Skill ... After using you can use another individual skill". Nessas cadeias, usar uma skill sem
cadeia no meio não quebra a sequência. Nas capturas oficiais (18/10/2026, 775 usos em cadeia), os 13 casos com outra skill
entre as duas eram todos de famílias alterchain: Gu_SoulBreakCannon entre En_DoubleFireChain e En_EnFireChain, ST_speed e
ST_attack entre ST_kickR e ST_kickL, ST_smallkick entre ST_sigpunch1 e ST_sigpunch2. O emulador resetava a cadeia em todo
cast sem <chain>.

A flag é uniforme em cada família (201 skills ativas com 1, 360 sem). O script só mexe no atributo alter de <chain> que já
existe; o resto do <chain> fica com o fix_50_chain.py. É idempotente.

Uso: python fix_50_alterchain.py [--dry] [skill_templates.xml ...]   (padrão: o do Código Fonte)
"""
import collections
import re
import sys

from fix_50_energia_sp_ep import TEMPLATES, le_cliente


def aplica(caminho, alter_ids, seco):
    raw = open(caminho, encoding="utf-8", newline="").read()
    contagem = collections.Counter()

    def edita(m):
        sid = int(m.group(2))
        corpo = m.group(3)
        tem = re.search(r"<chain\b[^>]*/>", corpo)
        if not tem:
            return m.group(0)
        chain = tem.group(0)
        sem = re.sub(r'\s+alter="[^"]*"', "", chain)
        quer = sem.replace("<chain ", '<chain alter="true" ', 1) if sid in alter_ids else sem
        if quer == chain:
            return m.group(0)
        contagem["posto" if sid in alter_ids else "retirado"] += 1
        return m.group(1) + corpo.replace(chain, quer, 1) + m.group(4)

    novo = re.sub(r'(<skill_template skill_id="(\d+)"[^>]*>)(.*?)(</skill_template>)', edita, raw, flags=re.S)
    print(caminho, dict(contagem) or "nada a mudar")
    if novo != raw and not seco:
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(novo)


def main():
    seco = "--dry" in sys.argv
    caminhos = [a for a in sys.argv[1:] if a != "--dry"] or [TEMPLATES]
    cli = le_cliente()
    alter_ids = {i for i, c in cli.items() if c.get("alterchain_use") == "1" and c.get("chain_category_name")}
    for caminho in caminhos:
        aplica(caminho, alter_ids, seco)


if __name__ == "__main__":
    main()
