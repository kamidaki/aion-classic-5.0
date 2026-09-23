#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dados das campanhas (category1=mission) do Classic 5.0 que impedem ou distorcem a progressão.

1. Objetos de etapa sem interação no servidor. O cliente marca todos com `quest_ai_name`, `talk_delay_time` e
   `user_animation`; no servidor alguns ficaram com uma IA que não avisa o motor de quests:
     - 700749 LF4_DragonTabletE_Q30205 (10169, etapa 5): `useitem`, enquanto as tabuletas A-D são `quest_use_item`;
     - 701475 / 701477 LDF4b_FOBJ_T4_TombstoneA/C (10541/20541, etapa 7): `noaction`.
   A captura outros2 (22/09) mostra a lápide C com barra de 12000 ms (S 0xC4) e o S_QUEST na var 8 ao terminar;
   `talk_delay_time` 12 no client_npcs. A ferramenta põe `ai="quest_use_item"` e copia distância e tempo do cliente.

2. Chance dos drops de quest. O `parse_quests_50.py` grava `chance="100"` para todo `quest_drop`; o quest.xml do cliente
   dá `drop_prob_N` por grupo de monstros (50 para os comuns, 100 para os nomeados/objetos). Só as campanhas ativas
   (minlevel_permitted != 99) são tocadas.

Edita `npc_templates.xml` e `quest_data.xml` das duas árvores no lugar (as árvores divergem; nunca copiar uma sobre a outra).

Uso:
    python "6 - Ferramentas/parsersXML/fix_50_campanhas.py"            aplica
    python "6 - Ferramentas/parsersXML/fix_50_campanhas.py" --simular  só relata
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
DADOS_CLIENTE = os.path.join(RAIZ, "5 - Documentação e Referências", "3 - Client 5.0 - Dados Extraidos", "data")
ARVORES = [
    os.path.join(RAIZ, "1 - Código Fonte [Emulador]", "game-server", "data", "static_data"),
    os.path.join(RAIZ, "2 - Emulador [Produto Final]", "GameServer", "data", "static_data"),
]

OBJETOS_DE_ETAPA = {
    700749: "10169 etapa 5 (tabuleta E; A-D já são quest_use_item)",
    701475: "10541 etapa 7 (lápide A)",
    701477: "20541 etapa 7 (lápide C; captura outros2: barra de 12000 ms e var 8)",
}


def cliente_npcs():
    out = {}
    for n in ET.parse(os.path.join(DADOS_CLIENTE, "npcs", "client_npcs.xml")).getroot():
        d = {c.tag: (c.text or "").strip() for c in n}
        out[int(d["id"])] = d
    return out


def corrige_objetos(caminho, clientes, simular):
    texto = open(caminho, encoding="utf-8", newline="").read()
    mudou = 0
    for npc_id, motivo in OBJETOS_DE_ETAPA.items():
        c = clientes[npc_id]
        m = re.search(r'(\t<npc_template npc_id="%d" [^>]*>)(.*?)(</npc_template>)' % npc_id, texto, re.S)
        if not m:
            print(f"  {npc_id}: sem template em {caminho}")
            continue
        cabeca, corpo, fim = m.groups()
        nova_cabeca = re.sub(r' ai="[^"]*"', ' ai="quest_use_item"', cabeca)
        distancia = int(float(c["talking_distance"]))
        atraso = int(c["talk_delay_time"])
        talk = f'<talk_info distance="{distancia}" delay="{atraso}" can_talk_invisible="false" />'
        novo_corpo = re.sub(r"<talk_info [^>]*/>", talk, corpo)
        if nova_cabeca == cabeca and novo_corpo == corpo:
            continue
        print(f"  {npc_id} {c['name']}: ai=quest_use_item, talk_info distance={distancia} delay={atraso} -- {motivo}")
        texto = texto[:m.start()] + nova_cabeca + novo_corpo + fim + texto[m.end():]
        mudou += 1
    if mudou and not simular:
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(texto)
    return mudou


def probabilidades_do_cliente(clientes_por_nome):
    """{quest_id: {npc_id: prob}} das campanhas ativas, pelo drop_monster_N/drop_prob_N do quest.xml europeu."""
    out = {}
    for q in ET.parse(os.path.join(DADOS_CLIENTE, "europe", "Quest", "quest.xml")).getroot().findall("quest"):
        d = {c.tag: (c.text or "").strip() for c in q}
        if d.get("category1") != "mission" or d.get("minlevel_permitted") == "99":
            continue
        probs = {}
        for i in range(1, 10):
            nomes, prob = d.get(f"drop_monster_{i}"), d.get(f"drop_prob_{i}")
            if not nomes or not prob:
                continue
            for nome in nomes.split():
                for npc_id in clientes_por_nome.get(nome.lower(), []):
                    probs[npc_id] = int(prob)
        if probs:
            out[int(d["id"])] = probs
    return out


def corrige_drops(caminho, probs, simular):
    texto = open(caminho, encoding="utf-8", newline="").read()
    mudou = 0

    def troca_quest(m):
        nonlocal mudou
        qid = int(m.group(1))
        if qid not in probs:
            return m.group(0)

        def troca_drop(d):
            nonlocal mudou
            npc_id = int(d.group(1))
            chance = probs[qid].get(npc_id)
            if chance is None or int(d.group(2)) == chance:
                return d.group(0)
            mudou += 1
            print(f"  {qid}: quest_drop npc {npc_id} chance {d.group(2)} -> {chance}")
            return d.group(0).replace(f'chance="{d.group(2)}"', f'chance="{chance}"')

        return re.sub(r'<quest_drop npc_id="(\d+)"[^>]*? chance="(\d+)"[^>]*/>', troca_drop, m.group(0))

    texto = re.sub(r'<quest id="(\d+)".*?</quest>', troca_quest, texto, flags=re.S)
    if mudou and not simular:
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(texto)
    return mudou


def main(argv):
    simular = "--simular" in argv
    clientes = cliente_npcs()
    por_nome = {}
    for i, d in clientes.items():
        por_nome.setdefault(d.get("name", "").lower(), []).append(i)
    probs = probabilidades_do_cliente(por_nome)
    for arvore in ARVORES:
        print(arvore)
        n1 = corrige_objetos(os.path.join(arvore, "npcs", "npc_templates.xml"), clientes, simular)
        n2 = corrige_drops(os.path.join(arvore, "quest_data", "quest_data.xml"), probs, simular)
        print(f"  => {n1} objetos, {n2} drops{' (simulação)' if simular else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
