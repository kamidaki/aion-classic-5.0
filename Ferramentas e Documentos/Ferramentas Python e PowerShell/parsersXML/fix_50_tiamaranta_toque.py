#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_tiamaranta_toque.py

Objetos de toque de Tiamaranta Mesa (800040000) como no 5.0 oficial: Aethers que explodem e anéis que dão buff.

Provas (Tiamaranta.pcapng e 08_Spawns_Mapas/Tiamaranta_Mesa, decodificadas pelo aion_pcap.py):
  - Aether 220977 lança 21420 nível 4 e 220978 lança 21421 nível 2 em si mesmo (S_USE_SKILL alvo = ele mesmo) e some no mesmo
    instante (S_REMOVE_OBJECT animação 1). Dano oficial 4759 e 2570 = 1000 + 1000 x nível menos a defesa.
  - O anel não lança nada: aparece o NPC invisível 802439 (Flight Ring → 21382) ou 802438 (Stealth Ring → 21381), que lança a skill
    nível 1 no jogador e some junto com o anel.

O que grava (com backup, nas duas árvores, só os blocos/linhas destes ids):
  skill_templates.xml  21381 e 21382 eram stub sem efeito; corpo refeito pelo client_skills.xml com a tradução campo -> atributo medida no
                       gabarito (Hide: reserved7 -> HIDE<n>, reserved3 -> buffcount, reserved2 = velocidade que sobra -> SPEED 100-r2 %;
                       StatUp: token de reserved13 -> stat PERCENT; 21382 e1 tem o valor em reserved1 com reserved2 0).
  npc_skills/open_worlds/800040000_Tiamaranta_Mesa.xml  skill e nível de cada NPC, pela captura.
  npc_templates.xml    ai: ldf4b_mine (220977/220978), ldf4b_getitem_npc (802217/802218), noaction nos auxiliares (802438/802439).

Uso:
    python fix_50_tiamaranta_toque.py            (mostra o que mudaria)
    python fix_50_tiamaranta_toque.py --aplicar  (grava, com backup pelo backup_manager)
"""

import argparse
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backup_manager  # noqa: E402

ARVORES = [backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR]

# client_skills 21381 GetItem_Hide_NPC_Skill: Buff, Hide remain2 300000 effectid 165 basiclv 21 reserved2 80 reserved3 3 reserved7 1 SkillLV
CORPO_21381 = """		<properties first_target="TARGET" target_type="AREA" target_species="PC" target_maxcount="24" first_target_range="6" target_distance="6" effective_range="6" effective_altitude="6"/>
		<effects>
			<hide state="HIDE1" buffcount="3" duration2="300000" effectid="165" e="1" basiclvl="21" noresist="true" hoptype="SKILLLV">
				<change stat="SPEED" func="PERCENT" value="-20"/>
			</hide>
		</effects>
		<motion name="NormalFire" instant_skill="true"/>
"""
# client_skills 21382 GetItem_Buff_NPC_Skill: Buff, e1 Statup speed reserved1 80 (effectid 1219221, basiclv 100, hop SkillLv a0 b1),
# e2 StatUp Flyspeed reserved2 160 (effectid 10181453, preeffect e1, hop Damage); duração 300000 nos dois
CORPO_21382 = """		<properties first_target="TARGET" target_type="AREA" target_species="PC" target_maxcount="24" first_target_range="6" target_distance="6" effective_range="6" effective_altitude="6"/>
		<effects>
			<statup duration2="300000" effectid="1219221" e="1" basiclvl="100" noresist="true" hoptype="SKILLLV" hopb="1">
				<change stat="SPEED" func="PERCENT" value="80"/>
			</statup>
			<statup duration2="300000" effectid="10181453" e="2" noresist="true" preeffect="1" preeffect_prob="100" hoptype="DAMAGE">
				<change stat="FLY_SPEED" func="PERCENT" value="160"/>
			</statup>
		</effects>
		<motion name="NormalFire" instant_skill="true"/>
"""
SKILLS = {"21381": CORPO_21381, "21382": CORPO_21382}

NPC_SKILLS = """<?xml version="1.0" encoding="UTF-8"?>
<npc_skill_templates xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="npc_skills.xsd">
	<!-- Tiamaranta Mesa: skill e nível pelas capturas oficiais (S_USE_SKILL), usados pelas AIs ldf4b_mine e ldf4b_getitem_npc -->
	<npc_skills npc_ids="220977">
		<npc_skill id="21420" lv="4" /><!-- Mutated Fallen Aether: dano + atordoamento + queda -->
	</npc_skills>
	<npc_skills npc_ids="220978">
		<npc_skill id="21421" lv="2" /><!-- Mutated Poison Aether: dano + veneno -->
	</npc_skills>
	<npc_skills npc_ids="802438">
		<npc_skill id="21381" lv="1" /><!-- LDF4b_GetItem_Hide_Skill_NPC (Stealth Ring): Hide -->
	</npc_skills>
	<npc_skills npc_ids="802439">
		<npc_skill id="21382" lv="1" /><!-- LDF4b_GetItem_Buff_Skill_NPC (Flight Ring): velocidade e voo -->
	</npc_skills>
</npc_skill_templates>
"""

AI = {"220977": ("aggressive", "ldf4b_mine"), "220978": ("aggressive", "ldf4b_mine"),
      "802217": ("general", "ldf4b_getitem_npc"), "802218": ("general", "ldf4b_getitem_npc"),
      "802438": ("portal_dialog", "noaction"), "802439": ("portal_dialog", "noaction")}


def troca_skills(dados):
    for sid, corpo in SKILLS.items():
        padrao = re.compile(rb'(\t<skill_template skill_id="' + sid.encode() + rb'"[^>]*>)\r?\n(.*?)(\t</skill_template>)', re.S)
        m = padrao.search(dados)
        if not m:
            raise SystemExit(f"skill {sid} não encontrada")
        cab = m.group(1)
        cab = re.sub(rb'skillsubtype="[A-Z_]+"', b'skillsubtype="BUFF"', cab)
        cab = re.sub(rb'tslot="[A-Z_]+"', b'tslot="BUFF"', cab)
        if b"dispel_category=" not in cab:
            cab = cab.replace(b' activation="', b' dispel_category="BUFF" activation="', 1)
        nl = b"\r\n" if b"\r\n" in m.group(0) else b"\n"
        novo = cab + nl + corpo.replace("\n", nl.decode()).encode("utf-8") + m.group(3)
        print(f"  skill {sid}: {'já aplicada' if m.group(0) == novo else 'refeita'}")
        dados = dados[:m.start()] + novo + dados[m.end():]
    return dados


def troca_ai(dados):
    for nid, (antiga, nova) in AI.items():
        padrao = re.compile(rb'(<npc_template npc_id="' + nid.encode() + rb'"[^>]*?\bai=")([^"]*)(")')
        m = padrao.search(dados)
        if not m:
            raise SystemExit(f"npc {nid} não encontrado")
        atual = m.group(2).decode()
        if atual not in (antiga, nova):
            raise SystemExit(f"npc {nid}: ai inesperada {atual!r} (esperava {antiga!r})")
        print(f"  npc {nid}: ai {atual} -> {nova}")
        dados = dados[:m.start(2)] + nova.encode() + dados[m.end(2):]
    return dados


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args()
    for arvore in ARVORES:
        print(arvore)
        sk = os.path.join(arvore, "skills", "skill_templates.xml")
        nt = os.path.join(arvore, "npcs", "npc_templates.xml")
        ns = os.path.join(arvore, "npc_skills", "open_worlds", "800040000_Tiamaranta_Mesa.xml")
        dados_sk = open(sk, "rb").read()
        dados_nt = open(nt, "rb").read()
        novo_sk = troca_skills(dados_sk)
        novo_nt = troca_ai(dados_nt)
        print(f"  {os.path.relpath(ns, arvore)}: {'cria' if not os.path.exists(ns) else 'reescreve'}")
        if not a.aplicar:
            continue
        for caminho, antigo, novo in ((sk, dados_sk, novo_sk), (nt, dados_nt, novo_nt)):
            if antigo != novo:
                backup_manager.backup_file_before_modification(caminho)
                open(caminho, "wb").write(novo)
        backup_manager.backup_file_before_modification(ns)
        open(ns, "w", encoding="utf-8", newline="\n").write(NPC_SKILLS)
    if not a.aplicar:
        print("Sem --aplicar: nada foi gravado.")


if __name__ == "__main__":
    main()
