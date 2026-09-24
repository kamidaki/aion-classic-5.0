"""<provoker> sem provoke_target no skill_templates.xml, corrigido a partir do client_skills 5.0.

Sem provoke_target o ProvokerEffect estoura NullPointerException no primeiro golpe depois de aplicado (log de 2026-09-14: depois da
RB_Isolation_G1 do Soul Reaper, toda 4407 e todo ataque do servant 19985 davam erro).

Gabarito, medido nos 312 provokers do servidor que têm provoke_target e cujo efeito no cliente é Provoker:
  provoke_target = reserved14 (309/312)     hittype = reserved_cond1 (299/312)     hittypeprob2 = reserved_cond1_prob2 (267/312)
  radius = reserved5 (307/312)              duration2 = remain2 (288/312)          effectid, basiclvl (307/312)
  noresist (311/312)                        preeffect = cond_preeffect e1 (312/312)

O script, idempotente (rodar de novo não muda nada):
  1. efeito que é Provoker no cliente: a linha é refeita pelo gabarito, com skill_id pelo nome do reserved17
  2. efeito que não é Provoker no cliente: a linha é inventada e sai. Caso da RB_Isolation_G1 (4440), que no cliente é TargetLock
     (sem implementação no emulador) e tinha um <provoker skill_id="4440"> apontando para ela mesma

Uso: python fix_50_provoker_sem_alvo.py [--dry]
"""
import re
import sys

from fix_50_energia_sp_ep import TEMPLATES, le_cliente, pre_efeito

HIT_TYPES = {"EVERYHIT", "NMLATK", "MAHIT", "PHHIT", "FEAR", "SKILL", "BACKATK"}


def linha_provoker(c, n, skill_id_antigo, ids):
    g = lambda k, d="": c.get("effect%d_%s" % (n, k), d)
    skill_id = ids.get(g("reserved17").lower(), skill_id_antigo)
    s = '<provoker e="%d" skill_id="%s" provoke_target="%s"' % (n, skill_id, g("reserved14").upper())
    hit = g("reserved_cond1").upper()
    if hit in HIT_TYPES and hit != "EVERYHIT":
        s += ' hittype="%s"' % hit
    if g("reserved_cond1_prob2"):
        s += ' hittypeprob2="%s"' % g("reserved_cond1_prob2")
    if g("reserved5", "0") != "0":
        s += ' radius="%s"' % g("reserved5")
    if g("remain2", "0") != "0":
        s += ' duration2="%s"' % g("remain2")
    if g("effectid"):
        s += ' effectid="%s"' % g("effectid")
    if g("basiclv", "0") != "0":
        s += ' basiclvl="%s"' % g("basiclv")
    if g("noresist") == "1":
        s += ' noresist="true"'
    return s + pre_efeito(c, n) + " />"


def main():
    seco = "--dry" in sys.argv
    cli = le_cliente()
    ids = {d["name"].lower(): str(i) for i, d in cli.items()}
    raw = open(TEMPLATES, encoding="utf-8", newline="").read()
    eol = "\r\n" if "\r\n" in raw[:5000] else "\n"
    refeitos, removidos = [], []

    def edita(m):
        sid = int(m.group(2))
        texto = m.group(0)
        c = cli.get(sid)
        if c is None:
            return texto
        for p in re.finditer(r"([ \t]*)(<provoker\b[^>]*/>)[ \t]*" + re.escape(eol), texto):
            tag = p.group(2)
            if "provoke_target" in tag:
                continue
            e = re.search(r'\be="(\d+)"', tag)
            n = int(e.group(1)) if e else 1
            if (c.get("effect%d_type" % n) or "").lower() == "provoker" and c.get("effect%d_reserved14" % n):
                antigo = re.search(r'\bskill_id="(\d+)"', tag)
                novo = p.group(1) + linha_provoker(c, n, antigo.group(1) if antigo else "0", ids) + eol
                refeitos.append(sid)
            else:
                novo = ""
                removidos.append((sid, c.get("effect%d_type" % n)))
            texto = texto.replace(p.group(0), novo, 1)
        return texto

    novo = re.sub(r'(<skill_template skill_id="(\d+)"[^>]*>)(.*?)(</skill_template>)', edita, raw, flags=re.S)
    print("refeitos pelo gabarito:", refeitos)
    print("removidos (não são Provoker no cliente):", removidos)
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
