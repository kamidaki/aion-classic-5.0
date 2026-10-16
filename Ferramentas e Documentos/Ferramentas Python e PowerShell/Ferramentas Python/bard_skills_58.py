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
#: Segundo lote: as do Bard dos niveis 10-15 (sem as Charge). Ar_SongofRest_G1 fica para o lote
#: do Ba_Lullaby: o Deform das duas transforma o alvo num NPC do 5.8 que o 5.0 nao tem
#: (Ar_SongofRest_G1_NPC 201081, Monster/PolyDancer). Sempre acrescentar no fim: a ordem da os ids
#: das strings.
LOTE = ("P_EQUIP_EnhancedHarp_G1", "P_EQUIP_Harp_G1", "Ar_SongofAir_G1", "Ar_SongofAir_G2",
        "Ar_SongofCold_G1", "Ar_SongofCold_G2", "Ar_SongofHeal_G1",
        # lote 2
        "Ar_SongofFire_G1", "Ar_SongofHeal_G2", "Ar_SongofRelax_G1", "Ar_SongofRoot_G1",
        "Ar_Songofshield_G1", "BA_SeraphicSong_G1", "Ba_SongofAnger_G1", "Ba_SongofDelayDamage_G1",
        "Ar_SongofAir_G3", "Ar_SongofCold_G3", "Ar_SongofFire_G2",
        "Ar_SongofHeal_G3", "Ar_SongofRelax_G2", "Ar_Songofshield_G2", "Ba_SongofAnger_G2",
        "Ba_SongofDelayDamage_G2", "Ba_SongofDimensionDoor_G1", "Ba_SongofLand_G1",
        # lote 3: niveis 16-20, sem as Charge e sem o Ba_Lullaby_G1 (NPC, ver Ar_SongofRest_G1)
        "Ar_SongofAir_G4", "Ba_SongofEmergentHeal_G1", "Ar_SongofCold_G4", "Ba_SongofPurify_G1",
        "Ar_SongofFire_G3", "Ar_SongofHeal_G4", "Ar_SongofRelax_G3", "Ar_Songofshield_G3",
        "Ba_MagicalDestruction_G1", "Ba_SongofAdvance_G1", "Ba_SongofAnger_G3", "Ba_SongofDelayDamage_G3",
        "Ba_SongofEarth_G1", "Ba_SongofFirm_G1", "Ba_SongofLand_G2", "Ba_SongofManaReverse_G1",
        "Ba_SongofRegeneration_G1", "Ba_SongofSerenity_1_G1", "Ba_songofBrave_G1",
        # lote 4: niveis 21-30, sem as Charge
        "Ar_SongofAir_G5", "Ba_SongofEmergentHeal_G2", "Ba_SongofStamina_G1", "Ar_SongofCold_G5",
        "Ba_SongofShock_G1", "Ar_SongofFire_G4", "Ar_SongofHeal_G5", "Ar_SongofRelax_G4",
        "Ar_Songofshield_G4", "BA_BardsGift_G1", "Ba_SongofAnger_G4", "Ba_SongofDelayDamage_G4",
        "Ba_SongofEagle_G1", "Ba_SongofLand_G3", "P_EQUIP_Harp_G2", "Ar_SongofAir_G6",
        "Ba_MagicalDestruction_G2", "Ba_SongofEarth_G2", "Ba_SongofFirm_G2", "Ba_SongofManaReverse_G2",
        "Ba_SongofRegeneration_G2", "Ba_SongofSerenity_1_G2", "Ba_songofBrave_G2",
        "Ba_SongofEmergentHeal_G3", "Ba_SongofStamina_G2", "Ar_SongofCold_G6", "Ba_SongofResurrection_G1",
        "Ba_SongofShock_G2", "Ar_SongofFire_G5", "Ar_SongofHeal_G6", "Ar_SongofRelax_G5",
        "Ar_Songofshield_G5", "Ba_SongofAnger_G5", "Ba_SongofDelayDamage_G5", "Ba_SongofEagle_G2",
        "Ba_SongofLand_G4", "Ba_SongofMinddamage_G1",
        # lote 5: niveis 31-40, sem as Charge
        "Ar_SongofAir_G7", "Ba_SongofDestroy_G1", "Ba_MagicalDestruction_G3", "Ba_SongofEarth_G3",
        "Ba_SongofEmergentHeal_G4", "Ba_SongofFirm_G3", "Ba_SongofRegeneration_G3", "Ba_SongofSerenity_1_G3",
        "Ba_SongofStamina_G3", "Ba_songofBrave_G3", "Ar_SongofCold_G7", "Ba_SongofShock_G3",
        "Ar_SongofFire_G6", "Ar_SongofHeal_G7", "Ar_SongofRelax_G6", "Ar_Songofshield_G6",
        "Ba_SongofAnger_G6", "Ba_SongofDelayDamage_G6", "Ba_SongofEagle_G3", "Ba_SongofLand_G5",
        "Ba_SongofMinddamage_G2", "Ba_SongofWind_G1", "Ar_SongofAir_G8", "Ba_SongofEmergentHeal_G5",
        "Ba_SongofStamina_G4", "Ar_SongofCold_G8", "Ba_MagicalDestruction_G4", "Ba_SongofEarth_G4",
        "Ba_SongofFirm_G4", "Ba_SongofRegeneration_G4", "Ba_SongofSerenity_1_G4", "Ba_SongogPeace_G1",
        "Ba_songofBrave_G4", "Ba_SongofShock_G4", "Ar_SongofFire_G7", "Ar_SongofHeal_G8",
        "Ar_SongofRelax_G7", "Ar_Songofshield_G7", "Ba_SongofAnger_G7", "Ba_SongofBind_G1",
        "Ba_SongofDelayDamage_G7", "Ba_SongofEagle_G4", "Ba_SongofHope_G1", "Ba_SongofLand_G6",
        "Ba_SongofMinddamage_G3", "Ba_SongofWind_G2", "P_EQUIP_Harp_G3",
        # lote 6: niveis 41-50, sem as Charge
        "Ar_SongofAir_G9", "Ba_SongofEmergentHeal_G6", "Ba_SongofRefreshMind_G1", "Ba_SongofStamina_G5",
        "Ar_SongofCold_G9", "Ba_SongogPeace_G2", "Ba_MagicalDestruction_G5", "Ba_SongofEarth_G5",
        "Ba_SongofFirm_G5", "Ba_SongofRegeneration_G5", "Ba_SongofSerenity_1_G5", "Ba_SongofShock_G5",
        "Ba_songofBrave_G5", "Ar_SongofFire_G8", "Ar_SongofHeal_G9", "Ar_SongofRelax_G8",
        "Ar_Songofshield_G8", "Ba_DelayParalyze_G1", "Ba_PlayingStylesChangeA_G1", "Ba_PlayingStylesChangeB_G1",
        "Ba_SongofAnger_G8", "Ba_SongofDelayDamage_G8", "Ba_SongofEagle_G5", "Ba_SongofLand_G7",
        "Ba_SongofMinddamage_G4", "Ba_SongofPain_G1", "Ba_SongofWarmth_G1", "Ba_SongofWind_G3",
        "Ar_SongofAir_G10", "Ba_SongofMentalic_G1", "Ba_SongofAppreciation_G1", "Ba_SongofEmergentHeal_G7",
        "Ba_SongofRefreshMind_G2", "Ba_SongofStamina_G6", "Ar_SongofCold_G10", "Ba_SongofGreatHeal_G1",
        "Ba_SongofSoulextinction_G1", "Ba_SongogPeace_G3", "Ba_SongofPain_G2", "Ba_SongofResistance_G1",
        "Ba_SongofShock_G6", "Ba_SongofWarmth_G2", "Ar_SongofFire_G9", "Ar_SongofHeal_G10",
        "Ar_SongofRelax_G9", "Ar_Songofshield_G9", "Ba_MagicalDestruction_G6", "Ba_SongofAnger_G9",
        "Ba_SongofDelayDamage_G9", "Ba_SongofEagle_G6", "Ba_SongofEarth_G6", "Ba_SongofFirm_G6",
        "Ba_SongofLand_G8", "Ba_SongofMinddamage_G5", "Ba_SongofRegeneration_G6", "Ba_SongofSerenity_1_G6",
        "Ba_SongofWind_G4", "Ba_songofBrave_G6", "P_EQUIP_Harp_G4",
        # lote 7: niveis 51-60, sem as Charge
        "Ar_SongofAir_G11", "Ba_SongofMentalic_G2", "Ba_SongofWeight_G1", "Ba_SongofAppreciation_G2",
        "Ba_SongofEmergentHeal_G8", "Ba_SongofInjury_G1", "Ba_SongofRefreshMind_G3", "Ar_SongofCold_G11",
        "Ba_SongofGreatHeal_G2", "Ba_SongofPain_G3", "Ba_SongofSoulextinction_G2", "Ba_SongofWarmth_G3",
        "Ba_SongogPeace_G4", "Ba_SongofResistance_G2", "Ba_SongofShock_G7", "Ba_SongofTidalwave_G1",
        "Ar_SongofFire_G10", "Ar_SongofHeal_G11", "Ar_SongofRelax_G10", "Ar_Songofshield_G10",
        "Ba_MassDispel_G1", "Ba_SongofAnger_G10", "Ba_SongofBless_G1", "Ba_SongofDelayDamage_G10",
        "Ba_SongofEagle_G7", "Ba_SongofGale_G1", "Ba_SongofIllusion_G1", "Ba_SongofLand_G9",
        "Ba_SongofMinddamage_G6", "Ba_SongofWind_G5", "Ar_SongofAir_G12", "Ba_MagicalDestruction_G7",
        "Ba_SongofEarth_G7", "Ba_SongofGust_G1", "Ba_SongofMentalic_G3", "Ba_SongofRegeneration_G7",
        "Ba_SongofSerenity_1_G7", "Ba_SongofWeight_G2", "BA_FocusDefence_G1", "Ba_SongofAppreciation_G3",
        "Ba_SongofEmergentHeal_G9", "Ba_SongofInjury_G2", "Ba_SongofPain_G4", "Ba_SongofRefreshMind_G4",
        "Ba_SongofWarmth_G4", "Ar_SongofCold_G12", "Ba_SongofGreatHeal_G3", "Ba_SongofSoulextinction_G3",
        "Ba_SongogPeace_G5", "Ba_SongofBless_G2", "Ba_SongofGale_G2", "Ba_SongofIllusion_G2",
        "Ba_SongofResistance_G3", "Ba_SongofShock_G8", "Ba_SongofTidalwave_G2", "Ar_SongofFire_G11",
        "Ar_SongofHeal_G12", "Ar_SongofRelax_G11", "Ar_Songofshield_G11", "Ba_SongofAnger_G11",
        "Ba_SongofDelayDamage_G11", "Ba_SongofEagle_G8", "Ba_SongofLand_G10", "Ba_SongofMinddamage_G7",
        "Ba_SongofWind_G6",
        # lote 8: niveis 61-65, sem as Charge e sem as EV_ do nivel 66 (sem autolearn nem estigma
        # no 5.8: vem de outro sistema)
        "Ar_SongofAir_G13", "Ba_SongofGust_G2", "Ba_SongofMentalic_G4", "Ba_SongofPain_G5",
        "Ba_SongofWarmth_G5", "Ba_SongofWeight_G3", "BA_FocusDefence_G2", "Ba_MagicalDestruction_G8",
        "Ba_SongofAppreciation_G4", "Ba_SongofEarth_G8", "Ba_SongofEmergentHeal_G10", "Ba_SongofInjury_G3",
        "Ba_SongofRefreshMind_G5", "Ba_SongofRegeneration_G8", "Ba_SongofSerenity_1_G8", "Ar_SongofCold_G13",
        "Ba_SongofBless_G3", "Ba_SongofGale_G3", "Ba_SongofGreatHeal_G4", "Ba_SongofIllusion_G3",
        "Ba_SongofSoulextinction_G4", "Ba_SongogPeace_G6", "BA_ExcitingMelody_G1", "Ba_SongofResistance_G4",
        "Ba_SongofShock_G9", "Ba_SongofTidalwave_G3", "Ar_SongofFire_G12", "Ar_SongofHeal_G13",
        "Ar_SongofRelax_G12", "Ar_Songofshield_G12", "Ba_Sanctuary_G1", "Ba_SongofAnger_G12",
        "Ba_SongofDelayDamage_G12", "Ba_SongofEagle_G9", "Ba_SongofLand_G11", "Ba_SongofMinddamage_G8",
        "Ba_SongofPain_G6", "Ba_SongofWarmth_G6", "Ba_SongofWind_G7",
        # Requiem e Freestyle: o Deform transforma o alvo nos NPCs de NPCS_DE_DEFORM (--npcs)
        "Ar_SongofRest_G1", "Ba_Lullaby_G1")


def _dependencias():
    """Skills que as do lote disparam pelo nome (DelayedSkill...): entram junto, sem aprendizado."""
    texto = open(BARD_SKILLS_58, encoding="utf-8").read()
    nomes = set(re.findall(r"<name>([^<]+)</name>", texto))
    # As que o 5.0 ja tem (CL_ResurrectDebuff do Ba_SongofResurrection) ficam com o id do 5.0; as
    # do Bard ja trazidas (ids a partir de ID_BASE) continuam dependencia.
    cliente50 = open(os.path.join(REPO_DADOS, "client_skills.xml"), encoding="utf-8").read()
    nomes -= {n for i, n in re.findall(r"<skill_base_client>\s*<id>(\d+)</id>\s*<name>([^<]+)</name>", cliente50)
              if int(i) < ID_BASE}
    saida = []
    for bloco in re.findall(r"<skill_base_client>(.*?)</skill_base_client>", texto, re.S):
        d = dict(re.findall(r"<([A-Za-z0-9_]+)>([^<]*)</\1>", bloco))
        if d.get("name") in LOTE:
            for tag, valor in d.items():
                if tag.startswith("effect") and valor in nomes and valor not in LOTE and valor not in saida:
                    saida.append(valor)
    return tuple(sorted(saida))


#: Skills do Bard no 5.8 que o 5.0 ja tem com o mesmo nome: so entram no aprendizado.
JA_NO_50 = ("P_EQUIP_EnhancedCloth_G1", "P_EQUIP_EnhancedRobe_G1", "P_EQUIP_Robe_G1",
            "P_HealMastery_G1", "P_StatBoostMagiclOffense_G1", "Aromatherapy_G1", "Mending_G2",
            "Aromatherapy_G2", "Mending_G3",
            "P_StatBoostMaxMP_G1", "P_StatBoostElementalDefendAll_G1", "Aromatherapy_G3", "Mending_G4",
            "Aromatherapy_G4", "Mending_G5", "P_BoostHateDown_G1", "P_HealMastery_G2", "Aromatherapy_G5",
            "Mending_G6", "P_StatBoostMCReduceRate_G1", "ALL_ShockReflect_G1", "P_HealMastery_G3",
            "P_StatBoostMagiclOffense_G2", "P_BoostHateDown_G2", "P_StatBoostMaxMP_G2", "P_HealMastery_G4",
            "P_StatBoostMagiclOffense_G3", "P_StatBoostMCReduceRate_G2", "P_StatBoostMaxMP_G3")
#: No aprendizado do Bard no 5.8, mas sem definicao no bard_skills.xml nem skill no 5.0 (skills comuns
#: do 5.8 alem das do 5.0): ficam de fora por enquanto.
SEM_FONTE = ("Aromatherapy_G6", "Aromatherapy_G7", "Mending_G7", "Mending_G8", "Aromatherapy_G8", "Mending_G9",
             "Aromatherapy_G9", "Mending_G10",
             "Aromatherapy_G10", "Mending_G11", "Aromatherapy_G11", "Mending_G12", "Aromatherapy_G12", "Mending_G13")
ID_BASE = 22000
ID_BASE_APRENDIZADO = 90000
ID_BASE_STRING = 1991000
CLASSE = "BARD"
DEPENDENCIAS = _dependencias()


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
    for nome in LOTE + DEPENDENCIAS:
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
    saida, sem_texto = [], []
    for nome in nomes:
        texto = eng.get(nome.lower())
        if texto is not None:
            # Quebra de linha como no 5.0 (1.501 textos de skill com \n, nenhum com \r\n); o 5.8 traz \r\n.
            texto = texto.replace("\r\n", "\n")
        if texto is None:
            # Citado e sem texto no proprio 5.8 (355 skills do Live tem desc_abnormal assim, ex.:
            # STR_Ba_SongofDelayDamage_sys_Abnormal): o campo fica como no 5.8, sem string.
            sem_texto.append(nome)
            continue
        saida.append(("strings/client_strings_skill.xml", ID_BASE_STRING + len(saida), nome,
                      {lingua: texto for lingua in ("ENG", "DEU", "FRA", "BRA")}))
    if sem_texto:
        print(f"    textos citados sem texto nem no 5.8 (ficam sem string): {', '.join(sem_texto)}")
    return saida


@lru_cache(maxsize=None)
def EFEITOS_CITADOS():
    """Os nomes de efeito (fc_<biblioteca>.<efeito>) que o lote cita nos campos *_fx."""
    skills = _skills_58()
    return frozenset(valor for nome in LOTE + DEPENDENCIAS for _tag, valor in skills[nome][1]
                     if valor.lower().startswith("fc_"))


@lru_cache(maxsize=None)
def FXC_DAS_SKILLS():
    """Os .fxc dos efeitos que o lote cita (cast_fx, fire_fx, ammo_fx, hit_fx...: fc_<biblioteca>.<efeito>)."""
    skills = _skills_58()
    libs = []
    for nome in LOTE + DEPENDENCIAS:
        for _tag, valor in skills[nome][1]:
            if valor.lower().startswith("fc_"):
                chave = f"fxc/{valor.split('.', 1)[0].lower()}.fxc"
                if chave not in libs:
                    libs.append(chave)
    return tuple(libs)


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
        if texto.startswith("\r\n", fim):  # o arquivo e CRLF
            fim += 2
        elif texto.startswith("\n", fim):
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


#: Efeitos que o rebuild_50_skill_effects.py nao aprova (poucos exemplos ou presenca < 70%): o
#: template sai inteiro daqui, com a traducao campo a campo de skills oficiais do 5.0 com o mesmo
#: efeito -- shield/statup: CH_ProtectSelf_G1 (1201) e 161; mphealinstant: 1370; mpheal: 1490 e
#: 21308; boostheal: P_HealMastery_G1 (108) e 1146 (reserved9=1 -> <onfly/>); delayedskill: 18683.
#: Cabecalho, properties, custo e motion seguem o que o gerador fez nas irmas do Bard (22134...).
#: fphealinstant: RA_RestoreWing_G1 (701) e 20059; resurrect: CL_Revive_G1 (972, reserved6 = a
#: skill do debuff pelo nome); statup com reserved6=1/reserved9=1: FI_BoostWing_G1 (335).
EFEITOS_MANUAIS = {"Shield", "StatUp", "MPHeal_Instant", "MpHeal", "BoostHealEffect", "DelayedSkill",
                   "FPHeal_Instant", "Resurrect", "BoostSkillCastingTime", "Heal_Instant", "Rebirth",
                   "DispelDebuff", "DeboostHealAmount", "Sleep", "Deform", "StatDown"}
#: Token do StatUp -> (stat, sinal). O sinal e o que o 5.0 usa: attackDelay positivo no cliente vira
#: ATTACK_SPEED negativo em 351 de 372 statup oficiais (menos atraso = mais rapido); speed, 366 de 366 igual.
STAT_DO_CLIENTE = {"pvpdefendratio": ("PVP_DEFEND_RATIO", 1), "flyspeed": ("FLY_SPEED", 1),
                   "speed": ("SPEED", 1), "attackdelay": ("ATTACK_SPEED", -1), "maxhp": ("MAXHP", 1),
                   # SC_PandemoniumProtect_G1 e RA_ParalyzeArrow_G1: as quatro resistencias com o mesmo valor
                   "elementaldefendall": (("WATER_RESISTANCE", "WIND_RESISTANCE", "FIRE_RESISTANCE",
                                           "EARTH_RESISTANCE"), 1),
                   "magicalresist": ("MAGICAL_RESIST", 1)}
#: reserved3 do BoostSkillCastingTime: PR_SagesWisdom_G1 (none), CH_NightWish_G1 (Heal), RA_TrapperMode_G1.
CASTING_DO_CLIENTE = {"none": "BOOST_CASTING_TIME", "heal": "BOOST_CASTING_TIME_HEAL",
                      "summontrap": "BOOST_CASTING_TIME_TRAP"}
#: heal_instant: KN_LayHand_G1 (428); rebirth: PR_ReviveHand_G1 (1041, reserved6 = debuff pelo nome).
#: Elemento do cliente -> SkillElement do servidor (Air vira WIND, como no RA_RestoreWing_G1).
ELEMENTO = {"air": "WIND"}
_ENUM = {"targetorme": "TARGETORME", "debuffphy": "DEBUFF_PHYSICAL",
         "debuffmen": "DEBUFF_MENTAL"}  # KN_AbsoluteScare_G1 (540)


def _enum(v):
    return _ENUM.get(v.lower(), v.upper())


def _efeitos(d):
    return [k for k in range(1, 5) if d.get(f"effect{k}_type")]


#: Os que o gerador reprova; StatUp e MPHeal_Instant ele faz sozinho, so entram aqui junto deles.
REPROVADOS_NO_GERADOR = {"Shield", "MpHeal", "BoostHealEffect", "DelayedSkill", "FPHeal_Instant", "Resurrect",
                         "BoostSkillCastingTime", "Rebirth", "DeboostHealAmount", "Sleep"}


def _tipo(valor):
    """Nome do efeito sem depender da grafia: o proprio 5.0 escreve MPHeal (66), MpHeal (35) e Mpheal (1)."""
    return {t.lower(): t for t in EFEITOS_MANUAIS}.get(valor.lower(), valor)


def _manual(d):
    tipos = {_tipo(d[f"effect{k}_type"]) for k in _efeitos(d)}
    return bool(tipos & REPROVADOS_NO_GERADOR) and tipos <= EFEITOS_MANUAIS


def _efeito_manual(d, k, ids):
    p = f"effect{k}_"
    g = lambda c, padrao="0": d.get(p + c) or padrao
    tipo = _tipo(d[p + "type"])
    comum = []
    if g("remain2") != "0":
        comum.append(("duration2", g("remain2")))
    if g("effectid") != "0":
        comum.append(("effectid", g("effectid")))
    comum.append(("e", k))
    if g("basiclv") != "0":
        comum.append(("basiclvl", g("basiclv")))
    # Acerto e critico do efeito, como o 5.0 escreve (RA_ParalyzeArrow_G1: acc_mod2 50 -> accmod2="50").
    if g("acc_mod2") != "0":
        comum.append(("accmod2", g("acc_mod2")))
    if g("critical_prob_mod2") != "0":
        comum.append(("critprobmod2", g("critical_prob_mod2")))
    if g("noresist") == "1":
        comum.append(("noresist", "true"))
    if g("reserved10", "") and tipo not in ("Shield",):
        comum.append(("element", ELEMENTO.get(g("reserved10").lower(), g("reserved10").upper())))
    if g("cond_preeffect", ""):
        comum += [("preeffect", g("cond_preeffect")[1:]), ("preeffect_prob", g("cond_preeffect_prob2", "100"))]
    hop = [("hoptype", g("hop_type").upper()), ("hopb", g("hop_b"))] if g("hop_type", "") and g("hop_b") != "0" else []
    attrs = lambda pares: " ".join(f'{a}="{_xml_attr(v)}"' for a, v in pares)
    if tipo == "Shield":
        pares = [("hitvalue", g("reserved2")), ("hitdelta", g("reserved1")), ("value", g("reserved8")),
                 ("delta", g("reserved7"))] + ([("percent", "true")] if g("reserved6") == "1" else []) + comum
        if g("reserved_cond1", ""):
            pares += [("hittype", g("reserved_cond1").upper()), ("hittypeprob2", g("reserved_cond1_prob2", "1000"))]
        return f"\t\t\t<shield {attrs(pares + hop)}/>\n"
    if tipo in ("StatUp", "StatDown"):
        # 1o stat: reserved13/reserved2/reserved6; 2o: reserved14/reserved4/reserved7 (FI_BerserkStance_G1).
        # No StatDown o 5.0 escreve o valor negado (magicalresist: 26 de 26; elementaldefendall: 44 de 44).
        negado = -1 if tipo == "StatDown" else 1
        changes = ""
        for campo_stat, campo_valor, campo_pct in (("reserved13", "reserved2", "reserved6"),
                                                   ("reserved14", "reserved4", "reserved7")):
            if not g(campo_stat, ""):
                continue
            stats, sinal = STAT_DO_CLIENTE[g(campo_stat).lower()]
            func = "PERCENT" if g(campo_pct) == "1" else "ADD"
            valor = int(g(campo_valor)) * sinal * negado
            for stat in ((stats,) if isinstance(stats, str) else stats):
                changes += f"\t\t\t\t<change stat=\"{stat}\" func=\"{func}\" value=\"{valor}\""
                if g("reserved9") == "1":
                    changes += ">\n\t\t\t\t\t<conditions>\n\t\t\t\t\t\t<onfly/>\n\t\t\t\t\t</conditions>\n\t\t\t\t</change>\n"
                else:
                    changes += "/>\n"
        tag = tipo.lower()
        return f"\t\t\t<{tag} {attrs(comum + hop)}>\n{changes}\t\t\t</{tag}>\n"
    if tipo == "Sleep":  # RA_ParalyzeArrow_G1 (695)
        return f"\t\t\t<sleep {attrs(comum + hop)}/>\n"
    if tipo == "Deform":
        # WI_CursedTree_G1 (1454): model = id do NPC citado pelo nome (reserved9), type = reserved8.
        pares = [("model", NPCS_DE_DEFORM[g("reserved9")]), ("type", g("reserved8", "None").upper())] + comum
        return f"\t\t\t<deform {attrs(pares + hop)}/>\n"
    if tipo == "BoostSkillCastingTime":
        stat = CASTING_DO_CLIENTE[g("reserved3", "none").lower()]
        return (f"\t\t\t<boostskillcastingtime {attrs(comum + hop)}>\n"
                f"\t\t\t\t<change stat=\"{stat}\" func=\"PERCENT\" value=\"{g('reserved2')}\"/>\n"
                "\t\t\t</boostskillcastingtime>\n")
    if tipo == "Heal_Instant":
        pares = [("value", g("reserved2"))] + ([("delta", g("reserved1"))] if g("reserved1") != "0" else []) + \
                ([("percent", "true")] if g("reserved6") == "1" else []) + comum
        return f"\t\t\t<healinstant {attrs(pares + hop)}/>\n"
    if tipo == "DispelDebuff":  # PR_HolyGrail_G1 (1165), PR_Tranquility_G1 (1042)
        pares = [("dispel_level", g("reserved16")), ("power", g("reserved18")), ("value", g("reserved2"))] + comum
        return f"\t\t\t<dispeldebuff {attrs(pares + hop)}/>\n"
    if tipo == "DeboostHealAmount":
        # HEAL_SKILL_DEBOOST com o valor do cliente negado, nos 4 oficiais (PR_CourseWound_G1: 50 -> -50).
        # O Ba_SongofBless tem -6: +6, "increases the effect of HP recovery received".
        return (f"\t\t\t<deboostheal {attrs(comum + hop)}>\n"
                f"\t\t\t\t<change stat=\"HEAL_SKILL_DEBOOST\" func=\"PERCENT\" value=\"{-int(g('reserved2'))}\"/>\n"
                "\t\t\t</deboostheal>\n")
    if tipo == "Rebirth":
        pares = [("resurrect_percent", g("reserved2")), ("skill_id", ids[g("reserved6")])] + comum
        return f"\t\t\t<rebirth {attrs(pares + hop)}/>\n"
    if tipo == "FPHeal_Instant":
        pares = [("value", g("reserved2"))] + ([("delta", g("reserved1"))] if g("reserved1") != "0" else []) + \
                ([("percent", "true")] if g("reserved6") == "1" else []) + comum
        return f"\t\t\t<fphealinstant {attrs(pares + hop)}/>\n"
    if tipo == "Resurrect":
        pares = [("skill_id", ids[g("reserved6")])] + comum
        return f"\t\t\t<resurrect {attrs(pares + hop)}/>\n"
    if tipo == "MPHeal_Instant":
        pares = [("value", g("reserved2")), ("delta", g("reserved1"))] + \
                ([("percent", "true")] if g("reserved6") == "1" else []) + comum
        return f"\t\t\t<mphealinstant {attrs(pares + hop)}/>\n"
    if tipo == "MpHeal":
        pares = [("checktime", g("checktime")), ("value", g("reserved9")), ("delta", g("reserved8"))] + \
                ([("percent", "true")] if g("reserved6") == "1" else []) + comum
        return f"\t\t\t<mpheal {attrs(pares)}/>\n"
    if tipo == "BoostHealEffect":
        cond = "\t\t\t\t\t<conditions>\n\t\t\t\t\t\t<onfly/>\n\t\t\t\t\t</conditions>\n" if g("reserved9") == "1" else ""
        change = f"\t\t\t\t<change stat=\"HEAL_SKILL_BOOST\" func=\"PERCENT\" value=\"{g('reserved2')}\""
        change += f">\n{cond}\t\t\t\t</change>\n" if cond else "/>\n"
        return f"\t\t\t<boostheal {attrs(comum)}>\n{change}\t\t\t</boostheal>\n"
    if tipo == "DelayedSkill":
        pares = [("skill_id", ids[g("reserved1")]), ("value", g("reserved2"))] + comum
        return f"\t\t\t<delayedskill {attrs(pares)}/>\n"
    raise ValueError(tipo)


def _template_manual(id_novo, d, nome, ids):
    passiva = (d.get("activation_attribute") or "").lower() == "passive"
    attrs = [("skill_id", id_novo), ("name_en", nome[1]), ("name_pt", nome[1]), ("nameId", nome[0]),
             ("delayId", d.get("delay_id") or id_novo), ("stack", d["name"].upper()), ("lvl", 1),
             ("skilltype", (d.get("type") or "PHYSICAL").upper()), ("skillsubtype", _enum(d.get("sub_type") or "None")),
             ("tslot", _enum(d.get("target_slot") or "None")),
             ("activation", (d.get("activation_attribute") or "ACTIVE").upper()),
             ("cooldown", int(float(d.get("delay_time") or 0)) // 100),
             ("duration", 0 if d.get("instant_skill") == "1" else int(float(d.get("casting_delay") or 0)))]
    if d.get("dispel_category"):
        attrs.append(("dispel_category", _enum(d["dispel_category"])))
    if d.get("required_dispel_level"):
        attrs.append(("req_dispel_level", d["required_dispel_level"]))
    if d.get("cancel_rate"):
        attrs.append(("cancel_rate", d["cancel_rate"]))
    if d.get("ammo_speed"):
        attrs.append(("ammospeed", d["ammo_speed"]))
    if d.get("chain_skill_prob2"):
        attrs.append(("chain_skill_prob", d["chain_skill_prob2"]))
    alvo = _enum(d.get("first_target") or "Me")
    if passiva:
        props = '\t\t<properties first_target="ME"/>\n'
    else:
        p = [("first_target", alvo)]
        if alvo == "TARGETORME" and d.get("revision_distance"):
            p.append(("revision_distance", int(d["revision_distance"]) * 2))
        if (d.get("target_species_restriction") or "").upper() == "PC":  # CL_Revive_G1 (972)
            p.append(("target_species", "PC"))
        p += [("first_target_range", d.get("first_target_valid_distance") or "0"),
              ("target_relation", _enum(d.get("target_relation_restriction") or "All")),
              ("target_type", _enum(d.get("target_range") or "OnlyOne"))]
        # Area: raio e altura do cliente (21308, KN_Recover_G1); sem eles o raio fica 0.
        if (d.get("target_range") or "").lower() in ("area", "party"):
            p += [("target_maxcount", d.get("target_maxcount") or "1"),
                  ("target_distance", d.get("target_range_opt1") or "0"),
                  ("effective_range", d.get("target_range_opt1") or "0")]
            if d.get("target_range_opt3"):
                p.append(("effective_altitude", d["target_range_opt3"]))
        props = "\t\t<properties " + " ".join(f'{a}="{v}"' for a, v in p) + "/>\n"
    corpo = props
    custo = d.get("cost_parameter", "").upper() == "MP" and d.get("cost_end")
    # Custo em DP (cost_dp): <dp> e <dpuse>, como o gerador faz no Ba_SongofAnger_G1.
    dp = d.get("cost_dp") if d.get("cost_dp") not in (None, "", "0") else None
    if custo or dp:
        corpo += "\t\t<startconditions>\n"
        if custo:
            corpo += f'\t\t\t<mp value="{d["cost_end"]}" delta="{d.get("cost_end_lv") or 0}"/>\n'
        if dp:
            corpo += f'\t\t\t<dp value="{dp}"/>\n'
        corpo += "\t\t</startconditions>\n"
    if passiva or d.get("move_casting") != "1":
        corpo += '\t\t<useconditions>\n\t\t\t<playermove allow="false"/>\n\t\t</useconditions>\n'
    corpo += "\t\t<effects>\n" + "".join(_efeito_manual(d, k, ids) for k in _efeitos(d)) + "\t\t</effects>\n"
    if custo or dp:
        corpo += "\t\t<actions>\n"
        if custo:
            corpo += f'\t\t\t<mpuse value="{d["cost_end"]}" delta="{d.get("cost_end_lv") or 0}"/>\n'
        if dp:
            corpo += f'\t\t\t<dpuse value="{dp}"/>\n'
        corpo += "\t\t</actions>\n"
    if not passiva and d.get("motion_name"):
        corpo += f'\t\t<motion name="{d["motion_name"]}"/>\n'
    return "\t<skill_template " + " ".join(f'{k}="{_xml_attr(v)}"' for k, v in attrs) + ">\n" + corpo + "\t</skill_template>\n"


def _template_minimo(id_novo, campos, textos_por_nome, ids=None):
    d = dict(campos)
    if ids is not None and _manual(d):
        return _template_manual(id_novo, d, textos_por_nome[d["desc"]], ids)
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
    # Nome -> id: as do 5.0 (JA_NO_50 e as citadas pelo nome, como o CL_ResurrectDebuff 8296) e as do lote.
    ids = dict(_ids_50())
    ids.update({nome: i for nome, (i, _c) in convertidas.items()})
    novos = {i: _template_minimo(i, c, textos_por_nome, ids) for i, c in convertidas.values()}
    arvore = "".join(f'\t<skill name="{nome.lower()}" skillId="{ids[nome]}" skillLevel="1" minLevel="{nivel}" '
                     f'race="PC_ALL" classId="{CLASSE}" autoLearn="true" />\n' for _l, nome, nivel in linhas)
    for base in SERVIDOR:
        caminho = os.path.join(base, TEMPLATES_REL)
        with open(caminho, encoding="utf-8", newline="") as f:
            texto = f.read()
        # O skill_templates.xml e CRLF: os blocos vao com a quebra do arquivo (com LF, os fix_50_*,
        # que procuram os blocos pela quebra do arquivo, nao achavam o <startconditions> e criavam
        # outro antes do <properties> -- o XSD recusou e o servidor nao subiu).
        eol = "\r\n" if "\r\n" in texto[:4096] else "\n"
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
            insercoes.append((depois, novos[id_novo].replace("\n", eol)))
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
        eol = "\r\n" if "\r\n" in texto[:4096] else "\n"
        texto = re.sub(r'\t<skill [^>]*classId="%s"[^>]*/>\r?\n' % CLASSE, "", texto)
        fim = texto.rindex("</skill_tree>")
        texto = texto[:fim] + arvore.replace("\n", eol) + texto[fim:]
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(texto)
        print(f"OK  {base}: +{len(novos)} templates minimos, +{len(linhas)} linhas {CLASSE} na arvore")


# --------------------------------------------------------------------------------------------
# NPCs de Deform: Requiem (Ar_SongofRest_G1) e Freestyle (Ba_Lullaby_G1) transformam o alvo num NPC
# do 5.8 (a dancarina, Monster/PolyDancer). O cliente acha o NPC pelo nome (reserved9 do Deform); o
# servidor, pelo id (<deform model=>), como o WI_CursedTree_G1 do 5.0 (NPC 201046, com template).
# Os ids do 5.8 (201081/201082) sao de monstros de Teva no 5.0: os NPCs ganham ids livres.
# O modelo e o polymorph do pinguim LM (texturas pc_polymorph/penguinlm*, que o 5.0 ja tem) com uma
# animacao de PC (LM_Nidle_sleepwalking1/2), que so o 5.8 tem.
# --------------------------------------------------------------------------------------------
NPCS_DE_DEFORM = {"Ar_SongofRest_G1_NPC": 299901, "Ba_Lullaby_G1_NPC": 299902}
ID_BASE_STRING_NPC = 1991900  # faixa propria: nao desloca os ids dos textos das skills
PAK_NPCS_58 = r"Data\Npcs\Npcs.pak"
#: As tres copias gerais e as tres da Europa: o cliente usa a de data\europe (so com as gerais o NPC
#: nao entrava na tabela de NPCs do tables.dmp e o Deform nao mostrava modelo), como nos itens.
PAKS_DE_NPC = (r"data\npcs\npcs.pak", r"data\npcs\special\special.pak", r"data\npcs\special2\special2.pak",
               r"data\europe\Npcs\Npcs.pak", r"data\europe\Npcs\special\special.pak",
               r"data\europe\Npcs\special2\special2.pak")
#: Paks que nenhum outro passo regrava (o LM 019/020 sao das animacoes de classe e de harpa).
PAK_MODELO_NPC = r"objects\monster\Mesh_Meshes_037.pak"
PAK_ANIMACAO_NPC = r"objects\pc\lm\animation\Animation_Animations_018.pak"
REPO_NPCS = os.path.join(T.REPO, "Ferramentas e Documentos", "Client e Coletas", "Client 5.0 - Dados Extraidos",
                         "data", "npcs")


@lru_cache(maxsize=None)
def _npcs_58():
    """{nome: bloco <npc_client> do 5.8} dos NPCs de deform."""
    d, idx = aion_pak.abre(os.path.join(T.LIVE_CLIENTE, PAK_NPCS_58))
    texto = aion_bxml.decodifica(aion_pak.le(d, next(e for e in idx if e.nome.lower() == "client_npcs_npc.xml")))
    saida = {}
    for nome in NPCS_DE_DEFORM:
        m = re.search(r"  <npc_client>\s*<id>\d+</id>\s*<name>%s</name>.*?</npc_client>" % re.escape(nome), texto, re.S)
        if not m:
            raise ValueError(f"{nome} nao esta no client_npcs do 5.8")
        saida[nome] = m.group(0)
    return saida


def npcs_convertidos():
    """{nome: texto do <npc_client> no formato do 5.0}: id novo, so as tags que o 5.0 tem."""
    texto50 = open(os.path.join(REPO_NPCS, "client_npcs.xml"), encoding="utf-8").read()
    tags50 = set(re.findall(r"<([a-z0-9_]+)>", texto50))
    saida = {}
    for nome, bloco in _npcs_58().items():
        bloco = re.sub(r"<id>\d+</id>", f"<id>{NPCS_DE_DEFORM[nome]}</id>", bloco, count=1)
        linhas = [l for l in bloco.split("\n")
                  if not (re.match(r"\s*<([a-z0-9_]+)>[^<]*</\1>\s*$", l)
                          and re.match(r"\s*<([a-z0-9_]+)>", l).group(1) not in tags50)]
        saida[nome] = "\n".join(linhas)
    return saida


@lru_cache(maxsize=None)
def STRINGS_DOS_NPCS():
    """Os textos (desc) dos NPCs de deform, do client_strings_npc do 5.8 em ingles."""
    d, idx = aion_pak.abre(STRINGS_ENG[0])
    t = aion_bxml.decodifica(aion_pak.le(d, next(e for e in idx if e.nome.lower() == "strings/client_strings_npc.xml")))
    eng = {m.group(1).lower(): m.group(2) for m in re.finditer(r"<name>([^<]+)</name>\s*<body>(.*?)</body>", t, re.S)}
    nomes = []
    for bloco in _npcs_58().values():
        desc = re.search(r"<desc>([^<]+)</desc>", bloco).group(1)
        if desc not in nomes:
            nomes.append(desc)
    return tuple(("strings/client_strings_npc.xml", ID_BASE_STRING_NPC + k, nome,
                  {lingua: eng[nome.lower()].replace("\r\n", "\n") for lingua in ("ENG", "DEU", "FRA", "BRA")})
                 for k, nome in enumerate(nomes))


def _arquivos_do_modelo():
    """({nome: bytes} do modelo, {nome: bytes} das animacoes), do 5.8, prontos para o 5.0."""
    import glob
    modelo = {}
    for p in glob.glob(os.path.join(T.LIVE_CLIENTE, "Objects", "Monster", "Mesh_Meshes_*.pak")):
        d, idx = aion_pak.abre(p)
        for e in idx:
            if e.nome.lower().startswith("polydancer/") and e.nome not in modelo:
                dados = aion_pak.le(d, e)
                if e.nome.lower().endswith(".cal"):
                    # O 5.0 guarda as animacoes de PC em PC\, o 5.8 em PC2\ (como nas animacoes de classe).
                    dados = dados.replace(b"PC2\\", b"PC\\")
                modelo[e.nome] = dados
    cafs = sorted({c.decode("latin-1").replace("/", "\\").rsplit("\\", 1)[-1]
                   for n, dados in modelo.items() if n.lower().endswith(".cal")
                   for c in re.findall(rb"=\s*(\S+\.caf)", dados, re.I)})
    animacoes = T.do_58(os.path.join("Objects", "PC2", "lm", "animation"), cafs)
    if len(animacoes) != len(cafs) or len(modelo) != 6:
        raise ValueError(f"modelo da dancarina incompleto no 5.8: {sorted(modelo)} {sorted(animacoes)}")
    return modelo, animacoes


def aplica_npcs_cliente():
    elementos = [ET.fromstring(t) for t in npcs_convertidos().values()]
    for rel in PAKS_DE_NPC:
        caminho = os.path.join(T.CLIENTE, rel)
        origem = caminho + T.SUFIXO_BACKUP if os.path.exists(caminho + T.SUFIXO_BACKUP) else caminho
        d, idx = aion_pak.abre(origem)
        entrada = next(e for e in idx if e.nome.lower() == "client_npcs.xml")
        bxml = aion_pak.le(d, entrada)
        texto = aion_bxml.decodifica(bxml)
        for i in NPCS_DE_DEFORM.values():
            if f"<id>{i}</id>" in texto:
                raise ValueError(f"{rel}: o id {i} ja existe")
        novo, _ = T.acrescenta_filhos(bxml, elementos)
        T._backup(caminho)
        if origem != caminho:
            shutil.copy2(origem, caminho)
        T.regrava_pak(caminho, troca={entrada.nome: novo})
        T._confere_pak(caminho, len(idx), {entrada.nome: "troca"})
        lido = aion_bxml.decodifica(aion_pak.le(*_entrada_do_pak(caminho, "client_npcs.xml")))
        for nome, i in NPCS_DE_DEFORM.items():
            assert f"<id>{i}</id>" in lido and f"<name>{nome}</name>" in lido, (rel, nome)
        print(f"OK  {rel}: +{len(elementos)} NPCs ({', '.join(f'{n} {i}' for n, i in NPCS_DE_DEFORM.items())})")
    modelo, animacoes = _arquivos_do_modelo()
    for rel, novos in ((PAK_MODELO_NPC, modelo), (PAK_ANIMACAO_NPC, animacoes)):
        caminho = os.path.join(T.CLIENTE, rel)
        origem = caminho + T.SUFIXO_BACKUP if os.path.exists(caminho + T.SUFIXO_BACKUP) else caminho
        _d, idx = aion_pak.abre(origem)
        if {e.nome.lower() for e in idx} & {n.lower() for n in novos}:
            raise ValueError(f"{rel} ja tem parte de {sorted(novos)}")
        T._backup(caminho)
        if origem != caminho:
            shutil.copy2(origem, caminho)
        T.regrava_pak(caminho, acrescenta=novos)
        T._confere_pak(caminho, len(idx), {n: "novo" for n in novos})
        print(f"OK  {rel}: +{len(novos)} ({', '.join(sorted(novos))})")


def _entrada_do_pak(caminho, nome):
    d, idx = aion_pak.abre(caminho)
    return d, next(e for e in idx if e.nome.lower() == nome)


def aplica_npcs_repo():
    blocos = npcs_convertidos()
    for pasta in ("", "special", "special2"):
        caminho = os.path.join(REPO_NPCS, pasta, "client_npcs.xml")
        if not os.path.exists(caminho):
            continue
        with open(caminho, encoding="utf-8", newline="") as f:
            xml = f.read()
        nl = "\r\n" if "\r\n" in xml else "\n"
        xml = xml.replace("\r\n", "\n")
        for i in NPCS_DE_DEFORM.values():  # reaplicar nao duplica
            xml = re.sub(r"  <npc_client>\s*<id>%d</id>.*?</npc_client>\n" % i, "", xml, flags=re.S)
        fim = xml.rindex("</npc_clients>")
        xml = xml[:fim] + "".join(b + "\n" for b in blocos.values()) + xml[fim:]
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(xml.replace("\n", nl))
        print(f"OK  repo {os.path.join('npcs', pasta, 'client_npcs.xml')}: +{len(blocos)} NPCs")


NPC_TEMPLATES_REL = os.path.join("npcs", "npc_templates.xml")


def aplica_npcs_servidor():
    """npc_template de cada NPC no molde do 201046 (WI_CursedTree_G1_NPC): so o modelo do Deform."""
    textos = {nome: (i, t["ENG"]) for _a, i, nome, t in STRINGS_DOS_NPCS()}
    blocos = []
    for nome, bloco in _npcs_58().items():
        g = lambda k: re.search(r"<%s>([^<]*)</%s>" % (k, k), bloco).group(1)
        id_string, texto = textos[g("desc")]
        meia = lambda v: f"{float(v) / 2:g}"
        blocos.append(
            f'\t<npc_template npc_id="{NPCS_DE_DEFORM[nome]}" level="1" name_en="{_xml_attr(texto)}" '
            f'name_pt="{_xml_attr(texto)}" name_id="{id_string}" height="{float(g("upper")):g}" rank="DISCIPLINED" '
            f'rating="NORMAL" tribe="GENERAL" type="ABYSS_GUARD" ai="useitem" sangle="0" '
            f'attack_speed="{g("attack_delay")}" hpgauge="{g("hpgauge_level")}">\n'
            f'\t\t<stats maxHp="14614">\n'
            f'\t\t\t<speeds walk="{float(g("move_speed_normal_walk")):g}" group_walk="{float(g("move_speed_normal_walk")):g}" '
            f'run="{float(g("move_speed_normal_run")):g}" run_fight="{float(g("move_speed_combat_run")):g}" '
            f'group_run_fight="{float(g("move_speed_combat_run")):g}" />\n'
            f'\t\t</stats>\n'
            f'\t\t<bound_radius front="{meia(g("front"))}" side="{meia(g("side"))}" upper="{float(g("upper")):g}" />\n'
            f'\t</npc_template>\n')
    for base in SERVIDOR:
        caminho = os.path.join(base, NPC_TEMPLATES_REL)
        with open(caminho, encoding="utf-8", newline="") as f:
            texto = f.read()
        eol = "\r\n" if "\r\n" in texto[:4096] else "\n"
        for i in NPCS_DE_DEFORM.values():  # reaplicar nao duplica
            texto = re.sub(r'\t<npc_template npc_id="%d".*?</npc_template>\r?\n' % i, "", texto, flags=re.S)
        fim = texto.rindex("</npc_templates>")
        texto = texto[:fim] + "".join(blocos).replace("\n", eol) + texto[fim:]
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(texto)
        print(f"OK  {base}: +{len(blocos)} npc_template")


def confere_servidor():
    """As duas copias do servidor: iguais, validas no static_data.xsd agregado, todo template do lote
    com efeito e com o <chain> igual ao do cliente (category/precategory/time). Devolve os erros."""
    from lxml import etree
    skills = _skills_58()
    ids = ids_novos(skills)
    erros = []
    textos = []
    for base in SERVIDOR:
        with open(os.path.join(base, TEMPLATES_REL), encoding="utf-8", newline="") as f:
            textos.append(f.read())
    if textos[0] != textos[1]:
        erros.append("as duas copias do skill_templates.xml diferem")
    esquema = etree.XMLSchema(etree.parse(os.path.join(SERVIDOR[1], "static_data.xsd")))
    for rel in (TEMPLATES_REL, ARVORE_REL):
        if not esquema.validate(etree.parse(os.path.join(SERVIDOR[1], rel))):
            erros.append(f"{rel}: {list(esquema.error_log)[0]}")
    blocos = {sid: textos[1][ini:fim] for sid, ini, fim in _templates(textos[1])}
    for nome in LOTE + DEPENDENCIAS:
        d = dict(skills[nome][1])
        bloco = blocos.get(ids[nome], "")
        if "<effects>" not in bloco:
            erros.append(f"{nome}: sem efeito")
        cadeias = [dict(re.findall(r'(\w+)="([^"]*)"', c)) for c in re.findall(r"<chain ([^>]*)/>", bloco)]
        quer = {}
        if d.get("chain_category_name"):
            quer["category"] = d["chain_category_name"].upper()
            if d.get("prechain_category_name"):
                quer["precategory"] = d["prechain_category_name"].upper()
            if d.get("chain_time") and d["chain_time"] != "0":
                quer["time"] = d["chain_time"]
        if (cadeias or [{}])[0] != quer or len(cadeias) > 1:
            erros.append(f"{nome}: <chain> {cadeias} != cliente {quer}")
    return erros


def main():
    if "--npcs" in sys.argv:
        aplica_npcs_repo()
        aplica_npcs_cliente()
        aplica_npcs_servidor()
        print("Os textos dos NPCs vao pelo `teste_harpa_58.py --strings`.")
        return
    if "--confere-servidor" in sys.argv:
        erros = confere_servidor()
        print("\n".join(erros) if erros else "OK  servidor: copias iguais, XSD valido, efeitos e cadeias do Bard iguais ao cliente")
        sys.exit(1 if erros else 0)
    skills = _skills_58()
    ids = ids_novos(skills)
    convertidas, fora = converte(skills, ids, _campos_50())
    niveis = _aprendizado_58()
    linhas = aprendizado(niveis)
    textos = strings(convertidas)
    print("Lote:")
    for nome, (id_novo, campos) in convertidas.items():
        d = dict(campos)
        print(f"  {nome}: 5.8 {skills[nome][0]} -> {id_novo}, nivel {niveis.get(nome, '- (dependencia)')}, "
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
        print("Proximo: rebuild_50_skill_effects.py --ids <ids do Bard> --aplicar (corpo dos templates minimos),")
        print("depois fix_50_chain.py (<chain> do cliente: sem ele a skill que abre a cadeia a reseta) e")
        print("levar so os templates 22xxx do Bard para as duas copias do servidor, e por fim")
        print("bard_skills_58.py --confere-servidor (sai com erro se alguma cadeia ou copia nao bate).")
        return
    arquivos_de_icone = icones(convertidas)
    aplica_cliente(convertidas, linhas, arquivos_de_icone)
    aplica_repo(convertidas, linhas)
    print("Os textos vao pelo `teste_harpa_58.py --strings` (mesmo pak das outras strings).")


if __name__ == "__main__":
    main()
