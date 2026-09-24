#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_50_skill_templates.py

Devolve ao skill_templates.xml os cinco atributos que o parse_skills.py apagava. Ele lia do client_skills.xml tags
que nao existem (skilltype, activation, cooldown, duration) e gravava o default em toda skill: tudo PHYSICAL, tudo
ACTIVE, cast time 0 e cooldown 0. No jogo isso aparece como skill que ignora o cast time, passiva que nao aplica e
magia calculada como golpe fisico.

    atributo do servidor   campo do client_skills.xml     conferido
    duration (cast, ms)    casting_delay                  12113 de 12113 na versao anterior ao e66f527b5
    cooldown (1/10 s)      delay_time / 100               12094 de 12113 na mesma versao
    delayId                delay_id (grupo de cooldown)   7288 de 7292 na mesma versao
    activation             activation_attribute           Active/Passive/Provoked/Toggle/Maintain = ActivationAttribute
    skilltype              type                           Magical/Physical = SkillType

activation e skilltype ja estavam quebrados antes daquele commit, entao nao ha versao boa para servir de gabarito;
os valores do cliente, em maiusculas, sao exatamente os nomes dos enums do Java. Campo ausente no cliente nao muda
nada. O lvl nao tem fonte no cliente e fica como esta.

Uso (a pasta do cliente e a que contem data/ e Strings/):
    python rebuild_50_skill_templates.py --cliente "<pasta dos XMLs do cliente 5.0>"            (mostra e gera relatorio)
    python rebuild_50_skill_templates.py --cliente "<pasta dos XMLs do cliente 5.0>" --aplicar  (grava com backup)
A pasta tambem pode vir da variavel de ambiente AION_CLIENT_XML_DIR.
"""

import argparse
import collections
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402
from rebuild_50_item_templates import DEFAULT_CLIENT_DIR  # noqa: E402

REL_XML = os.path.join("skills", "skill_templates.xml")
REL_XSD = os.path.join("skills", "skills.xsd")
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_skill_templates_50.txt")
TAG_RE = re.compile(r"<skill_template\b([^>]*?)(/?)>")
CAMPOS = ("duration", "cooldown", "delayId", "activation", "skilltype")


def le_cliente(path):
    """skill_id -> valores que o servidor deve ter, so dos campos que o cliente traz."""
    txt = open(path, encoding="utf-8", errors="replace").read()
    out = {}
    resto_cooldown = 0
    for m in re.finditer(r"<skill_base_client>(.*?)</skill_base_client>", txt, re.S):
        b = m.group(1)

        def campo(nome):
            v = re.search(r"<" + nome + r">([^<]*)</" + nome + r">", b)
            return v.group(1).strip() if v else ""

        sid = campo("id")
        if not sid:
            continue
        valores = {"duration": str(int(float(campo("casting_delay") or 0))), "cooldown": None}
        delay = int(float(campo("delay_time") or 0))
        valores["cooldown"] = str(delay // 100)
        if delay % 100:
            resto_cooldown += 1
        if campo("delay_id"):
            valores["delayId"] = campo("delay_id")
        if campo("activation_attribute"):
            valores["activation"] = campo("activation_attribute").upper()
        if campo("type"):
            valores["skilltype"] = campo("type").upper()
        out[sid] = valores
    return out, resto_cooldown


def troca(attrs, nome, valor):
    return re.sub(r'(\s' + nome + r'=")[^"]*(")', lambda m: m.group(1) + valor + m.group(2), attrs)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    skills_xml = os.path.join(args.cliente, "data", "skills", "client_skills.xml")
    if not os.path.isfile(skills_xml):
        sys.exit("Arquivo do cliente nao encontrado: " + skills_xml + ". Informe --cliente ou AION_CLIENT_XML_DIR.")

    print("1. Lendo client_skills e skill_templates...")
    cli, resto_cooldown = le_cliente(skills_xml)
    caminho = os.path.join(backup_manager.SERVER_DATA_DIR, REL_XML)
    with open(caminho, encoding="utf-8", newline="") as f:  # preserva o fim de linha do arquivo
        text = f.read()
    print("   cliente: {} skills ({} com delay_time que nao fecha em 1/10 s)".format(len(cli), resto_cooldown))

    print("2. Reescrevendo os atributos...")
    edits, linhas = [], []
    mudou = collections.Counter()
    transicoes = {c: collections.Counter() for c in ("activation", "skilltype")}
    sem_cliente = total = 0
    for m in TAG_RE.finditer(text):
        attrs = m.group(1)
        a = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
        sid = a.get("skill_id")
        if sid not in cli:
            sem_cliente += 1
            continue
        total += 1
        novo, diffs = attrs, []
        for campo in CAMPOS:
            valor = cli[sid].get(campo)
            if valor is None or campo not in a or a[campo] == valor:
                continue
            novo = troca(novo, campo, valor)
            mudou[campo] += 1
            diffs.append("{} {}->{}".format(campo, a[campo], valor))
            if campo in transicoes:
                transicoes[campo][(a[campo], valor)] += 1
        if diffs:
            edits.append((m.start(1), m.end(1), novo))
            linhas.append((int(sid), a.get("name", ""), diffs))
    print("   {} templates conhecidos pelo cliente ({} sem par no cliente ficam como estao) | {} mudam".format(
        total, sem_cliente, len(linhas)))
    print("   por campo: {}".format(dict(mudou)))
    for campo, t in transicoes.items():
        print("   {}: {}".format(campo, dict(t.most_common())))

    out, pos = [], 0
    for a, b, novo in edits:
        out.append(text[pos:a])
        out.append(novo)
        pos = b
    out.append(text[pos:])
    novo_texto = "".join(out)

    print("3. Validando no XSD...")
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, REL_XSD)))
    if not schema.validate(etree.fromstring(novo_texto.encode("utf-8"))):
        for e in list(schema.error_log)[:20]:
            print("   XSD linha {}: {}".format(e.line, e.message))
        sys.exit("XSD invalido: nada foi gravado.")
    print("   XSD valido.")

    if linhas:
        with open(RELATORIO, "w", encoding="utf-8") as f:
            f.write("skill_templates canonizado pelo client_skills 5.0 (duration, cooldown, delayId, activation, skilltype).\n")
            f.write("{} templates mudam. Por campo: {}\n".format(len(linhas), dict(mudou)))
            for campo, t in transicoes.items():
                f.write("{}: {}\n".format(campo, dict(t.most_common())))
            f.write("\n{:>6}  {:32}  mudancas\n".format("id", "nome"))
            for sid, nome, diffs in sorted(linhas):
                f.write("{:>6}  {:32}  {}\n".format(sid, nome[:32], "; ".join(diffs)))
        print("   relatorio: " + RELATORIO)
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


if __name__ == "__main__":
    main()
