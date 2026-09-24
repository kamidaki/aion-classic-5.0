#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_npc_land_of_shadows.py

Corrige os 76 templates de NPCs da instância Land of Shadows (IDTutorialQ, world 390000000,
faixa 804100..804175) eliminando a colisão com dados legados do 4.8.

Conferido em 23/09 com o S_PUT_NPC de todas as capturas oficiais (fix_50_npc_captura.py em simulação):
  - 804135 attack_speed 2249 (= attack_delay do cliente, igual no 804134)
  - controladores 804136..804155 e 804166 com maxHp 172; bonus box 22/23 (804174/804175) no level 7
Nome: o texto do desc no cliente coreano manda (o Strings/strings traduzido tem 465678/465679 errados):
  STR_IDTutorialQ_Teleport_Out_Li (804134) = Inggness, STR_IDTutorialQ_Teleport_Out_Da (804135) = Inggril.
  O <ment> do client_npcs vem trocado e nao serve de nome.
srange e talk_info dos dois teleportadores saem do sensory_range (25) e do talking_distance (3) do cliente.
Guardas 804100..804109: tribo do cliente (IDTutorialQ_Guard_L/_D, criadas pelo fix_50_land_of_shadows_tribos.py) e
ai aggressive -- no oficial eles atacam os mobs (IDTutorialQ_Monster) sem atacar o jogador, e aggressive e a ai que
decide aggro pela relacao de tribo.

Sincroniza as duas árvores:
  - Código Fonte - Emulador/game-server/data/static_data/npcs/npc_templates.xml
  - Emulador - Produto Final/GameServer/data/static_data/npcs/npc_templates.xml

Uso:
  python "Ferramentas e Documentos/Ferramentas Python e PowerShell/parsersXML/fix_50_npc_land_of_shadows.py"            (simulação/dry-run)
  python "Ferramentas e Documentos/Ferramentas Python e PowerShell/parsersXML/fix_50_npc_land_of_shadows.py" --aplicar  (grava com backup e validação XSD)
"""

import argparse
import os
import re
import sys
from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
sys.path.insert(0, AQUI)
import backup_manager  # noqa: E402

ARVORES = (
    ("fonte", os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data")),
    ("produto", os.path.join(RAIZ, "Emulador - Produto Final", "GameServer", "data", "static_data")),
)
REL_XML = os.path.join("npcs", "npc_templates.xml")
REL_XSD = os.path.join("npcs", "npcs.xsd")
BLOCO_RE = re.compile(r'(\t?<npc_template\b[^>]*npc_id="(\d+)"[^>]*>.*?</npc_template>)', re.S)

# Equipamentos pré-resolvidos do client 5.0 (client_npcs.xml + client_items.xml)
EQUIP_GUARDS_LI = [
    # 804100: Sword + Shield
    [100001009, 115001055, 125300028, 110601059, 111601036, 114601016, 112601009, 113601020],
    # 804101: Bow + Arrow
    [101700809, 163000003, 125300028, 110601059, 111601036, 114601016, 112601009, 113601020],
    # 804102: Sword + Dagger
    [100001009, 100200902, 125300028, 110601059, 111601036, 114601016, 112601009, 113601020],
    # 804103: Book
    [100600840, 125300028, 110601059, 111601036, 114601016, 112601009, 113601020],
    # 804104: Mace + Shield
    [100100766, 115001055, 125300028, 110601059, 111601036, 114601016, 112601009, 113601020],
]

EQUIP_GUARDS_DA = [
    # 804105: Sword + Shield
    [100001008, 115001054, 125300029, 110601060, 111601037, 114601017, 112601010, 113601021],
    # 804106: Bow + Arrow
    [101700808, 163000003, 125300029, 110601060, 111601037, 114601017, 112601010, 113601021],
    # 804107: Sword + Dagger
    [100001008, 100200901, 125300029, 110601060, 111601037, 114601017, 112601010, 113601021],
    # 804108: Book
    [100600839, 125300029, 110601060, 111601037, 114601017, 112601010, 113601021],
    # 804109: Mace + Shield
    [100100765, 115001054, 125300029, 110601060, 111601037, 114601017, 112601010, 113601021],
]

EQUIP_DEAD_LI = [125300028, 110601059, 111601036, 114601016, 112601009, 113601020]
EQUIP_DEAD_DA = [125300029, 110601060, 111601037, 114601017, 112601010, 113601021]

EQUIP_GOSSIP_LI = [100000058, 115000734, 125300028, 110601059, 111601036, 114601016, 112601009, 113601020]
EQUIP_GOSSIP_DA = [100000058, 115000738, 125300028, 110601059, 111601036, 114601016, 112601009, 113601020]

EQUIP_TELEPORT_LI = [113500319, 110500336, 112500309, 111500327, 114500331]
EQUIP_TELEPORT_DA = [110900154, 111100277, 114100294, 112100256, 113100276]


def format_equipment(items):
    if not items:
        return ""
    lines = ["\t\t<equipment>"]
    for it in items:
        lines.append(f"\t\t\t<item>{it}</item>")
    lines.append("\t\t</equipment>")
    return "\n" + "\n".join(lines)


def build_template_xml(npc_id):
    """Gera o bloco <npc_template> canônico para o npc_id especificado."""
    # 1. Guardas Elyos (804100..804104)
    if 804100 <= npc_id <= 804104:
        idx = npc_id - 804100
        classes = ["Fi", "Ra", "As", "Wi", "Pr"]
        cname = f"IDTutorialQ_Guard_Li_{classes[idx]}_01"
        equip = format_equipment(EQUIP_GUARDS_LI[idx])
        return (
            f'\t<npc_template npc_id="{npc_id}" level="5" name="{cname}" name_id="465670" title_id="465676" '
            f'height="2.5" group_drop="NONE" rank="DISCIPLINED" rating="NORMAL" race="ELYOS" tribe="IDTUTORIALQ_GUARD_L" '
            f'type="GUARD" ai="aggressive" srange="10" arange="2" attack_speed="2249" hpgauge="3">\n'
            f'\t\t<stats maxHp="3871652">\n'
            f'\t\t\t<speeds walk="1.419" group_walk="1.419" run="6" run_fight="8" group_run_fight="6" />\n'
            f'\t\t</stats>{equip}\n'
            f'\t\t<bound_radius front="0.3125" side="0.4375" upper="2.5" />\n'
            f'\t</npc_template>'
        )

    # 2. Guardas Asmodianos (804105..804109)
    if 804105 <= npc_id <= 804109:
        idx = npc_id - 804105
        classes = ["Fi", "Ra", "As", "Wi", "Pr"]
        cname = f"IDTutorialQ_Guard_Da_{classes[idx]}_01"
        equip = format_equipment(EQUIP_GUARDS_DA[idx])
        return (
            f'\t<npc_template npc_id="{npc_id}" level="5" name="{cname}" name_id="465671" title_id="465677" '
            f'height="2.5" group_drop="NONE" rank="DISCIPLINED" rating="NORMAL" race="ASMODIANS" tribe="IDTUTORIALQ_GUARD_D" '
            f'type="GUARD" ai="aggressive" srange="10" arange="2" attack_speed="2249" hpgauge="3">\n'
            f'\t\t<stats maxHp="3871652">\n'
            f'\t\t\t<speeds walk="1.419" group_walk="1.419" run="6" run_fight="8" group_run_fight="6" />\n'
            f'\t\t</stats>{equip}\n'
            f'\t\t<bound_radius front="0.3125" side="0.4375" upper="2.5" />\n'
            f'\t</npc_template>'
        )

    # 3. Corpos / Cadáveres (804110..804113)
    if 804110 <= npc_id <= 804113:
        is_elyos = npc_id in (804110, 804111)
        gender = "M" if npc_id in (804110, 804112) else "F"
        cname = f"IDTutorialQ_DeadBody_{'Li' if is_elyos else 'Da'}_{gender}"
        name_id = 465672 if is_elyos else 465673
        race = "ELYOS" if is_elyos else "ASMODIANS"
        equip = format_equipment(EQUIP_DEAD_LI if is_elyos else EQUIP_DEAD_DA)
        return (
            f'\t<npc_template npc_id="{npc_id}" level="5" name="{cname}" name_id="{name_id}" '
            f'height="2.5" group_drop="NONE" rank="DISCIPLINED" rating="NORMAL" race="{race}" tribe="NONE" '
            f'type="GENERAL" ai="noaction" flag_type="8" srange="10" arange="2" attack_speed="2249" hpgauge="3">\n'
            f'\t\t<stats maxHp="3871652">\n'
            f'\t\t\t<speeds walk="0" group_walk="0" run="0" run_fight="0" group_run_fight="0" />\n'
            f'\t\t</stats>{equip}\n'
            f'\t\t<bound_radius front="0.3125" side="0.4375" upper="2.5" />\n'
            f'\t</npc_template>'
        )

    # 4. Fofoca Elyos (804114..804123)
    if 804114 <= npc_id <= 804123:
        idx = npc_id - 804113
        cname = f"IDTutorialQ_Gossip_Li_{idx:02d}"
        equip = format_equipment(EQUIP_GOSSIP_LI)
        return (
            f'\t<npc_template npc_id="{npc_id}" level="5" name="{cname}" name_id="465674" title_id="465676" '
            f'height="2" group_drop="NONE" rank="DISCIPLINED" rating="NORMAL" race="ELYOS" tribe="USEALL" '
            f'type="GENERAL" ai="noaction" srange="10" arange="2" attack_speed="2249" hpgauge="3">\n'
            f'\t\t<stats maxHp="3871652">\n'
            f'\t\t\t<speeds walk="0" group_walk="0" run="0" run_fight="0" group_run_fight="0" />\n'
            f'\t\t</stats>{equip}\n'
            f'\t\t<bound_radius front="0.25" side="0.35" upper="2" />\n'
            f'\t</npc_template>'
        )

    # 5. Fofoca Asmodianos (804124..804133)
    if 804124 <= npc_id <= 804133:
        idx = npc_id - 804123
        cname = f"IDTutorialQ_Gossip_Da_{idx:02d}"
        equip = format_equipment(EQUIP_GOSSIP_DA)
        return (
            f'\t<npc_template npc_id="{npc_id}" level="5" name="{cname}" name_id="465675" title_id="465677" '
            f'height="2" group_drop="NONE" rank="DISCIPLINED" rating="NORMAL" race="ASMODIANS" tribe="USEALL" '
            f'type="GENERAL" ai="noaction" srange="10" arange="2" attack_speed="2249" hpgauge="3">\n'
            f'\t\t<stats maxHp="3871652">\n'
            f'\t\t\t<speeds walk="0" group_walk="0" run="0" run_fight="0" group_run_fight="0" />\n'
            f'\t\t</stats>{equip}\n'
            f'\t\t<bound_radius front="0.25" side="0.35" upper="2" />\n'
            f'\t</npc_template>'
        )

    # 6. Inggness (804134, STR_IDTutorialQ_Teleport_Out_Li, Daeva do Tempo do lado Elyos)
    if npc_id == 804134:
        equip = format_equipment(EQUIP_TELEPORT_LI)
        return (
            f'\t<npc_template npc_id="804134" level="5" name="Inggness" name_id="465678" '
            f'height="2.18" group_drop="NONE" rank="DISCIPLINED" rating="NORMAL" race="ELYOS" tribe="USEALL" '
            f'type="GENERAL" ai="idtutorialq_teleport_out_li" srange="25" arange="2" attack_speed="2249" hpgauge="3">\n'
            f'\t\t<stats maxHp="3871652">\n'
            f'\t\t\t<speeds walk="0" group_walk="0" run="0" run_fight="0" group_run_fight="0" />\n'
            f'\t\t</stats>{equip}\n'
            f'\t\t<bound_radius front="0.2725" side="0.3815" upper="2.18" />\n'
            f'\t\t<talk_info distance="3" is_dialog="true" />\n'
            f'\t</npc_template>'
        )

    # 7. Inggril (804135, STR_IDTutorialQ_Teleport_Out_Da, Daeva do Tempo do lado Asmodiano)
    if npc_id == 804135:
        equip = format_equipment(EQUIP_TELEPORT_DA)
        return (
            f'\t<npc_template npc_id="804135" level="5" name="Inggril" name_id="465679" '
            f'height="2" group_drop="NONE" rank="DISCIPLINED" rating="NORMAL" race="ASMODIANS" tribe="USEALL" '
            f'type="GENERAL" ai="idtutorialq_teleport_out_da" srange="25" arange="2" attack_speed="2249" hpgauge="3">\n'
            f'\t\t<stats maxHp="3871652">\n'
            f'\t\t\t<speeds walk="0" group_walk="0" run="0" run_fight="0" group_run_fight="0" />\n'
            f'\t\t</stats>{equip}\n'
            f'\t\t<bound_radius front="0.25" side="0.35" upper="2" />\n'
            f'\t\t<talk_info distance="3" is_dialog="true" />\n'
            f'\t</npc_template>'
        )

    # 8. Controladores e Gatilhos (804136..804155)
    if 804136 <= npc_id <= 804155:
        if npc_id <= 804145:
            idx = npc_id - 804135
            cname = f"IDTutorialQ_Set_Ctrl_NPC_{idx:02d}"
            srange = 20  # sensory_range do cliente; o gatilho dos bosses mediu 17-20 m na captura
        else:
            idx = npc_id - 804145
            cname = f"IDTutorialQ_MSG_Ctrl_NPC_{idx:02d}"
            srange = 10  # sensory_range do cliente; as mensagens comecaram a 5-10 m na captura
        return (
            f'\t<npc_template npc_id="{npc_id}" level="1" name="{cname}" name_id="350000" '
            f'height="2" group_drop="NONE" rank="DISCIPLINED" rating="NORMAL" race="NONE" tribe="USEALL" '
            f'type="GENERAL" ai="noaction" srange="{srange}" arange="2" attack_speed="2000" hpgauge="3">\n'
            f'\t\t<stats maxHp="172">\n'  # S_PUT_NPC oficial
            f'\t\t\t<speeds walk="0" group_walk="0" run="0" run_fight="0" group_run_fight="0" />\n'
            f'\t\t</stats>\n'
            f'\t\t<bound_radius front="0.25" side="0.35" upper="2" />\n'
            f'\t</npc_template>'
        )

    # 9. Baús e Caixas Bônus (804156..804175)
    if 804156 <= npc_id <= 804175:
        # Baús mobs (ataque)
        if npc_id in (804156, 804161, 804168):
            names = {
                804156: ("IDTutorialQ_TREASUREBOX_01_01", 465770),
                804161: ("IDTutorialQ_TREASUREBOX_02_01", 465775),
                804168: ("IDTutorialQ_TREASUREBOX_03_01", 465808),
            }
            cname, name_id = names[npc_id]
            return (
                f'\t<npc_template npc_id="{npc_id}" level="5" name="{cname}" name_id="{name_id}" '
                f'height="2" group_drop="NONE" rank="DISCIPLINED" rating="NORMAL" race="NONE" tribe="MONSTER" '
                f'type="MONSTER" ai="aggressive" srange="10" arange="2" attack_speed="2000" hpgauge="3">\n'
                f'\t\t<stats maxHp="10">\n'
                f'\t\t\t<speeds walk="0" group_walk="0" run="0" run_fight="0" group_run_fight="0" />\n'
                f'\t\t</stats>\n'
                f'\t\t<bound_radius front="0.25" side="0.35" upper="2" />\n'
                f'\t</npc_template>'
            )

        # Baús interativos (action / chest)
        if (804157 <= npc_id <= 804160) or (804162 <= npc_id <= 804165) or (804169 <= npc_id <= 804172):
            if 804157 <= npc_id <= 804160:
                sub = npc_id - 804155
                cname = f"IDTutorialQ_TREASUREBOX_01_{sub:02d}"
                name_id = 465771 + (npc_id - 804157)
            elif 804162 <= npc_id <= 804165:
                sub = npc_id - 804160
                cname = f"IDTutorialQ_TREASUREBOX_02_{sub:02d}"
                name_id = 465776 + (npc_id - 804162)
            else:
                sub = npc_id - 804167
                cname = f"IDTutorialQ_TREASUREBOX_03_{sub:02d}"
                name_id = 465809 + (npc_id - 804169)
            return (
                f'\t<npc_template npc_id="{npc_id}" level="5" name="{cname}" name_id="{name_id}" '
                f'height="2" group_drop="NONE" rank="DISCIPLINED" rating="NORMAL" race="NONE" tribe="FIELD_OBJECT_ALL" '
                f'type="GENERAL" ai="chest" srange="10" arange="2" attack_speed="2000" hpgauge="3">\n'
                f'\t\t<stats maxHp="10">\n'
                f'\t\t\t<speeds walk="0" group_walk="0" run="0" run_fight="0" group_run_fight="0" />\n'
                f'\t\t</stats>\n'
                f'\t\t<bound_radius front="0.25" side="0.35" upper="2" />\n'
                f'\t\t<talk_info distance="5" is_dialog="true" />\n'
                f'\t</npc_template>'
            )

        # NoShow NPCs (804166, 804167)
        if npc_id == 804166:
            return (
                f'\t<npc_template npc_id="804166" level="1" name="IDTutorialQ_NoShowNPC_DarkShadow_Normalfire" name_id="2288143" '
                f'height="2" group_drop="NONE" rank="DISCIPLINED" rating="NORMAL" race="NONE" tribe="NONE" '
                f'type="GENERAL" ai="noaction" srange="10" arange="2" attack_speed="2000" hpgauge="3">\n'
                f'\t\t<stats maxHp="172">\n'  # S_PUT_NPC oficial
                f'\t\t\t<speeds walk="0" group_walk="0" run="0" run_fight="0" group_run_fight="0" />\n'
                f'\t\t</stats>\n'
                f'\t\t<bound_radius front="0.25" side="0.35" upper="2" />\n'
                f'\t</npc_template>'
            )
        if npc_id == 804167:
            return (
                f'\t<npc_template npc_id="804167" level="1" name="IDTutorialQ_NoShowNPC_DarkShadow_Spawn" name_id="350000" '
                f'height="2" group_drop="NONE" rank="DISCIPLINED" rating="NORMAL" race="NONE" tribe="NONE" '
                f'type="GENERAL" ai="noaction" srange="10" arange="2" attack_speed="2000" hpgauge="3">\n'
                f'\t\t<stats maxHp="10">\n'
                f'\t\t\t<speeds walk="0" group_walk="0" run="0" run_fight="0" group_run_fight="0" />\n'
                f'\t\t</stats>\n'
                f'\t\t<bound_radius front="0.25" side="0.35" upper="2" />\n'
                f'\t</npc_template>'
            )

        # Bonus Boxes (804173..804175); level 7 do S_PUT_NPC oficial na 22 e na 23 (a 21 nao aparece nas capturas)
        boxes = {
            804173: ("IDTutorialQ_Content_UI_BonusBox_21", 465851, 5, 6.0, 0.75, 1.05, 6.0),
            804174: ("IDTutorialQ_Content_UI_BonusBox_22", 465852, 7, 4.0, 0.5, 0.7, 4.0),
            804175: ("IDTutorialQ_Content_UI_BonusBox_23", 465853, 7, 2.0, 0.25, 0.35, 2.0),
        }
        cname, name_id, lvl, h, bf, bs, bu = boxes[npc_id]
        h_str = f"{int(h)}" if h.is_integer() else f"{h}"
        bu_str = f"{int(bu)}" if bu.is_integer() else f"{bu}"
        return (
            f'\t<npc_template npc_id="{npc_id}" level="{lvl}" name="{cname}" name_id="{name_id}" '
            f'height="{h_str}" group_drop="NONE" rank="DISCIPLINED" rating="NORMAL" race="NONE" tribe="FIELD_OBJECT_ALL" '
            f'type="GENERAL" ai="chest" srange="10" arange="2" attack_speed="2000" hpgauge="3">\n'
            f'\t\t<stats maxHp="831">\n'
            f'\t\t\t<speeds walk="0" group_walk="0" run="0" run_fight="0" group_run_fight="0" />\n'
            f'\t\t</stats>\n'
            f'\t\t<bound_radius front="{bf}" side="{bs}" upper="{bu_str}" />\n'
            f'\t\t<talk_info distance="5" is_dialog="true" />\n'
            f'\t</npc_template>'
        )

    raise ValueError(f"ID fora da faixa Land of Shadows: {npc_id}")


def process_tree(nome, base, aplicar=False):
    caminho_xml = os.path.join(base, REL_XML)
    caminho_xsd = os.path.join(base, REL_XSD)

    if not os.path.isfile(caminho_xml):
        print(f"[{nome}] Arquivo não encontrado: {caminho_xml}")
        return False

    conteudo = open(caminho_xml, "r", encoding="utf-8", newline="").read()
    substituidos = 0
    novos_blocos = {nid: build_template_xml(nid) for nid in range(804100, 804176)}
    if "\r\n" in conteudo:  # os blocos saem com LF; o checkout (autocrlf) usa CRLF
        novos_blocos = {nid: b.replace("\n", "\r\n") for nid, b in novos_blocos.items()}

    # Mapa de posições dos blocos existentes
    matches = list(BLOCO_RE.finditer(conteudo))
    mapa_pos = {}
    for m in matches:
        nid = int(m.group(2))
        mapa_pos[nid] = (m.start(1), m.end(1), m.group(1))

    # Realiza substituição preservando ordenação
    partes = []
    ultimo_pos = 0

    for m in matches:
        nid = int(m.group(2))
        if 804100 <= nid <= 804175:
            partes.append(conteudo[ultimo_pos:m.start(1)])
            partes.append(novos_blocos[nid])
            ultimo_pos = m.end(1)
            substituidos += 1

    partes.append(conteudo[ultimo_pos:])
    novo_conteudo = "".join(partes)

    print(f"[{nome}] Total de templates substituídos na faixa 804100..804175: {substituidos} de 76")
    if substituidos != 76:
        print(f"[{nome}] AVISO: Esperado 76 templates, mas foram encontrados {substituidos}!")
        return False

    # Validação com lxml e Schema XSD
    print(f"[{nome}] Validando XML resultante contra {REL_XSD}...")
    try:
        xsd = etree.XMLSchema(etree.parse(caminho_xsd))
        doc = etree.fromstring(novo_conteudo.encode("utf-8"), base_url=caminho_xml)
        if not xsd.validate(doc):
            print(f"[{nome}] ERRO: XML não valida no XSD: {xsd.error_log.last_error}")
            return False
        print(f"[{nome}] Validação XSD OK!")
    except Exception as e:
        print(f"[{nome}] Falha ao validar XSD: {e}")
        return False

    if aplicar:
        backup_manager.backup_file_before_modification(caminho_xml)
        with open(caminho_xml, "w", encoding="utf-8", newline="") as f:
            f.write(novo_conteudo)
        print(f"[{nome}] Alterações gravadas com sucesso após backup!")
    else:
        print(f"[{nome}] Modo simulação: nenhuma alteração gravada. Use --aplicar.")

    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--aplicar", action="store_true", help="Grava as alterações nas duas árvores após backup")
    args = parser.parse_args()

    print("=== Correção dos Templates Land of Shadows (804100..804175) ===")
    sucesso_total = True
    for nome, base in ARVORES:
        ok = process_tree(nome, base, aplicar=args.aplicar)
        if not ok:
            sucesso_total = False

    if not args.aplicar:
        print("\nModo simulação concluído. Execute com --aplicar para efetivar as gravações.")
    elif sucesso_total:
        print("\nProcessamento concluído com sucesso nas duas árvores!")
    else:
        print("\nProcessamento finalizado com erros.")
        sys.exit(1)


if __name__ == "__main__":
    main()
