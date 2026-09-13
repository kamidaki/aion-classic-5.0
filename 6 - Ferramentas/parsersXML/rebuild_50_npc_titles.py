#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_50_npc_titles.py

Conserta o title_id dos npc_templates: o titulo que aparece embaixo do nome do NPC. Ele e herdado da 4.8 e, com os
ids reaproveitados pela NCSoft, milhares de NPCs mandam um id de string que o cliente 5.0 nao tem -- e o cliente
desenha "???" no lugar do titulo. Caso que mostrou: Adel 800825 com 370623, que nao existe em nenhum
client_strings; o certo e 465403 (STR_NPCTITLE_CORPS_SUPPORT_EQUIP_SELLER).

A regra e uma so e vem do cliente: o D@32 do S_PUT_NPC oficial e o id da string cujo <name> e o <npc_title> do
client_npcs.xml, e 0 quando o NPC nao tem npc_title. Conferida em todas as capturas 5.0 com S_KEY: 617 de 617
NPCs distintos. Nome de string nao se repete entre os client_strings_*.xml, entao a busca e direta.

O npc_title2 (titulo colorido de alguns teleportadores) nao e esse campo: os NPCs que so tem npc_title2 vao com 0
na captura, e continuam com 0 aqui.

Uso (a pasta do cliente e a que contem data/ e Strings/):
    python rebuild_50_npc_titles.py --cliente "<pasta dos XMLs do cliente 5.0>"            (mostra e gera relatorio)
    python rebuild_50_npc_titles.py --cliente "<pasta dos XMLs do cliente 5.0>" --aplicar  (grava com backup)
A pasta tambem pode vir da variavel de ambiente AION_CLIENT_XML_DIR.
"""

import argparse
import collections
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402
from rebuild_50_item_templates import DEFAULT_CLIENT_DIR  # noqa: E402

REL_XML = os.path.join("npcs", "npc_templates.xml")
REL_XSD = os.path.join("npcs", "npcs.xsd")
RELATORIO_TEMPLATES = os.path.join(PARSERS_DIR, "relatorio_npc_templates_50.txt")
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_npc_titles_50.txt")
TAG_RE = re.compile(r"<npc_template\b([^>]*?)(/?)>")
# TalkEventHandler desvia o dialogo de quem tem esse titulo (aldeao de Oriel/Pernon da 4.8)
TITULOS_COM_CODIGO = {462877}


def le_strings(cliente):
    """nome da string (minusculas) -> (id, arquivo). Aborta se o mesmo nome aparecer com ids diferentes."""
    out = {}
    for f in sorted(glob.glob(os.path.join(cliente, "data", "Strings", "client_strings_*.xml"))):
        texto = open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"<id>(\d+)</id>\s*<name>([^<]+)</name>", texto):
            nome, sid = m.group(2).strip().lower(), int(m.group(1))
            if nome in out and out[nome][0] != sid:
                sys.exit("string {} tem dois ids ({} e {}): a busca por nome nao e direta.".format(nome, out[nome][0], sid))
            out.setdefault(nome, (sid, os.path.basename(f)))
    return out


def le_cliente(path):
    """npc_id -> npc_title (minusculas, vazio se nao tiver)."""
    txt = open(path, encoding="utf-8", errors="replace").read()
    out = {}
    for m in re.finditer(r"<npc_client>(.*?)</npc_client>", txt, re.S):
        b = m.group(1)
        i = re.search(r"<id>(\d+)</id>", b)
        if not i:
            continue
        t = re.search(r"<npc_title>([^<]*)</npc_title>", b)
        out[i.group(1)] = t.group(1).strip().lower() if t else ""
    return out


def ids_trocados(path):
    """Os npcs cujo id mudou de dono na 5.0, do relatorio do rebuild_50_npc_templates: o resto e o gabarito."""
    if not os.path.isfile(path):
        return set()
    return {m.group(1) for l in open(path, encoding="utf-8") if (m := re.match(r"\s*(\d+)\s+(SIM|-)\s", l))}


def novo_atributos(attrs, titulo):
    """Troca, poe ou tira so o title_id; o resto da tag fica byte a byte como estava."""
    if re.search(r'\stitle_id="[^"]*"', attrs):
        if titulo:
            return re.sub(r'(\stitle_id=")[^"]*(")', r"\g<1>{}\g<2>".format(titulo), attrs)
        return re.sub(r'\stitle_id="[^"]*"', "", attrs)
    if not titulo:
        return attrs
    nid = re.search(r'\sname_id="[^"]*"', attrs)
    pos = nid.end() if nid else len(attrs.rstrip())
    return attrs[:pos] + ' title_id="{}"'.format(titulo) + attrs[pos:]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    npcs_xml = os.path.join(args.cliente, "data", "npcs", "client_npcs.xml")
    if not os.path.isfile(npcs_xml):
        sys.exit("Arquivo do cliente nao encontrado: " + npcs_xml + ". Informe --cliente ou AION_CLIENT_XML_DIR.")

    print("1. Lendo strings do cliente, client_npcs e npc_templates...")
    strings = le_strings(args.cliente)
    cli = le_cliente(npcs_xml)
    caminho = os.path.join(backup_manager.SERVER_DATA_DIR, REL_XML)
    with open(caminho, encoding="utf-8", newline="") as f:  # preserva o fim de linha do arquivo
        text = f.read()
    trocados = ids_trocados(RELATORIO_TEMPLATES)
    print("   strings: {} | cliente: {} | trocados na 5.0: {}".format(len(strings), len(cli), len(trocados)))

    sem_string = collections.Counter(t for t in cli.values() if t and t not in strings)

    print("2. Reescrevendo o title_id...")
    edits, linhas = [], []
    total = gab = gab_ok = 0
    motivos = collections.Counter()
    for m in TAG_RE.finditer(text):
        attrs = m.group(1)
        a = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
        npc = a.get("npc_id")
        if not npc or npc not in cli:  # o cliente 5.0 nao conhece esse npc: nao ha o que provar
            continue
        total += 1
        atual = int(a.get("title_id", "0") or 0)
        titulo = strings.get(cli[npc], (0,))[0] if cli[npc] else 0
        if npc not in trocados:
            gab += 1
            gab_ok += atual == titulo
        if atual == titulo:
            continue
        if titulo == 0:
            motivos["tirado (cliente nao tem npc_title)"] += 1
        elif atual == 0:
            motivos["posto (servidor nao tinha)"] += 1
        else:
            motivos["trocado"] += 1
        novo = novo_atributos(attrs, titulo)
        edits.append((m.start(1), m.end(1), novo))
        linhas.append((npc, a.get("name", ""), atual, titulo, cli[npc], npc in trocados))
    print("   {} templates conhecidos pelo cliente | {} mudam | {}".format(total, len(linhas), dict(motivos)))
    print("   gabarito (id nao trocado): {} de {} ja batiam ({:.1f}%)".format(gab_ok, gab, 100 * gab_ok / max(gab, 1)))

    com_codigo = [l for l in linhas if l[3] in TITULOS_COM_CODIGO]
    if com_codigo:
        sys.exit("titulo com desvio no TalkEventHandler iria para {}: nada foi gravado.".format([l[0] for l in com_codigo]))

    out, pos = [], 0
    for a, b, novo in edits:
        out.append(text[pos:a])
        out.append(novo)
        pos = b
    out.append(text[pos:])
    novo_texto = "".join(out)

    print("3. Conferindo o resultado...")
    ids_validos = {sid for sid, _f in strings.values()}
    invalidos = [t for t in re.findall(r'<npc_template\b[^>]*?\stitle_id="(\d+)"', novo_texto) if int(t) not in ids_validos]
    fora_do_cliente = len(invalidos)
    print("   title_id que o cliente nao resolve: {} (so em templates que o cliente 5.0 nao tem)".format(fora_do_cliente))

    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, REL_XSD)))
    if not schema.validate(etree.fromstring(novo_texto.encode("utf-8"))):
        for e in list(schema.error_log)[:20]:
            print("   XSD linha {}: {}".format(e.line, e.message))
        sys.exit("XSD invalido: nada foi gravado.")
    print("   XSD valido.")

    if linhas:
        relatorio(linhas, motivos, gab_ok, gab, sem_string, strings)
    else:  # rodar de novo depois de aplicar nao acha mais nada: nao apagar o relatorio bom
        print("   nada a mudar; relatorio anterior mantido.")

    if not args.aplicar:
        print("Sem --aplicar: nada foi gravado.")
        return
    backup_manager.backup_file_before_modification(REL_XML)
    for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
        p = os.path.join(base, REL_XML)
        with open(p, "wb") as f:
            f.write(novo_texto.encode("utf-8"))
        print("Gravado: " + p)


def relatorio(linhas, motivos, gab_ok, gab, sem_string, strings):
    nome_de = {sid: nome for nome, (sid, _f) in strings.items()}
    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("title_id canonizado pelo cliente 5.0: id da string cujo nome e o <npc_title> do client_npcs.xml.\n")
        f.write("Regra conferida no S_PUT_NPC oficial (617 de 617 NPCs das capturas com S_KEY).\n\n")
        f.write("{} templates mudam: {}\n".format(len(linhas), dict(motivos)))
        f.write("Gabarito (id nao trocado na 5.0): {} de {} ja estavam certos.\n".format(gab_ok, gab))
        inexistentes = sum(1 for l in linhas if l[2] and l[2] not in nome_de)
        f.write("{} mandavam um id que nao existe em client_strings nenhum -- esses sao os \"???\" no jogo.\n".format(inexistentes))
        if sem_string:
            f.write("\n{} npc_title do cliente nao tem string e vao com 0 (o cliente tambem nao teria o que mostrar):\n".format(
                len(sem_string)))
            for t, n in sem_string.most_common():
                f.write("  {:>4}  {}\n".format(n, t))
        f.write("\n{:>8}  {:24}  {:>7}  {:40}  {:>7}  {}\n".format("npc_id", "nome", "antes", "string de antes", "depois",
                                                                   "npc_title do cliente"))
        for npc, nome, atual, titulo, npc_title, _troc in linhas:
            antes = nome_de.get(atual, "INEXISTENTE") if atual else "-"
            f.write("{:>8}  {:24}  {:>7}  {:40}  {:>7}  {}\n".format(npc, nome[:24], atual, antes[:40], titulo,
                                                                     npc_title or "-"))
    print("   relatorio: " + RELATORIO)


if __name__ == "__main__":
    main()
