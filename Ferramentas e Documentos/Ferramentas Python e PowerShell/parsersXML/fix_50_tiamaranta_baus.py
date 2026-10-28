"""Baus de Tiamaranta Mesa (800040000) como no oficial 5.0.

Provas (capturas oficiais de 13/09 a 17/09 e cliente 5.0):

* Abertura (08_Spawns_Mapas_Tiamaranta_Mesa 2026-09-16 05:22, um 802182 e um 802183):
  C 0x37 alvo -> C 0xFFFC [oid] -> S 0xC4 [jogador][bau][10000][1] -> 10 s -> S 0xC4 ...[2]
  -> S 0xCC [bau][0] -> S 0xCD lista com 1 item -> S 0xCC [2] -> C 0x6B pega -> S 0xCC [3]
  + S 0x1B item no inventario + S 0x16 [bau][0x0F] some. E o fluxo do ActionItemNpcAI/ChestAI;
  o SM_LOOT_ITEMLIST ja bate com o S 0xCD (20 b). A barra e o talk_delay_time 10 do cliente.
* Loot: 802182 (LDF4b_TreasureBox_A) -> 188055450 x1; 802183 (LDF4b_TreasureBox_B) -> 188055451 x1.
* Nivel 75, maxHp 31143 e nome ja batiam com o S_PUT_NPC.
* Pontos (mission_mission0.xml x S_PUT_NPC, "perto" = outro NPC visto a <= 20 m):
  - 750045 (LDF4b_Tiamat_TREASUREBOX_01c): perto 109 vezes, bau 0 vezes -> o oficial nao o poe.
  - 802182: 42 de 47 -> todos os pontos, fixo.
  - 802183 SmallBox_Down: 5 de 5 -> fixo. TreasureBox_B_L: os 14 pontos cobertos numa sessao e
    1 bau; B_R 1 de 10; B_M 0 de 11 -> um bau por grupo (pool 1), sorteado de novo no respawn.
  - 802183 MiddleBox_Sky_*: so 1 ponto coberto (com bau) -> sem prova de sorteio, fica fixo.

* Greater (802184 sem ponto no mapa, 802536 nos 3 SP SmallBox_Down): nunca visto nas capturas. Barra de
  30 s e objeto de abrir pelo client_npcs; caixa 188055452 informada pelo usuario. A pagina 186020354 sai
  ao abrir a caixa (decomposable_items + STR_WRAP_LDF4B_DRAGON_RECORD_BOX_0x_DESC), nao do bau no chao.

Sem prova ainda: respawn_time (295 do SpawnParser), se o loot varia (uma abertura de cada) e o Greater.

Saida: templates, chest_templates, custom_drop, o arquivo do mapa (750045 sai, 802183 fixo)
e 800040000_Tiamaranta_Mesa_Baus.xml (802183 sorteado), nas duas arvores.

Uso: python fix_50_tiamaranta_baus.py   (idempotente)
"""

import math
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
ARVORES = [
    os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data", "static_data"),
    os.path.join(RAIZ, "Emulador - Produto Final", "GameServer", "data", "static_data"),
]
MISSION = os.path.join(RAIZ, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos",
                       "levels", "LDF4b", "mission_mission0.xml")
SPAWN = os.path.join("spawns", "Npcs", "800040000_Tiamaranta_Mesa.xml")
SPAWN_BAUS = os.path.join("spawns", "Npcs", "800040000_Tiamaranta_Mesa_Baus.xml")

LOOT = {802182: 188055450, 802183: 188055451,
        802184: 188055452, 802536: 188055452}      # Greater: caixa _03 informada pelo usuario (sem captura)
TALK_DELAY = {802182: 10, 802183: 10, 802184: 30, 802536: 30}   # talk_delay_time do cliente; S 0xC4 = x1000 ms
FONTE = {802182: "captura 16/09 05:22", 802183: "captura 16/09 05:22",
         802184: "cliente + usuario, sem captura", 802536: "cliente + usuario, sem captura"}
# O 802536 veio com atributos de outro NPC (ai aggressive, raca, aggro, dialogo). No cliente ele nao tem
# race_type, tem talking_distance 3 e ui_type craft: e objeto de abrir, como os outros baus.
LIMPA = {802536: ("race", "srange", "arange", "cancel_level")}
POOL_802183 = [                         # (prefixo do SP no editor, pool; 0 = todos os pontos)
    ("SP_LDF4b_SmallBox_Down_", 0),
    ("SP_LDF4b_MiddleBox_Sky_N_E_", 0),
    ("SP_LDF4b_MiddleBox_Sky_S_W_", 0),
    ("SP_LDF4b_TreasureBox_B_L", 1),
    ("SP_LDF4b_TreasureBox_B_M", 1),
    ("SP_LDF4b_TreasureBox_B_R", 1),
]


def le(caminho):
    with open(caminho, encoding="utf-8", newline="") as f:
        return f.read()


def grava(caminho, texto, antigo):
    if texto != antigo:
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(texto)
        print("  gravado", os.path.relpath(caminho, RAIZ))


def sp_do_editor(npc_nome):
    t = le(MISSION)
    pontos = []
    for m in re.finditer(r"<Object ([^>]*?)/?>", t):
        a = m.group(1)
        if f'npc="{npc_nome}"' not in a:
            continue
        x, y, _ = map(float, re.search(r'Pos="([^"]*)"', a).group(1).split(","))
        pontos.append((x, y, re.sub(r"\d+$", "", re.search(r'Name="([^"]*)"', a).group(1))))
    return pontos


def templates(t):
    for npc in LOOT:
        m = re.search(rf'(\t<npc_template npc_id="{npc}"[^>]*>)(.*?</npc_template>)', t, re.S)
        cab, corpo = m.group(1), m.group(2)
        cab = re.sub(r'\bai="[^"]*"', 'ai="chest"', cab)
        for a in LIMPA.get(npc, ()):
            cab = re.sub(rf'\s{a}="[^"]*"', "", cab)
        if npc in LIMPA:
            corpo = re.sub(r"<talk_info [^>]*/>",
                           f'<talk_info distance="3" delay="{TALK_DELAY[npc]}" can_talk_invisible="false" />', corpo)
        corpo = re.sub(r'(<talk_info[^>]*\bdelay=")\d+(")', rf"\g<1>{TALK_DELAY[npc]}\2", corpo)
        t = t[:m.start()] + cab + corpo + t[m.end():]
    return t


def fim_de_linha(t):
    return "\r\n" if "\r\n" in t else "\n"


def chests(t):
    nl = fim_de_linha(t)
    for npc in LOOT:
        if f'<chest npc_id="{npc}">' not in t:
            t = t.replace("</chest_templates>",
                          f'\t<!-- Tiamaranta Mesa: abre sem chave ({FONTE[npc]}) -->{nl}'
                          f'\t<chest npc_id="{npc}">{nl}\t\t<key_item item_ids="0" count="1" />{nl}\t</chest>{nl}'
                          "</chest_templates>")
    return t


def drops(t):
    nl = fim_de_linha(t)
    for npc, item in LOOT.items():
        bloco = (f'\t<!-- Tiamaranta Mesa: 1 item por abertura ({FONTE[npc]}) -->{nl}'
                 f'\t<npc_drop npc_id="{npc}">{nl}\t\t<drop_group max_items="1">{nl}'
                 f'\t\t\t<drop item_id="{item}" />{nl}\t\t</drop_group>{nl}\t</npc_drop>{nl}')
        if f'<npc_drop npc_id="{npc}">' in t:
            continue
        t = t.replace("</custom_drop>", bloco + "</custom_drop>")
    return t


def spawns(t, extra_antigo, sp_b, guarda_750045):
    """Devolve (arquivo do mapa, arquivo dos baus sorteados).

    O spawns.xsd so aceita um <spawn> por npc em cada <spawn_map> (unique-npc-id), e o
    runtime junta varios <spawn_map> do mesmo mapa numa lista de SpawnGroup por npc. Os pontos
    fixos do 802183 ficam no arquivo do mapa; cada grupo sorteado vai num <spawn_map> proprio
    do arquivo separado, para nao quebrar quem le o arquivo do mapa como um <spawn_map> so.
    """
    # 750045: o oficial nao poe nesses pontos. O bloco sai, guardado em arquivo para restaurar.
    m = re.search(r'[ \t]*<!--[^\n]*-->\r?\n[ \t]*<spawn npc_id="750045"[^>]*>.*?</spawn>\r?\n', t, re.S) \
        or re.search(r'[ \t]*<spawn npc_id="750045"[^>]*>.*?</spawn>\r?\n', t, re.S)
    if m:
        with open(guarda_750045, "w", encoding="utf-8", newline="") as f:
            f.write(m.group(0))
        print("  750045 retirado; bloco salvo em", guarda_750045)
        t = t[:m.start()] + t[m.end():]

    rx = r'[ \t]*(?:<!--[^\n]*-->\r?\n[ \t]*)?<spawn npc_id="802183"([^>]*)>(.*?)</spawn>\r?\n'
    blocos = list(re.finditer(rx, t, re.S))
    if not blocos:
        sys.exit("802183 sem spawn no arquivo do mapa")
    nl = fim_de_linha(t)
    resp = re.search(r'respawn_time="(\d+)"', blocos[0].group(1)).group(1)
    por_grupo = {g: [] for g, _ in POOL_802183}
    for b in blocos + list(re.finditer(rx, extra_antigo, re.S)):
        for s in re.finditer(r"[ \t]*<spot [^>]*/>", b.group(2)):
            x = float(re.search(r'x="([^"]*)"', s.group(0)).group(1))
            y = float(re.search(r'y="([^"]*)"', s.group(0)).group(1))
            d, g = min((math.hypot(x - p[0], y - p[1]), p[2]) for p in sp_b)
            if d > 0.5 or g not in por_grupo:
                sys.exit(f"ponto do 802183 fora dos SP do editor: {x} {y} ({g}, {d:.2f} m)")
            if s.group(0).strip() not in por_grupo[g]:
                por_grupo[g].append(s.group(0).strip())

    def bloco(grupos, pool, ind):
        spots = [s for g in grupos for s in por_grupo[g]]
        nomes = ", ".join(g.rstrip("_") for g in grupos)
        nota = f"sorteia {pool} de {len(spots)}" if pool else f"todos os {len(spots)} pontos"
        attr = f' pool="{pool}"' if pool else ""
        return (f"{ind}<!-- 802183 {nomes}: {nota} (capturas 16-17/09, fix_50_tiamaranta_baus.py) -->{nl}"
                f'{ind}<spawn npc_id="802183" respawn_time="{resp}"{attr}>{nl}'
                + "".join(f"{ind}\t{s}{nl}" for s in spots) + f"{ind}</spawn>{nl}")

    fixos = [g for g, pool in POOL_802183 if not pool and por_grupo[g]]
    ini, fim = blocos[0].start(), blocos[-1].end()
    meio = t[ini:fim]
    for b in blocos:
        meio = meio.replace(b.group(0), "", 1)
    if meio.strip():
        sys.exit("ha outros spawns entre os blocos do 802183; separar a mao")
    t = t[:ini] + bloco(fixos, 0, "\t\t") + t[fim:]

    extra = ('<?xml version="1.0" encoding="utf-8"?>' + nl
             + '<spawns xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">' + nl
             + "\t<!-- Baus 802183 de Tiamaranta Mesa sorteados por grupo do editor (SP_LDF4b_TreasureBox_B_L/M/R)." + nl
             + "\t     Um <spawn_map> por grupo porque o spawns.xsd aceita um <spawn> por npc em cada <spawn_map>;" + nl
             + "\t     os pontos fixos do mesmo npc estao em 800040000_Tiamaranta_Mesa.xml. -->" + nl)
    for g, pool in POOL_802183:
        if pool and por_grupo[g]:
            extra += f'\t<spawn_map map_id="800040000">{nl}' + bloco([g], pool, "\t\t") + f"\t</spawn_map>{nl}"
    extra += "</spawns>" + nl
    return t, extra


def main():
    sp_b = sp_do_editor("LDF4b_TreasureBox_B")
    for n, raiz in enumerate(ARVORES):
        print(raiz)
        for rel, f in ((os.path.join("npcs", "npc_templates.xml"), templates),
                       (os.path.join("chests", "chest_templates.xml"), chests),
                       (os.path.join("custom_drop", "custom_drop.xml"), drops)):
            c = os.path.join(raiz, rel)
            antigo = le(c)
            grava(c, f(antigo), antigo)
        c, ce = os.path.join(raiz, SPAWN), os.path.join(raiz, SPAWN_BAUS)
        antigo = le(c)
        extra_antigo = le(ce) if os.path.isfile(ce) else ""
        guarda = os.path.join(os.environ.get("BAUS_GUARDA", AQUI), f"tiamaranta_750045_retirado_{n}.xml.txt")
        novo, extra = spawns(antigo, extra_antigo, sp_b, guarda)
        grava(c, novo, antigo)
        grava(ce, extra, extra_antigo)


if __name__ == "__main__":
    main()
