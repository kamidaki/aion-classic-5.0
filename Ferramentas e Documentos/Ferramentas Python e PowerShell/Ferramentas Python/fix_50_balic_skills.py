"""Skills dos mobs do Balic Treasury (800070000) pela captura oficial -> npc_skills/open_worlds/800070000_Balic_Treasury.xml.

Fonte: "Wireshark - Oficial Classic 5.0/06_Sistemas_Novos_5.0/Balic Treasury.pcapng" (29/10), S_USE_SKILL 0x21
([D quem][H skill][C nível][C tipo de alvo][D alvo]...). Antes deste arquivo nenhum mob do mapa tinha npc_skills.

Cada luta mostra uma abertura fixa (a 1ª skill) e depois a mesma ordem, com 2 a 11 s entre uma skill e a próxima. O
Assault Team Leader (221298) é o único com lutas longas: gira 19710 -> 19712 -> 19713 em laço (quando a 19713 não sai, a
vez passa igual: 19712 -> 19710 em ~13 s). Os outros ficam na sequência vista, sem laço: no fim dela o emulador volta para
a abertura, como no começo de cada luta oficial.

No emulador (mesmo formato do fix_50_torre_skills.py): abertura com chain_id 0 (a única que a escolha normal pega) e a
sequência em chain_id 1..n, prob 100; next_skill_time = mediana do intervalo início a início até a próxima; max_chain_time
= esse intervalo + o passo seguinte + 3 s. target="ME" quando todo uso da skill na captura teve o próprio mob como alvo.

Fora: 221237 (é do 800060000), invocações de jogador e mobs sem template (armadilhas 220810/220857-220860 e Black Drana
221330/221331): entram quando o template existir (create_50_npc_templates_captura.py), com --incluir-sem-template.

Uso:
    python fix_50_balic_skills.py            # mostra o arquivo e as medidas
    python fix_50_balic_skills.py --aplicar  # grava nas duas árvores
"""
import collections
import os
import re
import statistics as st
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import aion_pcap  # noqa: E402

RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
CAPTURA = os.path.join(RAIZ, "Ferramentas e Documentos", "Client e Coletas", "Wireshark - Oficial Classic 5.0", "06_Sistemas_Novos_5.0",
                       "Balic Treasury.pcapng")
REL = os.path.join("npc_skills", "open_worlds", "800070000_Balic_Treasury.xml")
BASES = [os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data"),
         os.path.join(RAIZ, "Emulador - Produto Final", "GameServer", "data", "static_data")]
MAPA = 800070000

# npcId -> (sequência vista, laço?). A sequência é a da luta mais longa; as outras lutas do mesmo npc começam igual.
SEQ = {
    221257: ([18752, 20483, 20485, 20486], False),                # Protectorate Drakan Special Legate (Fi Tiamat Ae)
    221287: ([20484, 20483, 20484, 20485, 20486, 20486], False),  # Keymaster Snika (Fi Tiamat Key Ae)
    221258: ([21450, 21452, 21453, 21454], False),                # Sc Tiamat Ae
    221288: ([21450], False),                                     # Sc Tiamat Key Ae (só a abertura)
    221259: ([20490, 20489, 20490, 20491], False),                # Wi Tiamat Ae
    221261: ([18166, 16785, 19135], False),                       # Special Fighter (Fi Noble Ae)
    221262: ([18173, 16812, 19135], False),                       # Special Hawkeye (Sc Noble Ae)
    221264: ([17008], False),                                     # Cl Noble Ae (só a abertura)
    221283: ([18166, 18164, 18165], False),                       # Drakan Fighter (Fi Noble An)
    221284: ([18173, 16812], False),                              # Sc Noble An
    221265: ([21291, 19695], False),                              # Elite Combat Captain (dragão)
    221278: ([19697], False),                                     # Balic Aether Cannon
    221298: ([19710, 19712, 19713], True),                        # Assault Team Leader (laço)
    # sem template hoje (ver docstring)
    221330: ([16516, 16533], False),                              # Black Drana Worker
    221331: ([18166, 16785], False),                              # Black Drana DrakanFi
    220859: ([19701, 19702], False),                              # MistArea
    220860: ([19701], False),
    220857: ([19700], False),                                     # AntiMagicalArea
    220858: ([19699], False),
    220810: ([19698], False),                                     # DrakanWeapon_Invisible
}
SEM_TEMPLATE = {221330, 221331, 220859, 220860, 220857, 220858, 220810}
NOMES = {18752: "Capture", 20484: "Capture", 20483: "Smash", 20485: "Vortex", 20486: "Vortex", 21450: "Apply Poison I",
         21452: "Beast Swipe", 21453: "Beastly Scar", 21454: "Beast Fang", 20489: "Shock Wave", 20490: "Death Dread",
         20491: "Flame Loop", 18166: "Powerful Ankle Snare", 16785: "Knockback", 19135: "Dragon's Blessing",
         18173: "Long-range Incapacitation", 16812: "Arrow Strike", 17008: "Blinding Energy", 18164: "Boisterous Pummeling",
         18165: "Create Protective Shield", 21291: "Power Attack", 19695: "Dragon Breath", 19697: "Magic Drana Cannon Shot",
         19710: "Mace of Retribution", 19712: "Mace of Retribution", 19713: "Shock Wave", 16516: "Strike",
         16533: "Wide Ranged Knockdown", 19701: "Mist", 19702: "Mist", 19700: "Great Magical Barrier",
         19699: "Great Magical Barrier", 19698: "Explosive Damage"}
INICIO, FIM = "<!-- fix_50_balic_skills: inicio -->", "<!-- fix_50_balic_skills: fim -->"


def medir():
    """npcId -> {'lutas': [[(t, skill, nível, alvo_é_ele)]]} só no 800070000."""
    obj2npc, mapa, por_obj = {}, None, collections.defaultdict(list)
    for s in aion_pcap.abre_todas(CAPTURA, sem_skey=True):
        for (op, p, ok), t in zip(s["servidor"], s["tempo_servidor"]):
            if not ok:
                continue
            if op == 0x0F and len(p) >= 4:
                mapa = struct.unpack_from("<I", p, 0)[0]
            elif op == 0x14 and len(p) >= 5:
                mapa = struct.unpack_from("<I", p, 1)[0]
            elif op == 0x0E and len(p) >= 20:
                obj2npc[struct.unpack_from("<I", p, 12)[0]] = struct.unpack_from("<I", p, 16)[0]
            elif op == 0x21 and len(p) >= 12 and mapa == MAPA:
                o = struct.unpack_from("<I", p, 0)[0]
                if o in obj2npc:
                    alvo = struct.unpack_from("<I", p, 8)[0] if p[7] in (0, 3, 4) else None
                    por_obj[o].append((t / 1e9, struct.unpack_from("<H", p, 4)[0], p[6], alvo == o))
    med = collections.defaultdict(list)
    for o, ev in por_obj.items():
        med[obj2npc[o]].append(sorted(set(ev)))
    return med


def tempos(lutas, seq, laco):
    """ms medianos de cada passo para o próximo (seq[i] -> seq[i+1]; no laço também o último -> primeiro)."""
    pares = list(zip(seq, seq[1:])) + ([(seq[-1], seq[0])] if laco else [])
    medidos = collections.defaultdict(list)
    for luta in lutas:
        for (ta, a, _, _), (tb, b, _, _) in zip(luta, luta[1:]):
            medidos[(a, b)].append(tb - ta)
    return [int(round(st.median(medidos[par]) * 10)) * 100 if medidos.get(par) else None for par in pares], medidos


def bloco(med, incluir_sem_template):
    L = [f"\t{INICIO}",
         "\t<!-- Balic Treasury: abertura + sequência medidas no S_USE_SKILL de \"Balic Treasury.pcapng\" (29/10), geradas por",
         "\t     fix_50_balic_skills.py. chain_id 0 = abertura; os passos seguintes em chain_id 1..n, com o intervalo oficial. -->"]
    for npc, (seq, laco) in SEQ.items():
        if npc in SEM_TEMPLATE and not incluir_sem_template:
            continue
        lutas = med.get(npc, [])
        if not lutas:
            sys.exit(f"{npc}: sem S_USE_SKILL na captura")
        ms, _ = tempos(lutas, seq, laco)
        nivel = collections.Counter(lv for luta in lutas for _, _, lv, _ in luta).most_common(1)[0][0]
        # AoE ofensiva em volta de si também vem com o próprio mob de alvo: ME só para skill que não é contra inimigo
        em_si = {sk for sk in seq if all(me for luta in lutas for _, s2, _, me in luta if s2 == sk) and RELACAO.get(sk) != "ENEMY"}
        L.append(f"\t<!-- {npc}: {len(lutas)} luta(s), sequência {' -> '.join(map(str, seq))}{' (laço)' if laco else ''} -->")
        L.append(f'\t<npc_skills npc_ids="{npc}">')
        n = len(seq)
        for i, sk in enumerate(seq):
            a = f'id="{sk}" lv="{nivel}" prob="100"' + (f' chain_id="{i}"' if i else "")
            prox = (i + 1) % n if laco else i + 1
            if prox < n and ms[i] is not None and not (laco and n == 1):
                passo = ms[prox] if prox < len(ms) and ms[prox] is not None else 0
                destino = prox if prox else n  # no laço o "primeiro" de novo é uma cópia com chain_id n
                a += f' next_chain_id="{destino}" next_skill_time="{ms[i]}" max_chain_time="{ms[i] + passo + 3000}"'
            if sk in em_si:
                a += ' target="ME"'
            L.append(f"\t\t<npc_skill {a} /><!-- {NOMES.get(sk, '')} -->")
        if laco:  # cópia da abertura no fim do laço, que aponta para o passo 1
            sk = seq[0]
            a = f'id="{sk}" lv="{nivel}" prob="100" chain_id="{n}" next_chain_id="1" next_skill_time="{ms[0]}" max_chain_time="{ms[0] + ms[1] + 3000}"'
            L.append(f"\t\t<npc_skill {a} /><!-- {NOMES.get(sk, '')} (volta do laço) -->")
        L.append("\t</npc_skills>")
    L.append(f"\t{FIM}")
    return "\n".join(L)


def arquivo(b):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<npc_skill_templates xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="../npc_skills.xsd">\n'
            f"{b}\n</npc_skill_templates>\n")


def relacoes():
    txt = open(os.path.join(BASES[0], "skills", "skill_templates.xml"), encoding="utf-8").read()
    rel = {}
    for sk in {s for seq, _ in SEQ.values() for s in seq}:
        m = re.search(r'<skill_template skill_id="%d".*?</skill_template>' % sk, txt, re.S)
        if m is None:
            sys.exit(f"skill {sk} sem template")
        r = re.search(r'target_relation="([^"]*)"', m.group(0))
        rel[sk] = r.group(1) if r else None
    return rel


RELACAO = {}


def main():
    RELACAO.update(relacoes())
    med = medir()
    incluir = "--incluir-sem-template" in sys.argv
    for npc, (seq, laco) in SEQ.items():
        ms, medidos = tempos(med.get(npc, []), seq, laco)
        print(npc, seq, "ms", ms, {f"{a}>{b}": [round(x, 1) for x in v] for (a, b), v in medidos.items()})
    b = bloco(med, incluir)
    novo = arquivo(b)
    print(novo)
    if "--aplicar" not in sys.argv:
        print("Simulação: nada gravado.")
        return
    from lxml import etree
    xsd = etree.XMLSchema(etree.parse(os.path.join(BASES[0], "npc_skills", "npc_skills.xsd")))
    doc = etree.fromstring(novo.encode("utf-8"))
    if not xsd.validate(doc):
        sys.exit(f"XSD: {xsd.error_log}")
    for base in BASES:
        caminho = os.path.join(base, REL)
        if os.path.exists(caminho):
            txt = open(caminho, encoding="utf-8", newline="").read()
            if INICIO in txt:
                novo_txt = re.sub(re.escape(INICIO) + ".*?" + re.escape(FIM), lambda _: b.lstrip("\t"), txt, count=1, flags=re.S)
            else:
                novo_txt = txt.replace("</npc_skill_templates>", b + "\n</npc_skill_templates>")
        else:
            novo_txt = novo
        open(caminho, "w", encoding="utf-8", newline="\n").write(novo_txt)
        print("gravado:", caminho)


if __name__ == "__main__":
    main()
