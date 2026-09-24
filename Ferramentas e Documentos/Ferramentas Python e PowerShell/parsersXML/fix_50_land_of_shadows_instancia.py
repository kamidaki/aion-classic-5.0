#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_land_of_shadows_instancia.py

Registra a Land of Shadows (IDTutorialQ, world 390000000) como instancia no servidor.

Sem instance="true" no world_maps.xml o mapa sobe como mundo aberto e o
InstanceService.getNextAvailableInstance lanca UnsupportedOperationException no teletransporte do guarda da capital
(quests 10153/20153, var 0 -> 1): a var ja foi gravada, o jogador fica na capital e a campanha trava.

De onde vem cada dado
  world_maps.xml          instance="true": o cliente trata o IDTutorialQ como instancia (client_instance_cooltime id 110).
                          Tira o BIND das flags: nenhuma das outras instancias do servidor deixa registrar ponto de
                          retorno la dentro (o ponto sumiria junto com a instancia).
  instance_cooltimes.xml  client_instance_cooltime id 110: max_member 1/1, nivel 1-75 nas duas racas, sem mentor.
                          O cliente nao tem cooltime nem limite de entradas para ela (replay_criteria_count 0), entao
                          vai sem type/ent_cool_time/maxcount (maxcount 0 = entrada livre no InstanceCooltimeData).
                          Sem sync_id: o 110 do cliente ja esta em uso por dois ids herdados da 4.8 (301260000 e
                          301300000) e o syncIdToMapId trocaria o mapa deles.
  instance_exit.xml       saida dos Asmodianos pela captura subida-1-60-2026-08-28.pcapng (acao 104 da Inggril 804135:
                          Pandaemonium 120010000, 1469 1450 176.93 h30). Nao ha captura Elyos do tutorial; sem saida
                          cadastrada o TeleportService.moveToInstanceExit leva ao ponto de retorno (bind).
  chest_templates.xml     um <chest> sem chave (item_ids 0) para cada template da faixa 804100..804175 com ai="chest":
                          sem ele o ChestAI so registra "Missing chest template" e o bau nao abre. Na captura os baus
                          abrem pela barra de uso (S_GAUGE 3000/5000 ms) e dao loot sem gastar item (nenhum
                          S_REMOVE_INVENTORY na sessao da instancia).

A pasta do cliente (a que contem data/) pode vir da variavel de ambiente AION_CLIENT_XML_DIR.
Cada arvore e lida, validada contra o XSD e gravada separadamente.

Uso:
    python fix_50_land_of_shadows_instancia.py              (mostra o que muda, sem gravar)
    python fix_50_land_of_shadows_instancia.py --aplicar    (grava as duas arvores, com backup)
"""

import argparse
import os
import re
import sys

from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import backup_manager  # noqa: E402

ARVORES = (("fonte", backup_manager.SERVER_DATA_DIR), ("produto", backup_manager.PRODUTO_FINAL_DATA_DIR))
CLIENTE = os.path.join(os.environ.get("AION_CLIENT_XML_DIR") or os.path.join(
    backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos"),
    "data", "world", "client_instance_cooltime.xml")
CRLF = "\r\n"
WORLD_ID = 390000000
CODINOME = "IDTutorialQ"
# subida-1-60-2026-08-28.pcapng: acao 104 da Inggril (804135) -> S_REQ_TELEPORT para Pandaemonium
SAIDAS = (("ASMODIANS", 120010000, "1469", "1450", "176.93", "30"),)

ARQUIVOS = {
    "world_maps.xml": "world_maps.xsd",
    "instance_cooltimes/instance_cooltimes.xml": "instance_cooltimes/instance_cooltimes.xsd",
    "instance_exit/instance_exit.xml": "instance_exit/instance_exit.xsd",
    "chests/chest_templates.xml": "chests/chest_templates.xsd",
}
FAIXA_NPC = range(804100, 804176)


def baus_da_instancia(base):
    with open(os.path.join(base, "npcs", "npc_templates.xml"), encoding="utf-8") as f:
        texto = f.read()
    return sorted(int(m.group(1)) for m in re.finditer(r'<npc_template npc_id="(\d+)"[^>]*\bai="chest"', texto)
                  if int(m.group(1)) in FAIXA_NPC)


def baus(texto, ids):
    faltam = [i for i in ids if 'npc_id="%d"' % i not in texto]
    if not faltam:
        return texto, None
    bloco = "".join('\t<chest npc_id="%d">\n\t\t<key_item item_ids="0" count="1" />\n\t</chest>\n' % i for i in faltam)
    fim = texto.rindex("</chest_templates>")
    return texto[:fim] + bloco + texto[fim:], "+%d baus: %s" % (len(faltam), " ".join(map(str, faltam)))


def le_cliente():
    raiz = etree.parse(CLIENTE).getroot()
    for c in raiz.iter("client_instance_cooltime"):
        if (c.findtext("name") or "").strip() == CODINOME:
            return {e.tag: (e.text or "").strip() for e in c}
    sys.exit(CODINOME + " nao encontrado em " + CLIENTE)


def world_maps(texto):
    m = re.search(r'\t<map id="%d"[^>]*/>' % WORLD_ID, texto)
    if not m:
        sys.exit("map %d ausente no world_maps.xml" % WORLD_ID)
    linha = m.group(0)
    nova = linha
    if 'instance="true"' not in nova:
        nova = nova.replace('cName="%s"' % CODINOME, 'cName="%s" instance="true"' % CODINOME, 1)
    nova = re.sub(r'flags="([^"]*)"', lambda f: 'flags="%s"' % " ".join(x for x in f.group(1).split() if x != "BIND"),
                  nova, count=1)
    return texto.replace(linha, nova, 1), (linha, nova)


def cooltimes(texto, cli):
    if re.search(r'worldId="%d"' % WORLD_ID, texto):
        return texto, None
    ocupado = re.search(r'<instance_cooltime\b[^>]*\bid="%s"' % cli["id"], texto)
    if ocupado:
        sys.exit("id %s ja usado no instance_cooltimes.xml: %s" % (cli["id"], ocupado.group(0)))
    mentor = "true" if cli.get("can_enter_mentor", "").upper() == "TRUE" else "false"
    bloco = ('\t<instance_cooltime race="PC_ALL" worldId="{w}" id="{id}">\n'
             '\t\t<max_member_light>{ml}</max_member_light>\n'
             '\t\t<max_member_dark>{md}</max_member_dark>\n'
             '\t\t<enter_min_level_light>{nl}</enter_min_level_light>\n'
             '\t\t<enter_max_level_light>{xl}</enter_max_level_light>\n'
             '\t\t<enter_min_level_dark>{nd}</enter_min_level_dark>\n'
             '\t\t<enter_max_level_dark>{xd}</enter_max_level_dark>\n'
             '\t\t<can_enter_mentor>{mentor}</can_enter_mentor>\n'
             '\t</instance_cooltime>\n').format(
        w=WORLD_ID, id=cli["id"], ml=cli["max_member_light"], md=cli["max_member_dark"],
        nl=cli["enter_min_level_light"], xl=cli["enter_max_level_light"], nd=cli["enter_min_level_dark"],
        xd=cli["enter_max_level_dark"], mentor=mentor)
    fim = texto.rindex("</instance_cooltimes>")
    return texto[:fim] + bloco + texto[fim:], bloco


def saidas(texto):
    linhas = []
    for raca, mundo, x, y, z, h in SAIDAS:
        if re.search(r'instance_id="%d"[^>]*race="%s"' % (WORLD_ID, raca), texto):
            continue
        linhas.append('\t<instance_exit instance_id="%d" exit_world="%d" race="%s" x="%s" y="%s" z="%s" h="%s" />\n'
                      % (WORLD_ID, mundo, raca, x, y, z, h))
    if not linhas:
        return texto, None
    bloco = "\t<!-- Land of Shadows (IDTutorialQ) -->\n" + "".join(linhas)
    fim = texto.rindex("</instance_exits>")
    return texto[:fim] + bloco + texto[fim:], bloco


def valida(base, rel, texto):
    xsd = etree.XMLSchema(etree.parse(os.path.join(base, ARQUIVOS[rel])))
    doc = etree.fromstring(texto.encode("utf-8"), base_url=os.path.join(base, rel))
    if not xsd.validate(doc):
        for e in list(xsd.error_log)[:10]:
            print("   XSD linha {}: {}".format(e.line, e.message))
        return False
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    cli = le_cliente()
    print("cliente: {} id {} membros {}/{} nivel {}-{}".format(CODINOME, cli["id"], cli["max_member_light"],
                                                               cli["max_member_dark"], cli["enter_min_level_light"],
                                                               cli["enter_max_level_light"]))
    ok = True
    gravar = []
    for nome, base in ARVORES:
        print("[{}]".format(nome))
        for rel in ARQUIVOS:
            caminho = os.path.join(base, rel)
            with open(caminho, encoding="utf-8", newline="") as f:
                texto = f.read()
            if rel == "world_maps.xml":
                novo, mud = world_maps(texto)
                mud = None if mud[0] == mud[1] else "{}\n   -> {}".format(mud[0].strip(), mud[1].strip())
            elif rel.startswith("instance_cooltimes"):
                novo, mud = cooltimes(texto, cli)
            elif rel.startswith("chests"):
                novo, mud = baus(texto, baus_da_instancia(base))
            else:
                novo, mud = saidas(texto)
            if mud and CRLF in texto:  # os blocos sao montados com LF; o arquivo usa CRLF
                novo = re.sub(r"(?<!\r)\n", CRLF, novo)
            if not mud or novo == texto:
                print("  {}: nada a mudar".format(rel))
                continue
            print("  {}:\n   {}".format(rel, mud.strip().replace("\n", "\n   ")))
            if not valida(base, rel, novo):
                print("  {}: XSD invalido".format(rel))
                ok = False
                continue
            print("  {}: XSD valido".format(rel))
            gravar.append((caminho, novo))

    if not ok:
        sys.exit("Erro de validacao: nada foi gravado.")
    if not args.aplicar:
        print("Sem --aplicar: nada foi gravado.")
        return
    for caminho, novo in gravar:
        backup_manager.backup_file_before_modification(caminho)
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(novo)
        print("Gravado: " + caminho)


if __name__ == "__main__":
    main()
