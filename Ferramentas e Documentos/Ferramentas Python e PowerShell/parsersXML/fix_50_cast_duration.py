"""Tempo de conjuração do skill_templates.xml (atributo duration) igual ao casting_delay do client_skills 5.0.

O Skill usa o duration do template como tempo de cast (Skill.castDuration). Em 2026-09-14, 12.092 de 12.113 templates batiam com o cliente; os 21
restantes vinham do gerador antigo:
  - RB_SoulRemnant_G1/G2 com 240000 (a duração do buff): a Soul Pact ficava 4 min castando e parecia não ativar
  - RB_SoulRemnant_G1/G2_Effect com 3600000 (a duração do Soul Rest)
  - HellFire, IceAge, Control, TerrorSpirit e HellFlame com 0 onde o cliente tem 1000 a 2000 ms

O script, idempotente: duration = casting_delay (0 quando o cliente não tem o campo) em todo template que diverge.

Uso: python fix_50_cast_duration.py [--dry]
"""
import re
import sys

from fix_50_energia_sp_ep import TEMPLATES, le_cliente


def main():
    seco = "--dry" in sys.argv
    cli = le_cliente()
    raw = open(TEMPLATES, encoding="utf-8", newline="").read()
    mudou = []

    def edita(m):
        sid = int(m.group(2))
        c = cli.get(sid)
        if c is None:
            return m.group(0)
        cast = str(int(c.get("casting_delay") or 0))
        cabeca = m.group(1)
        atual = re.search(r'\sduration="(\d+)"', cabeca)
        if (atual.group(1) if atual else "0") == cast:
            return m.group(0)
        if atual:
            cabeca = cabeca.replace(atual.group(0), ' duration="%s"' % cast, 1)
        else:
            cabeca = cabeca[:-1] + ' duration="%s">' % cast
        mudou.append((sid, c.get("name"), atual.group(1) if atual else "-", cast))
        return cabeca

    novo = re.sub(r'(<skill_template skill_id="(\d+)"[^>]*>)', lambda m: edita(m), raw)
    for x in mudou:
        print("%5d %-32s %s -> %s" % x)
    print("templates alterados:", len(mudou))
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
