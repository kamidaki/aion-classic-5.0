"""hittypeprob2 dos <provoker> do skill_templates.xml em por mil, como o effectN_reserved_cond1_prob2 do client_skills 5.0.

A escala sai do texto oficial do Ariel Ring (STR_Item_Skill_Trans_Ariel_Ring_01_DESC): prob2 500 = 50%, 6 = 0,6%. O ProvokerEffect
lia "acima de 100 é por mil, até 100 é percentual", e em 2026-09-30 os 125 provokers com valor até 100 disparavam 10x mais que no
cliente (CH_ImbueEarth 100 = 100% em vez de 10%). Alguns já tinham sido divididos por 10 à mão para compensar (AS_StuningIntention
2 com 20 no cliente, CL_ImbueWind 5 com 50). Junto com este script, o ProvokerEffect passa a dividir sempre por 10.

Regras, na ordem:
  1. o efeito de mesmo índice no cliente é Provoker com prob2 > 0 -> hittypeprob2 = prob2 do cliente
  2. Moros_Promise G1-G3 (prob2 0 e a chance no prob1 = 20): mantém os 20% de hoje, 200 por mil (a G4 tem 220 no prob2)
  3. sem correspondente no cliente: mantém a chance de hoje. Os únicos até 100 eram th_imbueearth_g1-g3 (10 = 10%), fixados em
     100 por mil em SEM_CLIENTE (um "x10" genérico multiplicaria de novo a cada execução); sem o atributo (valia 100%) vira 1000
Todo provoker fica com hittypeprob2 explícito, porque o padrão 100 do EffectTemplate passaria a valer 10%.

Uso: python fix_50_provoker_prob.py [--dry]
"""
import collections
import re
import sys

from fix_50_energia_sp_ep import TEMPLATES, le_cliente

MOROS_PROB1 = {"moros_promise_g1", "moros_promise_g2", "moros_promise_g3"}
SEM_CLIENTE = {2384: "100", 2385: "100", 2386: "100"}  # th_imbueearth_g1-g3: 10% antes da troca de escala


def main():
    seco = "--dry" in sys.argv
    cli = le_cliente()
    raw = open(TEMPLATES, encoding="utf-8", newline="").read()
    contagem, exemplos = collections.Counter(), collections.defaultdict(list)

    def edita(m):
        sid = int(m.group(1))
        c = cli.get(sid, {})

        def provoker(p):
            tag = p.group(0)
            e = re.search(r'\be="(\d+)"', tag).group(1)
            tem = re.search(r'\shittypeprob2="(\d+)"', tag)
            atual = tem.group(1) if tem else None
            prob2 = c.get("effect%s_reserved_cond1_prob2" % e, "0")
            if c.get("effect%s_type" % e) == "Provoker" and prob2 not in ("", "0"):
                quer, regra = prob2, "1 cliente"
            elif c.get("name", "").lower() in MOROS_PROB1:
                quer, regra = str(int(c.get("effect%s_reserved_cond1_prob1" % e)) * 10), "2 moros"
            elif sid in SEM_CLIENTE:
                quer, regra = SEM_CLIENTE[sid], "3 sem cliente"
            elif atual is None:
                quer, regra = "1000", "3 sem cliente, sem atributo"
            else:
                return tag
            if quer == atual:
                return tag
            k = "%s: %s -> %s" % (regra, atual, quer) if regra != "1 cliente" else "%s (%s)" % (regra, "trocado" if tem else "acrescentado")
            contagem[k] += 1
            exemplos[k].append(sid)
            if tem:
                return tag.replace(tem.group(0), ' hittypeprob2="%s"' % quer, 1)
            return re.sub(r"\s*/>$", ' hittypeprob2="%s"/>' % quer, tag)

        return re.sub(r"<provoker\b[^>]*/>", provoker, m.group(0))

    novo = re.sub(r'<skill_template skill_id="(\d+)".*?</skill_template>', edita, raw, flags=re.S)
    for k in sorted(contagem):
        print("%5d  %-40s %s%s" % (contagem[k], k, exemplos[k][:10], " ..." if len(exemplos[k]) > 10 else ""))
    sem = [m.group(1) for m in re.finditer(r'<skill_template skill_id="(\d+)".*?</skill_template>', novo, re.S)
           if re.search(r"<provoker\b(?![^>]*hittypeprob2)[^>]*/>", m.group(0))]
    print("provokers sem hittypeprob2 depois:", len(sem), sem[:10])
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
