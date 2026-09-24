"""Corrige no skill_templates.xml o alcance das skills de área (AREA e PARTY), a partir do client_skills 5.0.

O TargetRangeProperty do Java mede a área por effective_range, effective_dist, effective_angle e effective_altitude, mas os
templates guardam o raio em target_distance, que o Java só lê em POINT. Sem effective_*, o alcance vira 0 mais os raios de
colisão: com first_target=ME a skill não acha ninguém (o próprio jogador sai no filtro ENEMY) e com first_target=TARGET só
acerta o primeiro alvo. Os PARTY usam o mesmo effective_range e não achavam o grupo.

Cliente -> servidor, por target_range_area_type:

  Fireball       effective_range = opt1, effective_altitude = opt3 (centro no primeiro alvo)
  FireStorm      effective_dist = opt1, effective_angle = opt2, effective_altitude = opt3, direction = BACK se opt4 = Back
                 (cone a partir de quem lança)
  LightningBolt  effective_dist = opt2 (comprimento), effective_range = 2 x opt1 (o Java usa effective_range / 2 como raio
                 do cilindro), effective_altitude = opt3, direction = BACK se opt4 = Back; sai o effective_angle, que o
                 gerador preenchia com o opt2 e o Java leria como cone
  Party          effective_range = opt1

5.0 oficial (05_Combate_Skills, 09-46-56): LU_RainSword_high_G1, Fireball com opt1 = 5, acertou alvos a 0 e 5,48 m do primeiro
alvo (centro a centro) e deixou de fora o seguinte, a 12,58 m. Bate com o raio somado às colisões do isInRange(..., false).
Não medidos: a altitude (opt3) e a largura da LightningBolt.

Também tira o direction="BACK" onde o cliente diz Front (TH_ElectricStrike, TH_LightningStorm, TH_LightningShock...), que
virava o cone para trás de quem lança.

Só mexe onde o target_type do servidor já concorda com o cliente (AREA com Area, PARTY/PARTY_WITHPET com Party). O
target_distance fica, porque o POINT usa. Idempotente: rodar de novo não muda nada. Rode depois de regenerar o
skill_templates.xml (rebuild_50_skill_effects.py), que continua escrevendo só target_distance.

Uso: python fix_50_area_alcance.py [--dry]
"""
import collections
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
XMLS = r"G:\Projetos AION\XMLS AION CLASSIC\data"
TEMPLATES = os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data", "skills", "skill_templates.xml")

PARTY = {"party": ("PARTY", "PARTY_WITHPET"), "party_withpet": ("PARTY", "PARTY_WITHPET")}


def le_cliente():
    t = open(os.path.join(XMLS, "skills", "client_skills.xml"), encoding="utf-8", errors="replace").read()
    cli = {}
    for b in t.split("<skill_base_client>")[1:]:
        d = dict(re.findall(r"<([a-z_0-9]+)>([^<]*)</\1>", b))
        if "id" in d:
            cli[int(d["id"])] = d
    return cli


def metros(v, fator=1):
    """opt do cliente -> inteiro do XSD; vazio, zero ou lixo -> None."""
    try:
        f = float(v) * fator
    except (TypeError, ValueError):
        return None
    n = int(f + 0.5)
    return n if n > 0 else None


def alvo(c):
    """Os atributos que o Java precisa para a área do cliente, ou None se não for área que o script trate."""
    tr = (c.get("target_range") or "").lower()
    tipo = (c.get("target_range_area_type") or "").lower()
    o1, o2, o3 = (c.get("target_range_opt%d" % i) for i in (1, 2, 3))
    costas = (c.get("target_range_opt4") or "").lower() == "back"
    if tr in PARTY:
        return PARTY[tr], {"effective_range": metros(o1)}, None, ()
    if tr != "area":
        return None
    if tipo == "fireball":
        return ("AREA",), {"effective_range": metros(o1), "effective_altitude": metros(o3)}, None, ()
    if tipo == "firestorm":
        return ("AREA",), {"effective_dist": metros(o1), "effective_angle": metros(o2), "effective_altitude": metros(o3)}, costas, ()
    if tipo == "lightningbolt":
        return ("AREA",), {"effective_dist": metros(o2), "effective_range": metros(o1, 2), "effective_altitude": metros(o3)}, costas, ("effective_angle",)
    return None


def poe_attr(attrs, nome, valor):
    if re.search(r'\s%s="[^"]*"' % nome, attrs):
        return re.sub(r'(\s%s=)"[^"]*"' % nome, r'\g<1>"%s"' % valor, attrs)
    return attrs + ' %s="%s"' % (nome, valor)


def tira_attr(attrs, nome):
    return re.sub(r'\s%s="[^"]*"' % nome, "", attrs)


def main():
    seco = "--dry" in sys.argv
    cli = le_cliente()
    raw = open(TEMPLATES, encoding="utf-8", newline="").read()
    contagem = collections.Counter()
    exemplos = collections.defaultdict(list)

    def edita(m):
        sid = int(m.group(2))
        c = cli.get(sid)
        if c is None:
            return m.group(0)
        regra = alvo(c)
        if regra is None:
            return m.group(0)
        tipos_srv, valores, costas, tirar = regra
        corpo = m.group(3)
        p = re.search(r"(<properties\b)([^>]*?)(\s*/>)", corpo)
        if not p:
            return m.group(0)
        attrs = p.group(2)
        tt = re.search(r'\starget_type="([A-Z_]+)"', attrs)
        chave = "%s/%s" % ((c.get("target_range") or "").lower(), (c.get("target_range_area_type") or "").lower())
        if not tt or tt.group(1) not in tipos_srv:
            contagem["pulado: target_type %s no servidor, %s no cliente" % (tt.group(1) if tt else "-", chave)] += 1
            return m.group(0)
        novo = attrs
        for nome, valor in valores.items():
            if valor is not None:
                novo = poe_attr(novo, nome, valor)
        for nome in tirar:
            novo = tira_attr(novo, nome)
        if costas:
            novo = poe_attr(novo, "direction", "BACK")
        elif costas is False and re.search(r'\sdirection="BACK"', novo):
            novo = tira_attr(novo, "direction")
            contagem["direction BACK retirado (cliente Front)"] += 1
            exemplos["BACK retirado"].append(sid)
        if novo == attrs:
            return m.group(0)
        contagem["corrigido " + chave] += 1
        exemplos[chave].append(sid)
        corpo = corpo[:p.start(2)] + novo + corpo[p.end(2):]
        return m.group(1) + corpo + m.group(4)

    novo = re.sub(r'(\t<skill_template skill_id="(\d+)"[^>]*>)(.*?)(</skill_template>)', edita, raw, flags=re.S)
    for k in sorted(contagem):
        print("%-60s %5d" % (k, contagem[k]))
    for k in sorted(exemplos):
        print("   ", k, exemplos[k][:15], "..." if len(exemplos[k]) > 15 else "")
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
