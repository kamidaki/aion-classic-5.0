"""<subeffect> de status (puxar, Stumble, Stagger, Spin, OpenAerial) nos danos do skill_templates.xml, pelo client_skills 5.0.

No cliente, o dano instantâneo (SkillATK_Instant, SpellATK_Instant...) leva o status em effectN_reserved14: o nome de uma skill
de status. O servidor representa isso com <subeffect skill_id="..."/> dentro do elemento do dano (e="N"). Em 18/10/2026, 122
skills que o jogador aprende estavam sem o subeffect, e o efeito não acontecia: a Doom Lure nova (KN_StunningSnacher_new_G1,
2691) não puxava. Eram 6 Pulled, 47 Stagger, 45 Stumble, 23 OpenAerial e 1 Spin, mais 158 de NPC ou não aprendidas.

Mapa nome → skill: o nome nem sempre é o da skill (Stumble = NormalAttack_Stumble 8218). Conferido contra os 90 templates que
já estavam certos: nenhum diverge do mapa abaixo.
chance = effectN_reserved18 quando o cliente tem o campo e ele não é 100 (50↔50, 90↔90, 20↔20 nos que já estavam certos).

Só cria o que falta; não mexe em subeffect existente. Idempotente.

Uso: python fix_50_status_subeffect.py [--dry] [skill_templates.xml ...]   (padrão: o do Código Fonte)
"""
import collections
import re
import sys

from fix_50_energia_sp_ep import TEMPLATES, le_cliente

STATUS = {
    "stagger": 8217, "stumble": 8218, "openaerialth": 8221, "spin": 8223, "openaerial": 8224, "pulled": 8441,
    "stagger2": 8632, "stagger3": 8633, "stagger4": 8634, "stagger5": 8785,
    "stumble2": 8635, "stumble3": 8636, "stumble4": 8637,
    "nstagger": 8675, "nstumble": 8676, "nspin": 8677, "nopenaerial": 8678, "npulled": 8679,
}


def subeffects_do_cliente(cli):
    """{skill_id: [(e, skill de status, chance ou None)]}"""
    por_nome = {c["name"].lower(): i for i, c in cli.items()}
    quer = collections.defaultdict(list)
    for sid, c in cli.items():
        for n in range(1, 5):
            if not c.get("effect%d_type" % n, "").endswith("_Instant"):
                continue
            r = c.get("effect%d_reserved14" % n, "").lower()
            sub = STATUS.get(r, por_nome.get(r) if r.startswith(("pulled", "stumble", "stagger", "spin", "openaerial")) else None)
            if sub is None:
                continue
            chance = c.get("effect%d_reserved18" % n)
            quer[sid].append((n, sub, chance if chance and chance != "100" else None))
    return quer


def aplica(caminho, quer, seco):
    raw = open(caminho, encoding="utf-8", newline="").read()
    eol = "\r\n" if "\r\n" in raw[:5000] else "\n"
    contagem = collections.Counter()
    sem_elemento = []

    def edita(m):
        sid = int(m.group(2))
        if sid not in quer:
            return m.group(0)
        corpo = m.group(3)
        novo = corpo
        for n, sub, chance in quer[sid]:
            linha = '<subeffect skill_id="%d"%s/>' % (sub, ' chance="%s"' % chance if chance else "")
            el = re.search(r'([ \t]*)<(\w+)\b([^>]*\be="%d"[^>]*?)(/?)>' % n, novo)
            if not el:
                sem_elemento.append(sid)
                continue
            ind, nome, attrs, fecha = el.group(1), el.group(2), el.group(3), el.group(4)
            if fecha:
                bloco = "%s<%s%s>%s%s\t%s%s%s</%s>" % (ind, nome, attrs.rstrip(), eol, ind, linha, eol, ind, nome)
                novo = novo[:el.start()] + bloco + novo[el.end():]
            else:
                fim = novo.find("</%s>" % nome, el.end())
                if "<subeffect " in novo[el.end():fim]:
                    continue
                novo = novo[:el.end()] + eol + ind + "\t" + linha + novo[el.end():]
            contagem[sub] += 1
        return m.group(1) + novo + m.group(4) if novo != corpo else m.group(0)

    novo = re.sub(r'(<skill_template skill_id="(\d+)"[^>]*>)(.*?)(</skill_template>)', edita, raw, flags=re.S)
    print(caminho, "criados:", sum(contagem.values()), dict(contagem))
    if sem_elemento:
        print("  sem elemento e=N:", sorted(set(sem_elemento))[:20])
    if novo != raw and not seco:
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(novo)


def main():
    seco = "--dry" in sys.argv
    caminhos = [a for a in sys.argv[1:] if a != "--dry"] or [TEMPLATES]
    quer = subeffects_do_cliente(le_cliente())
    for caminho in caminhos:
        aplica(caminho, quer, seco)


if __name__ == "__main__":
    main()
