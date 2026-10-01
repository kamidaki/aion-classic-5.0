#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_50_moros_passiva.py

Chance e restrição de raça das skills do Moreth (MOROS) no skills/skill_templates.xml, a partir do client_skills.xml.

Dois defeitos vistos em jogo em 28/09: a passiva do Moreth disparava o proc em todo ataque e contra qualquer alvo.

  1. **Chance**: o provoker das passivas Moros_Promise_G1/G2/G3 (2544, 2550, 3942) saiu sem `hittypeprob2`, e o padrão do
     EffectTemplate é 100 (todo ataque). No cliente a chance está em `effect1_reserved_cond1_prob1` (20); as outras skills
     do servidor trazem esse número do `effect1_reserved_cond1_prob2` (a G4, 4270, já está com 220). O número do cliente é
     copiado como está, como em todo provoker do servidor.
  2. **Raça do alvo**: os procs (8775, 9134, 9267) têm `target_race_restriction` no cliente (Drakan, lizardman, naga e, do
     G2 em diante, MorosMon) e nenhuma restrição no servidor. Vira o atributo `target_races` do skill_template, que o
     ProvokerEffect e o TargetRaceProperty respeitam. _Race_MorosMon não existe no Race do emulador e fica de fora (relatório).

Só mexe nas skills marcadas com `is_moros_skill` no cliente: 8 no total (3 passivas + 1 G4, 3 procs, e as ativas do
Moros_Victory quando tiverem a marca de raça).

Uso:
    python fix_50_moros_passiva.py --verificar
    python fix_50_moros_passiva.py --aplicar
A pasta do cliente (a que contem data/) vem de --cliente ou da variavel AION_CLIENT_XML_DIR.
"""

import argparse
import collections
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
PARSERS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSERS_DIR)
import backup_manager  # noqa: E402

REL_XML = os.path.join("skills", "skill_templates.xml")
DEFAULT_CLIENT_DIR = os.path.join(backup_manager.PROJECT_ROOT, "Ferramentas e Documentos", "Client e Coletas",
                                  "Client 5.0 - Dados Extraidos")
RELATORIO = os.path.join(PARSERS_DIR, "relatorio_moros_passiva_50.txt")
# _Race_* do cliente -> Race do emulador (model/Race.java)
RACAS = {"drakan": "DRAKAN", "lizardman": "LIZARDMAN", "naga": "NAGA"}


def le_cliente(pasta):
    """skills com is_moros_skill: id -> (chance do provoker, raças de alvo, nome)"""
    caminho = os.path.join(pasta, "data", "skills", "client_skills.xml")
    dados = {}
    for _, e in ET.iterparse(caminho):
        if e.tag != "skill_base_client":
            continue
        if (e.findtext("is_moros_skill") or "").strip() == "1":
            prob1 = (e.findtext("effect1_reserved_cond1_prob1") or "0").strip()
            prob2 = (e.findtext("effect1_reserved_cond1_prob2") or "0").strip()
            chance = prob1 if prob1 not in ("", "0") else prob2
            racas = [r.strip().lower().replace("_race_", "") for r in (e.findtext("target_race_restriction") or "").split(",") if r.strip()]
            dados[int(e.findtext("id"))] = (chance, racas, e.findtext("name"))
        e.clear()
    return dados


def aplica(texto, dados, rel):
    """Devolve o texto com hittypeprob2 nos provokers e target_races nos procs do Moreth."""
    def no_template(m):
        skill_id = int(m.group("id"))
        if skill_id not in dados:
            return m.group(0)
        chance, racas, nome = dados[skill_id]
        bloco = m.group(0)

        # 1. chance do provoker (só a passiva tem provoker)
        if "<provoker" in bloco and chance not in ("", "0"):
            def no_provoker(pm):
                tag = pm.group(0)
                atual = re.search(r'hittypeprob2="(\d+)"', tag)
                if atual:
                    if atual.group(1) != chance:
                        rel["chance já estava diferente (mantida)"].append(f"{skill_id} {nome}: {atual.group(1)} != {chance} do cliente")
                    return tag
                rel["chance do provoker acrescentada"].append(f"{skill_id} {nome}: hittypeprob2={chance}")
                return tag.replace(' element=', f' hittypeprob2="{chance}" element=', 1)
            bloco = re.sub(r'<provoker\b[^>]*>', no_provoker, bloco)

        # 2. raças de alvo do proc
        if racas:
            validas = [RACAS[r] for r in racas if r in RACAS]
            fora = [r for r in racas if r not in RACAS]
            if fora:
                rel["raça do cliente sem Race no emulador (fora)"].append(f"{skill_id} {nome}: {fora}")
            if validas:
                if 'target_races="' in bloco:
                    rel["target_races já estava no template (mantido)"].append(f"{skill_id} {nome}")
                else:
                    bloco = bloco.replace(' activation=', f' target_races="{" ".join(validas)}" activation=', 1)
                    rel["raças de alvo acrescentadas"].append(f"{skill_id} {nome}: {' '.join(validas)}")
        return bloco

    return re.sub(r'<skill_template skill_id="(?P<id>\d+)".*?</skill_template>', no_template, texto, flags=re.S)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cliente", default=os.environ.get("AION_CLIENT_XML_DIR", DEFAULT_CLIENT_DIR))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--verificar", action="store_true")
    g.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    print("1. Lendo o cliente...")
    dados = le_cliente(args.cliente)
    print(f"   skills com is_moros_skill: {len(dados)}")

    caminho = os.path.join(backup_manager.SERVER_DATA_DIR, REL_XML)
    texto = open(caminho, encoding="utf-8").read()
    rel = collections.defaultdict(list)
    novo = aplica(texto, dados, rel)
    mudou = sum(len(v) for k, v in rel.items() if "acrescentad" in k)
    print(f"   templates alterados: {mudou}")

    print("2. Validando contra o static_data.xsd agregado...")
    from lxml import etree
    schema = etree.XMLSchema(etree.parse(os.path.join(backup_manager.SERVER_DATA_DIR, "static_data.xsd")))
    doc = etree.fromstring(novo.encode("utf-8"))
    if not schema.validate(doc):
        for e in list(schema.error_log)[:20]:
            print(f"   linha {e.line}: {e.message}")
        sys.exit("   XSD INVALIDO")
    print("   valido")

    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("fix_50_moros_passiva.py\n")
        for k, v in rel.items():
            f.write(f"\n== {k}: {len(v)}\n")
            f.writelines(f"  {x}\n" for x in v)
    print(f"   relatorio: {RELATORIO}")

    if not args.aplicar:
        print("\nModo --verificar: nada foi gravado.")
        return
    print("3. Gravando...")
    backup_manager.backup_file_before_modification(REL_XML)
    for base in (backup_manager.SERVER_DATA_DIR, backup_manager.PRODUTO_FINAL_DATA_DIR):
        destino = os.path.join(base, REL_XML)
        with open(destino, "w", encoding="utf-8", newline="\n") as f:
            f.write(novo)
        print(f"   Gravado: {destino}")


if __name__ == "__main__":
    main()
