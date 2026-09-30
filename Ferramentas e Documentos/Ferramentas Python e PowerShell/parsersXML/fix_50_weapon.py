"""Condição de arma (<weapon weapon="..."/>) do skill_templates.xml alinhada com os required_<arma> do client_skills 5.0.

Em 2026-09-29, 4.441 templates tinham a mesma lista de 10 armas (GREATSWORD SPELLBOOK BOW DAGGER MACE ORB POLEARM STAFF SWORD CHAINBLADE),
sem as armas das classes novas. O WeaponCondition só valida skill lançada da barra (SkillMethod.CAST), então o servidor recusava:
  266 skills do Battlemaster (GAUNTLET), 195 do Lumines (DIMENSIONSWORD), 48 do Runeblade (RUNESWORD), 18 do Gunner (GUN_1H)
e ainda deixava passar arma que o cliente não aceita (ex.: AS_Blindside com espada grande, CH_SplashSwing com adaga).

Mapeamento: sword SWORD, mace MACE, dagger DAGGER, orb ORB, book SPELLBOOK, 2hsword GREATSWORD, polearm POLEARM, staff STAFF, bow BOW,
chainblade CHAINBLADE, gauntlet GAUNTLET, dimensionsword DIMENSIONSWORD, gun GUN_1H (grupo das armas nos item_templates), runesword RUNESWORD.
Só required_<arma> = 1 conta (37 campos vêm com 0).

O script mexe só em template que já tem <weapon> e cuja skill no cliente tem ao menos um required_<arma>; fica como está:
  - skill com WeaponStatBoost/WeaponStatUp: a arma do bônus vem do effectN_reserved5 do cliente (ex.: P_StatBoostAttackRange = BOW),
    e o <weapon> do servidor é o que limita o bônus a ela
  - template com <weapon> e cliente sem required_* (bônus de conjunto de armadura e afins, que usam o <weapon> para validar o stat)
  - template sem <weapon>: criar a condição onde o gerador não pôs fica para outro passo
GUN e GUN_1H valem o mesmo (o WeaponCondition aceita um pelo outro). Idempotente.

Uso: python fix_50_weapon.py [--dry]
"""
import collections
import re
import sys

from fix_50_energia_sp_ep import TEMPLATES, le_cliente

ARMAS = (
    ("sword", "SWORD"), ("mace", "MACE"), ("dagger", "DAGGER"), ("orb", "ORB"), ("book", "SPELLBOOK"), ("2hsword", "GREATSWORD"),
    ("polearm", "POLEARM"), ("staff", "STAFF"), ("bow", "BOW"), ("chainblade", "CHAINBLADE"), ("gauntlet", "GAUNTLET"),
    ("dimensionsword", "DIMENSIONSWORD"), ("gun", "GUN_1H"), ("runesword", "RUNESWORD"),
)


def armas_do_cliente(c):
    return [grupo for campo, grupo in ARMAS if c.get("required_" + campo) == "1"]


def normaliza(grupos):
    return {"GUN_1H" if g == "GUN" else g for g in grupos}


def main():
    seco = "--dry" in sys.argv
    cli = le_cliente()
    raw = open(TEMPLATES, encoding="utf-8", newline="").read()
    contagem = collections.Counter()
    exemplos = collections.defaultdict(list)

    def edita(m):
        sid = int(m.group(1))
        c = cli.get(sid)
        w = re.search(r'<weapon weapon="([^"]*)"', m.group(0))
        if c is None or w is None:
            return m.group(0)
        quer = armas_do_cliente(c)
        if not quer or any(v.startswith("WeaponStat") for k, v in c.items() if re.fullmatch(r"effect\d+_type", k)):
            return m.group(0)
        tem = w.group(1).split()
        if normaliza(tem) == set(quer):
            return m.group(0)
        ganha, perde = sorted(set(quer) - normaliza(tem)), sorted(normaliza(tem) - set(quer))
        k = "+%s -%s" % (",".join(ganha), ",".join(perde))
        contagem[k] += 1
        exemplos[k].append(sid)
        return m.group(0).replace(w.group(0), '<weapon weapon="%s"' % " ".join(quer), 1)

    novo = re.sub(r'<skill_template skill_id="(\d+)".*?</skill_template>', edita, raw, flags=re.S)
    for k, n in contagem.most_common():
        print("%5d  %s   %s%s" % (n, k, exemplos[k][:8], " ..." if len(exemplos[k]) > 8 else ""))
    print("total", sum(contagem.values()))
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
