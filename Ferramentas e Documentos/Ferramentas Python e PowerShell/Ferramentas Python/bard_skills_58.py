"""Skills do Bard (Live 5.8) no cliente 5.0 e nos dados extraidos do repositorio.

O Bard aprende as skills do Live: Artist (classe base no 5.8) nos niveis 1-8 e Bard a partir do
10, cada variante _G1, _G2... com nivel fixo. No 5.0 a classe ja nasce Bard (id 20): tudo vira
`class BARD` no `client_skill_learns`, com o nivel do 5.8.

- Definicao: `bard_skills.xml` (skill_base_client do 5.8, ja separado em Classes_Live_5.8). O 5.0
  le os mesmos campos, menos ~50 que so o 5.8 tem (required_harp, cast_fxc, toggle_id...): esses
  ficam de fora e sao listados.
- Ids: 5.188 dos 5.457 ids do Bard no 5.8 ja sao de outras skills no 5.0. Id novo = 22000 + posicao
  do id do 5.8 entre os do Bard (faixa livre no cliente e no servidor, abaixo de 32768).
- Textos: em ingles, do l10n/eng do Riftshade, nas quatro linguas (ainda sem traducao).
- Icones: `skills.pak` do 5.8 (o nome e a versao _gray).

Uso:
    python bard_skills_58.py --lista     o que o lote converte, sem gravar
    python bard_skills_58.py             grava o cliente de teste e os XMLs extraidos do repo
    python bard_skills_58.py --servidor  templates minimos e arvore do BARD no servidor (as duas copias);
                                         depois o rebuild_50_skill_effects.py --aplicar da o corpo
"""
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from functools import lru_cache

import aion_bxml
import aion_pak
import teste_harpa_58 as T

BARD_SKILLS_58 = r"G:\Projetos AION\Classic\Classes_Live_5.8\2_Bard_Songweaver\Skills_and_Items\bard_skills.xml"
PAK_SKILLS_58 = r"Data\skills\skills.pak"
STRINGS_ENG = (r"G:\Aion Riftshade\l10n\eng\data\data.pak", "strings/client_strings_skill.xml")
REPO_DADOS = os.path.join(T.REPO, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos",
                          "data", "skills")
#: As tres copias dos XMLs de skill do 5.0 (o cliente le uma conforme o modo).
PAKS_DE_SKILL = (r"data\skills\skills.pak", r"data\skills\special\special.pak",
                 r"data\skills\special2\special2.pak")
PASTAS_DO_REPO = ("", "special", "special2")

#: Primeiro lote: as skills do Artist (niveis 1-8 no 5.8) e as passivas de arma/armadura do Bard.
#: Ar_SongofBattle_1_G1 fica de fora: e "Charge" e o 5.0 nao tem o client_skill_charge.
LOTE = ("P_EQUIP_EnhancedHarp_G1", "P_EQUIP_Harp_G1", "Ar_SongofAir_G1", "Ar_SongofAir_G2",
        "Ar_SongofCold_G1", "Ar_SongofCold_G2", "Ar_SongofHeal_G1")
#: Skills do Bard no 5.8 que o 5.0 ja tem com o mesmo nome: so entram no aprendizado.
JA_NO_50 = ("P_EQUIP_EnhancedCloth_G1", "P_EQUIP_EnhancedRobe_G1", "P_EQUIP_Robe_G1")
ID_BASE = 22000
ID_BASE_APRENDIZADO = 90000
ID_BASE_STRING = 1991000
CLASSE = "BARD"


def _skills_58():
    texto = open(BARD_SKILLS_58, encoding="utf-8").read()
    skills = {}
    for bloco in re.findall(r"<skill_base_client>(.*?)</skill_base_client>", texto, re.S):
        campos = re.findall(r"<([A-Za-z0-9_]+)>([^<]*)</\1>", bloco)
        d = dict(campos)
        skills[d["name"]] = (int(d["id"]), campos)
    return skills


def ids_novos(skills):
    """Id do 5.0 de cada skill do Bard: 22000 + posicao do id do 5.8 (estavel entre execucoes)."""
    ordem = sorted({i for i, _c in skills.values()})
    posicao = {i: k for k, i in enumerate(ordem)}
    return {nome: ID_BASE + posicao[i] for nome, (i, _c) in skills.items()}


def _campos_50():
    texto = open(os.path.join(REPO_DADOS, "client_skills.xml"), encoding="utf-8").read()
    return set(re.findall(r"<([a-z0-9_]+)>[^<]*</\1>", texto))


def _aprendizado_58():
    d, idx = aion_pak.abre(os.path.join(T.LIVE_CLIENTE, PAK_SKILLS_58))
    texto = aion_bxml.decodifica(aion_pak.le(d, next(e for e in idx if e.nome.lower() == "client_skill_learns.xml")))
    niveis = {}
    for bloco in re.findall(r"<client_skill_learn>(.*?)</client_skill_learn>", texto, re.S):
        d = dict(re.findall(r"<([a-z_]+)>([^<]*)</\1>", bloco))
        if d.get("class", "").upper() in ("ARTIST", "BARD"):
            niveis.setdefault(d["skill"], int(d["pc_level"]))
    return niveis


def converte(skills, ids, campos50):
    """{nome: (id novo, [(tag, texto)])} do lote no formato do 5.0, e os campos que ficaram de fora."""
    saida, fora = {}, {}
    for nome in LOTE:
        _id58, campos = skills[nome]
        novos = []
        for tag, valor in campos:
            if tag == "id":
                valor = str(ids[nome])
            if tag not in campos50:
                fora.setdefault(tag, []).append(nome)
                continue
            novos.append((tag, valor))
        saida[nome] = (ids[nome], novos)
    return saida, fora


def aprendizado(niveis, inicio=ID_BASE_APRENDIZADO):
    """[(id, nome da skill, nivel)] do BARD, na ordem de nivel."""
    linhas = sorted((niveis[n], n) for n in LOTE + JA_NO_50)
    return [(inicio + k, nome, nivel) for k, (nivel, nome) in enumerate(linhas)]


def _strings_eng():
    d, idx = aion_pak.abre(STRINGS_ENG[0])
    t = aion_bxml.decodifica(aion_pak.le(d, next(e for e in idx if e.nome.lower() == STRINGS_ENG[1])))
    return {m.group(1).lower(): m.group(2) for m in
            re.finditer(r"<name>([^<]+)</name>\s*<body>(.*?)</body>", t, re.S)}


def strings(convertidas):
    """[(arquivo, id, nome, {lingua: texto})] dos textos que o lote cita (STR_*), em ingles."""
    eng = _strings_eng()
    nomes = []
    for _id, campos in convertidas.values():
        for _tag, valor in campos:
            if valor.upper().startswith("STR_") and valor not in nomes:
                nomes.append(valor)
    saida = []
    for k, nome in enumerate(nomes):
        texto = eng.get(nome.lower())
        if texto is None:
            raise ValueError(f"sem texto em ingles: {nome}")
        saida.append(("strings/client_strings_skill.xml", ID_BASE_STRING + k, nome,
                      {lingua: texto for lingua in ("ENG", "DEU", "FRA", "BRA")}))
    return saida


@lru_cache(maxsize=None)
def STRINGS_DAS_SKILLS():
    skills = _skills_58()
    convertidas, _fora = converte(skills, ids_novos(skills), _campos_50())
    return tuple(strings(convertidas))


def icones(convertidas):
    nomes = []
    for _id, campos in convertidas.values():
        icone = dict(campos).get("skillicon_name")
        if icone:
            base = icone[:-4] if icone.lower().endswith(".dds") else icone
            for n in (base + ".dds", base + "_gray.dds"):
                if n.lower() not in {x.lower() for x in nomes}:
                    nomes.append(n)
    achados = T.do_58(r"Data\skills", nomes)
    faltam = {n.lower() for n in nomes} - {n.lower() for n in achados}
    if faltam:
        raise ValueError(f"icones sem arquivo no 5.8: {sorted(faltam)}")
    return achados


def _el_skill(campos):
    el = ET.Element("skill_base_client")
    for tag, valor in campos:
        ET.SubElement(el, tag).text = valor
    return el


def _el_aprendizado(id_linha, skill, nivel):
    el = ET.Element("client_skill_learn")
    for tag, valor in (("id", str(id_linha)), ("name", str(id_linha)), ("race", "All"), ("class", CLASSE),
                       ("pc_level", str(nivel)), ("skill", skill), ("skill_level", "1"), ("learntype", "0"),
                       ("autolearn", "TRUE"), ("ui_display", "1"), ("stigma_display", "0")):
        ET.SubElement(el, tag).text = valor
    return el


def _texto_xml(el, recuo="  "):
    linhas = [f"{recuo}<{el.tag}>"]
    for f in el:
        linhas.append(f"{recuo}  <{f.tag}>{f.text}</{f.tag}>")
    linhas.append(f"{recuo}</{el.tag}>")
    return "\n".join(linhas) + "\n"


def _tira_do_texto(xml, marca, ids):
    """Tira do XML de texto os elementos <marca> com esses ids (reaplicar nao duplica)."""
    padrao = re.compile(r"  <%s>\s*<id>(\d+)</id>.*?</%s>\n" % (marca, marca), re.S)
    return padrao.sub(lambda m: "" if int(m.group(1)) in ids else m.group(0), xml)


def aplica_repo(convertidas, linhas):
    ids_skill = {i for i, _c in convertidas.values()}
    ids_linha = {i for i, _n, _l in linhas}
    for pasta in PASTAS_DO_REPO:
        for arquivo, marca, raiz, elementos, ids in (
                ("client_skills.xml", "skill_base_client", "skill_base_clients",
                 [_el_skill(c) for _i, c in convertidas.values()], ids_skill),
                ("client_skill_learns.xml", "client_skill_learn", "client_skill_learns",
                 [_el_aprendizado(*l) for l in linhas], ids_linha)):
            caminho = os.path.join(REPO_DADOS, pasta, arquivo)
            if not os.path.exists(caminho):
                continue
            with open(caminho, encoding="utf-8", newline="") as f:
                xml = f.read()
            nl = "\r\n" if "\r\n" in xml else "\n"
            xml = _tira_do_texto(xml.replace("\r\n", "\n"), marca, ids)
            fim = xml.rindex(f"</{raiz}>")
            xml = xml[:fim] + "".join(_texto_xml(e) for e in elementos) + xml[fim:]
            with open(caminho, "w", encoding="utf-8", newline="") as f:
                f.write(xml.replace("\n", nl))
            print(f"OK  repo {os.path.join(pasta, arquivo)}: +{len(elementos)}")


def aplica_cliente(convertidas, linhas, arquivos_de_icone):
    for rel in PAKS_DE_SKILL:
        caminho = os.path.join(T.CLIENTE, rel)
        origem = caminho + T.SUFIXO_BACKUP if os.path.exists(caminho + T.SUFIXO_BACKUP) else caminho
        d, idx = aion_pak.abre(origem)
        por_nome = {e.nome.lower(): e for e in idx}
        troca = {}
        for arquivo, elementos in (("client_skills.xml", [_el_skill(c) for _i, c in convertidas.values()]),
                                   ("client_skill_learns.xml", [_el_aprendizado(*l) for l in linhas])):
            entrada = por_nome[arquivo]
            bxml = aion_pak.le(d, entrada)
            texto = aion_bxml.decodifica(bxml)
            for e in elementos:
                if f"<id>{e.find('id').text}</id>" in texto and arquivo == "client_skills.xml":
                    raise ValueError(f"{rel}: o id {e.find('id').text} ja existe")
            troca[entrada.nome], _ = T.acrescenta_filhos(bxml, elementos)
        icones_novos = {}
        if any(e.nome.lower().endswith(".dds") for e in idx):
            icones_novos = {n: b for n, b in arquivos_de_icone.items() if n.lower() not in por_nome}
        T._backup(caminho)
        if origem != caminho:
            shutil.copy2(origem, caminho)
        T.regrava_pak(caminho, troca=troca, acrescenta=icones_novos)
        T._confere_pak(caminho, len(idx), {**{n: "troca" for n in troca}, **{n: "novo" for n in icones_novos}})
        d2, idx2 = aion_pak.abre(caminho)
        lido = {e.nome.lower(): e for e in idx2}
        skills_xml = aion_bxml.decodifica(aion_pak.le(d2, lido["client_skills.xml"]))
        for nome, (id_novo, _c) in convertidas.items():
            assert f"<id>{id_novo}</id>" in skills_xml and f"<name>{nome}</name>" in skills_xml, (rel, nome)
        print(f"OK  {rel}: +{len(convertidas)} skills, +{len(linhas)} aprendizados, +{len(icones_novos)} icones")


#: Servidor: o `skill_templates.xml` atual e bilingue (name_en/name_pt) e o `parse_skills.py`
#: ainda grava o formato antigo (name) em todas as skills -- nao serve. As skills do Bard entram como
#: template minimo (so <properties>), e o `rebuild_50_skill_effects.py` da o corpo a partir do
#: client_skills (custo, efeitos, corrente, motion), como fez com os outros templates vazios.
SERVIDOR = (os.path.join(T.REPO, "Código Fonte - Emulador", "game-server", "data", "static_data"),
            os.path.join(T.REPO, "Emulador - Produto Final", "GameServer", "data", "static_data"))
TEMPLATES_REL = os.path.join("skills", "skill_templates.xml")
ARVORE_REL = os.path.join("skill_tree", "skill_tree.xml")
_INICIO_RE = re.compile(r'^\t<skill_template skill_id="(\d+)"', re.M)


def _templates(texto):
    """[(skill_id, inicio, fim)] de cada <skill_template>, pelo inicio da linha (busca linear)."""
    saida = []
    for m in _INICIO_RE.finditer(texto):
        fim_tag = texto.index(">", m.end())
        if texto[fim_tag - 1] == "/":
            fim = fim_tag + 1
        else:
            fim = texto.index("</skill_template>", fim_tag) + len("</skill_template>")
        if texto.startswith("\n", fim):
            fim += 1
        saida.append((int(m.group(1)), m.start(), fim))
    return saida


def _xml_attr(v):
    return str(v).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def _ids_50():
    texto = open(os.path.join(REPO_DADOS, "client_skills.xml"), encoding="utf-8").read()
    return {m.group(2): int(m.group(1)) for m in re.finditer(r"<skill_base_client>\s*<id>(\d+)</id>\s*<name>([^<]+)</name>", texto)}


#: Passiva de arma (Wpn_Mastery): a traducao das de orbe e livro do 5.0 (P_EQUIP_Orb_G1 = 75,
#: P_EQUIP_EnhancedBook_G1 = 64) -- reserved5 -> weapon (ItemGroup), effectid e basiclv diretos,
#: reserved2 -> MAGICAL_ATTACK PERCENT, first_target ME, playermove false. O gerador nao tem exemplo
#: de harpa para aprender 2h_Harp -> HARP; o stat e o das armas magicas (a harpa ataca com
#: magical_water, ATAQUE_CLIENTE do teste_harpa_58).
ARMA_DO_CLIENTE = {"2h_harp": "HARP"}


def _corpo_wpn_mastery(d):
    arma = ARMA_DO_CLIENTE[d["effect1_reserved5"].lower()]
    return ("\t\t<properties first_target=\"ME\" />\n\t\t<useconditions>\n\t\t\t<playermove allow=\"false\" />\n"
            "\t\t</useconditions>\n\t\t<effects>\n"
            f"\t\t\t<wpnmastery weapon=\"{arma}\" effectid=\"{d['effect1_effectid']}\" e=\"1\" "
            f"basiclvl=\"{d['effect1_basiclv']}\">\n"
            f"\t\t\t\t<change stat=\"MAGICAL_ATTACK\" func=\"PERCENT\" value=\"{d['effect1_reserved2']}\" />\n"
            "\t\t\t</wpnmastery>\n\t\t</effects>\n")


def _template_minimo(id_novo, campos, textos_por_nome):
    d = dict(campos)
    nome = textos_por_nome[d["desc"]]
    attrs = [("skill_id", id_novo), ("name_en", nome[1]), ("name_pt", nome[1]), ("nameId", nome[0]),
             ("delayId", d.get("delay_id") or id_novo), ("stack", d["name"].upper()), ("lvl", 1),
             ("skilltype", (d.get("type") or "PHYSICAL").upper()), ("skillsubtype", "NONE"), ("tslot", "NOSHOW"),
             ("activation", (d.get("activation_attribute") or "ACTIVE").upper()),
             ("cooldown", int(float(d.get("delay_time") or 0)) // 100),
             ("duration", int(float(d.get("casting_delay") or 0)))]
    corpo = (_corpo_wpn_mastery(d) if d.get("effect1_type") == "Wpn_Mastery"
             else "\t\t<properties first_target=\"TARGET\" />\n")
    return "\t<skill_template " + " ".join(f'{k}="{_xml_attr(v)}"' for k, v in attrs) + ">\n" + corpo + "\t</skill_template>\n"


def aplica_servidor(convertidas, linhas, textos):
    textos_por_nome = {nome: (id_string, t["ENG"]) for _a, id_string, nome, t in textos}
    novos = {i: _template_minimo(i, c, textos_por_nome) for i, c in convertidas.values()}
    ids_50 = _ids_50()
    ids = {nome: i for nome, (i, _c) in convertidas.items()}
    ids.update({nome: ids_50[nome] for nome in JA_NO_50})
    arvore = "".join(f'\t<skill name="{nome.lower()}" skillId="{ids[nome]}" skillLevel="1" minLevel="{nivel}" '
                     f'race="PC_ALL" classId="{CLASSE}" autoLearn="true" />\n' for _l, nome, nivel in linhas)
    for base in SERVIDOR:
        caminho = os.path.join(base, TEMPLATES_REL)
        with open(caminho, encoding="utf-8", newline="") as f:
            texto = f.read()
        partes, pos = [], 0
        for sid, ini, fim in _templates(texto):  # tira os do Bard de uma execucao anterior
            if sid in novos:
                partes.append(texto[pos:ini])
                pos = fim
        texto = "".join(partes) + texto[pos:]
        # Na ordem de skill_id: cada um antes do primeiro template de id maior.
        lista = _templates(texto)
        insercoes = []
        for id_novo in sorted(novos):
            depois = next((ini for sid, ini, _f in lista if sid > id_novo), texto.rindex("</skill_data>"))
            insercoes.append((depois, novos[id_novo]))
        por_pos = {}
        for pos_ins, bloco in insercoes:  # ja em ordem de skill_id
            por_pos.setdefault(pos_ins, []).append(bloco)
        for pos_ins in sorted(por_pos, reverse=True):
            texto = texto[:pos_ins] + "".join(por_pos[pos_ins]) + texto[pos_ins:]
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(texto)
        caminho = os.path.join(base, ARVORE_REL)
        with open(caminho, encoding="utf-8", newline="") as f:
            texto = f.read()
        texto = re.sub(r'\t<skill [^>]*classId="%s"[^>]*/>\n' % CLASSE, "", texto)
        fim = texto.rindex("</skill_tree>")
        texto = texto[:fim] + arvore + texto[fim:]
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(texto)
        print(f"OK  {base}: +{len(novos)} templates minimos, +{len(linhas)} linhas {CLASSE} na arvore")


def main():
    skills = _skills_58()
    ids = ids_novos(skills)
    convertidas, fora = converte(skills, ids, _campos_50())
    niveis = _aprendizado_58()
    linhas = aprendizado(niveis)
    textos = strings(convertidas)
    print("Lote:")
    for nome, (id_novo, campos) in convertidas.items():
        d = dict(campos)
        print(f"  {nome}: 5.8 {skills[nome][0]} -> {id_novo}, nivel {niveis[nome]}, "
              f"{d.get('activation_attribute')}, {d.get('effect1_type')}, motion {d.get('motion_name', '-')}")
    for nome in JA_NO_50:
        print(f"  {nome}: ja no 5.0, nivel {niveis[nome]}")
    print("Campos do 5.8 que o 5.0 nao tem (ficam de fora):")
    for tag, nomes in sorted(fora.items()):
        print(f"  {tag}: {len(nomes)}")
    print(f"Textos: {len(textos)} ({', '.join(t[2] for t in textos)})")
    if "--lista" in sys.argv:
        return
    if "--servidor" in sys.argv:
        aplica_servidor(convertidas, linhas, textos)
        print("Proximo: rebuild_50_skill_effects.py --aplicar (corpo dos templates minimos).")
        return
    arquivos_de_icone = icones(convertidas)
    aplica_cliente(convertidas, linhas, arquivos_de_icone)
    aplica_repo(convertidas, linhas)
    print("Os textos vao pelo `teste_harpa_58.py --strings` (mesmo pak das outras strings).")


if __name__ == "__main__":
    main()
