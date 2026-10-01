#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditoria e Refinamento Cirúrgico de Nomes e Descrições de Magias/Habilidades (Aion Classic 5.0 PT-BR)
Corrige:
1. Resíduos de dicionário (: a), • 1 baixo, etc.) em nomes e descrições de habilidades
2. Nomes corrompidos / cópias errôneas (Large-Scale Frontal Strike, Retorno: Onda, etc.)
3. Aberrações de vocabulário ('idéia Divino' -> 'General Divino', 'Crack faz' -> 'Fissura Dilacerante')
4. Possessivos anglo-saxões ('s e ’s) em habilidades e efeitos de controle
5. Adjetivos prefixados e ordem frasal em magias
6. Aprisionamento do Éter ('Éter's Manter' / 'Éter’s Manter') em combos e descrições
7. Preserva integralmente todas as tags de CryEngine ([%...]) e sintaxe XML
"""

import os
import sys
import re
import argparse
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

CLIENT_STRINGS_DIR = "Ferramentas e Documentos/Client e Coletas/Tradução - Português Brasil/strings"

# Dicionário de substituições exatas por <name> em client_strings_skill.xml
EXACT_SKILL_REPLACEMENTS = {
    # Nomes com cópias errôneas / corrupções
    'STR_SKILL_Returnhome1_skin_12': 'Retorno: Onda',
    'STR_event_baseball_fireball': 'Golpe Frontal em Larga Escala',
    'STR_event_baseball_firestorm': 'Golpe Descendente',
    'STR_item_iddokkaebi_dokkaebigamtu_01': 'Olho de Dokkaebi',
    'STR_IDInfinity_2F_Shield_DESC_Abnormal': 'Imune a todos os ataques.',
    'STR_IDArena_team01_S5_Named_AreaATK_Abnormal': 'O efeito de recuperação é reduzido.',
    'STR_Station_Hugen_Slow': 'Sob a Garra',
    'STR_Artifact_ldf4b_40131_skill': 'Fissura Dilacerante',
    'STR_LDF4b_T1_Artifact_Crack_Stumble_MpAtk_G1_DESC': 'Fissura Dilacerante',
    'STR_DF4_Artifact_LegendofPhantom1_G1': 'Travessura de Alukina',
    'STR_BNFI_Summon_Nr': 'Boas-vindas da Rainha',
    'STR_Artifact_ab1_12231_skill': 'Efluxo Dévico',
    'STR_Artifact_ab1_12431_skill': 'Égide Abissal',
    'STR_Artifact_ab1_12131_skill': 'Aperto Restaurador',
    'STR_Artifact_ab1_12331_skill': 'Aperto Restaurador',
    'STR_SKILL_Abyss_Artifact_HandofMirage_G1': 'Aperto Restaurador',
    'STR_SKILL_Abyss_Artifact_HandofMirage_G2': 'Aperto Restaurador',
    'STR_SKILL_Abyss_Artifact_HandofMirage_G1_Proc': 'Efeito de Aperto Restaurador',
    'STR_SKILL_RA_SnipeShot_G2': 'Olho de Touro II',
    'STR_SKILL_RA_HunterMind_G1': 'Poder do Caçador I',
    'STR_SKILL_WI_AbysalSlayer_G2': 'Ira de Lumiel II',
    'STR_LDF4b_TiamatDrakanNmd_RangeAtk_t1': 'Arremesso de Tiamat',
    'STR_LDF4b_TiamatDrakanNmd_RangeAtk_t2': 'Arremesso de Tiamat',
    'STR_IDLDF1_AllAtkUP_Self': 'Ira do Senhor dos Dragões',
    'STR_Tdown_Seal_LDF4_Def_55L_Death_FireDMG_G1': 'Maldição do Senhor dos Dragões',
    'STR_BattleMaster_IDEvent_04_PvE_Buff_1': 'Grito de Guerra do Lutador',
    'STR_fighter_IDEvent_04_PvE_Buff_1': 'Grito de Guerra do Gladiador',
    'STR_priest_IDEvent_04_PvE_Buff_1': 'Grito de Guerra do Clérigo',
    'STR_wizard_IDEvent_04_PvE_Buff_1': 'Grito de Guerra do Feiticeiro',
    'STR_Arena_pvp01_S6_buff01': 'Aura da Bênção',
    'STR_Arena_pvp02_S1_heal': 'Aura da Bênção',
    'STR_Arena_pvp02_S2_heal': 'Aura da Bênção',
    'STR_LU_RainThunder_G1': 'Dilúvio Sagrado I',
    'STR_IDCubeQ_BNMA_Shield_HolyServant': 'Escudo de Espelho Antigo',
    'STR_NPC_SKILL_SA_Tornado_Abnormal': 'Você está atordoado. Não pode usar habilidades físicas nem itens, tampouco se mover ou atacar.',
    'STR_Item_Skill_Event_Summon_fighter_60_Ae': '[Evento] Habilidade de Invocação do Doutor Elyosnik (General 5 Estrelas)',
    'STR_Classic_Seed_Skill_open_G1': 'Aprisionamento do Éter I',
    
    # Habilidades com "Funcionários avançados" (Advanced Staff Training)
    'STR_SKILL_P_EQUIP_Staff_G2': 'Treinamento Avançado com Cajado II',
    'STR_SKILL_P_EQUIP_Staff_G3': 'Treinamento Avançado com Cajado III',
    'STR_SKILL_P_EQUIP_Staff_G4': 'Treinamento Avançado com Cajado IV',
    'STR_SKILL_CH_EQUIP_Staff_G2': 'Treinamento Avançado com Cajado II',
    'STR_SKILL_CH_EQUIP_Staff_G3': 'Treinamento Avançado com Cajado III',
    'STR_SKILL_Stigma_P_EQUIP_Staff_G1': 'Treinamento Avançado com Cajado I',

    # Resíduos de Dicionário em Nomes e Habilidades
    'STR_SKILL_WI_LargeBurstKnockDown': 'Derrubada: Normal, Poder: Alto, Conjuração: Normal, Recarga: Lenta',
    'STR_AWI_Spellatk_LC_ArFr_Carrier': 'Explosão do Motor',
    'STR_AWI_Spellatk_LC_ArFr_Carrier_DESC': 'Explosão do Motor',
    'STR_IDYun_CallOfDude': 'Esgrima Real',
    'STR_Artifact_ldf4b_40531_skill': 'Escudo Central',
    'STR_LDF4b_C3_Artifact_Tiamat_StatUp_G1_DESC': 'Escudo Central',
    'STR_ST_spinKK_G2': 'Chute Giratório II',
    'STR_LDF4_Teva_Mission_Paralyze_DESC': 'Impede o movimento.',
    'STR_Item_Skill_Npc_Summon_Teva_QNMD_01': 'Tomo Amarelado Fantasma',
    'STR_IDEvent_04_TribeChange_TeamA': 'Takun, o Terrível, Controlado',
    'STR_Classic_Wind_A_MagBoostHP': 'Poder Mágico 23, HP 102',
    'STR_Classic_Wind_A_MagAccHP': 'Precisão Mágica 14, HP 89',
    'STR_IDTiamat_DrakanArcher_FrontAtk': 'Ataque Frontal',
    'STR_Re_LU_OpenSpace_G6': 'Profecia Mortal Encarnada VI',
    'STR_SKILL_AS_FrontAssault_G1': 'Golpe Frontal I',
    'STR_SKILL_AS_FrontAssault_G2': 'Golpe Frontal II',
    'STR_SKILL_AS_ShadowWalk_G1': 'Passo da Sombra I',
    'STR_SKILL_AS_Stigma_ShadowWalk_G1': 'Passo da Sombra I',
    'STR_NPR_BlindShort_Po_Eye': 'Bicada na Face',
    'STR_GAS_SatkSpinStun_Nr': 'Golpe Frontal',
    'STR_GAS_SatkSpinStun_Nr_DESC': 'Golpe Frontal',
    'STR_DGAS_SatkSpinStun_Nr': 'Golpe Frontal',
    'STR_DGAS_SatkSpinStun_Nr_DESC': 'Golpe Frontal',
    'STR_DGFI_H_SatkSpinStun_Nr': 'Golpe Frontal',
    'STR_DGFI_H_SatkSpinStun_Nr_DESC': 'Golpe Frontal',
    'STR_LF5_24_NamedBuff': 'Golpe Frontal',
    'STR_IDRaksha_SatkSA_Nr': 'Golpe Frontal',
    'STR_GNAS_Signet1LongTA_Front': 'Golpe Frontal de Longo Alcance',

    # Descrições com resíduos de dicionário e gramática severa
    'STR_SKILL_Death_DESC': 'Um efeito posterior temporário da morte, que diminui a velocidade de movimento por um curto período de tempo.',
    'STR_SKILL_WI_NeedlessMP_DESC': 'Aumenta temporariamente seu poder mágico. O MP torna-se 0 como efeito posterior.',
    'STR_SKILL_KN_ShieldImpact_G1_DESC': 'Inflige [%e1.SkillATK_Instant.MinDamage]~[%e1.SkillATK_Instant.MaxDamage] de dano físico no alvo e o coloca no estado [%e1.SkillATK_Instant.AddEffect].\nCausa dano adicional quando o alvo for um PNJ.\nHabilidade em Cadeia Nível 2\nContra-ataque com Escudo, Contra-ataque Provocador com Escudo, Golpe Vingativo – Esmagar Face.',
    'STR_SKILL_KN_ShieldImpact_G2_DESC': 'Inflige [%e1.SkillATK_Instant.MinDamage]~[%e1.SkillATK_Instant.MaxDamage] de dano físico no alvo e o coloca no estado [%e1.SkillATK_Instant.AddEffect].\nHabilidade em Cadeia Nível 3\nGolpe Vingativo, Corte no Tendão – Esmagar Face.',
    'STR_CLASSIC_EVENT_L_SHAPE_EGGMAN_01_DESC': 'Manurunerk cometeu um erro e transformou você em um ovo. Os ícones de certas poções mudarão. Fale com Manurunerk na capital se quiser obter uma solução improvisada do genial inventor.\nAntes de poder usar um item que altere sua aparência, você precisa reverter o erro de Manurunerk.',
    'STR_CLASSIC_EVENT_D_SHAPE_EGGMAN_01_DESC': 'Manurunerk cometeu um erro e transformou você em um ovo. Os ícones de certas poções mudarão. Fale com Manurunerk na capital se quiser obter uma solução improvisada do genial inventor.\nAntes de poder usar um item que altere sua aparência, você precisa reverter o erro de Manurunerk.',
    'STR_LU_tele_DESC': 'Teleporte-se para um alvo a até [%First_Target_Valid_Distance]m, cause [%e2.SpellATK_Instant.FixDamage] de dano de água e atordoe-o por [%e3.Atordoamento.RemainTime]. Ergue um escudo que bloqueia até 486 de dano.\nMulticonjuração 3 vezes.\nApós o uso você pode usar outra habilidade individual.',
    'STR_SKILL_AS_Re_SignetBlast_G1_DESC': 'Remove a runa vinculada a um alvo a até [%First_Target_Valid_Distance]m até o grau [%e1.SignetBurst.SignetGrade], fazendo-a detonar e causando dano; coloca o alvo em um estado de velocidade de ataque reduzida, silêncio e imobilização por 7 segundos.',
    'STR_LDF5_Fortress_Anoha_Summon_NormalFire_DESC_Abnormal': 'Você sofre dano em intervalos regulares. A condição pode ser removida com cura.',
    'STR_Start_Abnormal': 'Você canalizou sua energia interior e está em um estado fortalecido. Enquanto estiver neste estado, cada ataque tem [%e4.Provoker.ConditionProb]%% de chance de redefinir a recarga de todas as habilidades.',
    'STR_SKILL_Abyss_Artifact_BreathofHeaven_G2_Abnormal': 'Efeito gerado pelo artefato.\nSeu tempo máximo de voo aumentou e o tempo de conjuração de toda magia diminuiu.',
    'STR_SKILL_RA_MarksmanMode_G1_DESC': '[%e1.WeaponStatBoost.StatName] de [%e1.WeaponStatBoost.WeaponCategory] aumenta em [%e1.WeaponStatBoost.RateValue]%%. Você se move a uma velocidade muito baixa enquanto a habilidade estiver ativa.\nHabilidade Ativa\nHabilidade de Estigma',
    'STR_SKILL_RA_MarksmanMode_G2_DESC': '[%e1.WeaponStatBoost.StatName] de [%e1.WeaponStatBoost.WeaponCategory] aumenta em [%e1.WeaponStatBoost.RateValue]%%. Você se move a uma velocidade muito baixa enquanto a habilidade estiver ativa.\nHabilidade Ativa\nHabilidade de Estigma',
    'STR_NGR_Snare_Nr_DESC': 'Um ataque corpo a corpo que reduz significativamente a velocidade de movimento do alvo. O dano real infligido é baixo.',
    'STR_SKILL_RA_Stigma_PhoenixArrow_G1_DESC': 'Dispara uma flecha em um alvo a até [%First_Target_Valid_Distance]m para causar [%e1.SkillATK_Instant.MinDamage]-[%e1.SkillATK_Instant.MaxDamage] de dano físico. Este ataque tem baixa precisão.\nHabilidade de Estigma',
    'STR_SKILL_RA_Stigma_DestructArrow_G1_DESC': 'Dispara uma flecha em um alvo a até [%First_Target_Valid_Distance]m para causar [%e1.SkillATK_Instant.MinDamage]-[%e1.SkillATK_Instant.MaxDamage] de dano físico. Este ataque tem baixa precisão.\nHabilidade de Estigma',
    'STR_SKILL_RA_Stigma_AncientArrow_G1_DESC': 'Dispara uma flecha em um alvo a até [%First_Target_Valid_Distance]m para infligir [%e1.SkillATK_Instant.MinDamage]~[%e1.SkillATK_Instant.MaxDamage] de dano físico. Este ataque tem baixa precisão. Causa dano adicional quando o alvo for um PNJ.\nHabilidade de Estigma',
    'STR_SKILL_RA_Stigma_MysticArrow_G1_DESC': 'Dispara uma flecha em um alvo a até [%First_Target_Valid_Distance]m para infligir [%e1.SkillATK_Instant.MinDamage]~[%e1.SkillATK_Instant.MaxDamage] de dano físico. Este ataque tem baixa precisão. Causa dano adicional quando o alvo for um PNJ.\nHabilidade de Estigma',
    'STR_SKILL_Moros_Promise_G1_DESC': 'A cada ataque contra inimigos Drakan, Dracos e Naga, há [%e1.Provoker.ConditionProb]%% de chance de causar um dano adicional de [%e1.Provoker.OtherSkill.e1.ProcATK_Instant.dano].\n(No nível máximo há 20%% de chance de causar dano adicional.)',
    'STR_SKILL_Moros_Promise_G2_DESC': 'A cada ataque contra inimigos Drakan, Dracos e Naga, assim como chefes de instâncias principais, Batalhas de Fortaleza e incursões, há [%e1.Provoker.ConditionProb]%% de chance de causar um dano adicional de [%e1.Provoker.OtherSkill.e1.ProcATK_Instant.dano].\n(No nível máximo há 20%% de chance de causar dano adicional.)',
    'STR_SKILL_FI_Glory_DestructBlow_G1_DESC': 'Causa [%e1.SkillATK_Instant.MinDamage] a [%e1.SkillATK_Instant.MaxDamage] de dano físico a um alvo a até [%First_Target_Valid_Distance]m e coloca-o no estado [%e1.SkillATK_Instant.AddEffect]. A chance de acerto crítico desta habilidade é muito baixa.',
    'STR_SKILL_RA_ThroughShot_G1_DESC': 'Inflige [%e1.SkillATKDrain_Instant.MinDamage] a [%e1.SkillATKDrain_Instant.MaxDamage] de dano físico a até 6 inimigos dentro de um raio de [%First_Target_Valid_Distance]m e absorve [%e1.SkillATKDrain_Instant.HPHeal]%% de seu HP, antes de atordoá-los com uma probabilidade baixa.\nMulticonjuração 3 vezes.',
    'STR_TH_ThunderStorm_G1_DESC': 'Causa [%e1.SkillATK_Instant.MinDamage] a [%e1.SkillATK_Instant.MaxDamage] de dano físico a 4 inimigos à sua frente.\nReduz a recarga de Capacitor, Explosão Sônica, Supercondutor, Descarga Magnética e Clarão Tônico em 33%%. Causa dano adicional quando o alvo for um PNJ.\nMulticonjuração 3 vezes.\nHabilidade em Cadeia Nível 1\nHabilidade de Estigma\nApós o uso você pode usar outra habilidade individual.',

    # Pogus / Januerk Minigames
    'STR_IDPogusgame_DeformFear_Saam_Abnormal': 'Você se transforma em um Coelhinho de Fuligem de [%e2.Medo.RandomTime] a [%e2.Medo.RemainTime] e é dominado pelo medo.',
    'STR_IDPogusgame_DeformFear_Saam_DESC': 'Alvos dentro do alcance se transformam em um Coelhinho de Fuligem por [%e2.Medo.RandomTime] a [%e2.Medo.RemainTime] e são dominados pelo medo.',
    'STR_IDPogusgame_Polymorph_DeformFear_DESC': 'Alvos a até [%First_Target_Valid_Distance]m se transformam em um Saam Dourado por [%e2.Medo.RandomTime] a [%e2.Medo.RemainTime] e são dominados pelo medo.\nHabilidade exclusiva da Sala de Jogos de Januerk 5',
    'STR_IDPogusgame_Polymorph_DeformFear_Abnormal': 'Você se transforma em um Saam Dourado de [%e2.Medo.RandomTime] a [%e2.Medo.RemainTime] e é dominado pelo medo.',
    'STR_IDPogusgame_Polymorph_Resist_DESC': 'Você resiste a [%e1.AlwaysResist.Count] ataques mágicos por [%e1.AlwaysResist.RemainTime].\nHabilidade exclusiva da Sala de Jogos de Januerk 5',
    
    # Armadilha de Caçador (FairyFlare)
    'STR_SKILL_RA_FairyFlare_DESC': 'Posiciona uma armadilha a até [%First_Target_Valid_Distance]m de você. A armadilha dura [%e1.SummonTrap.SummonTime]. Quando um inimigo se aproxima a menos de 30m da armadilha, ela explode, revelando o inimigo.\nHabilidade de Estigma',
    
    # Espírito
    'STR_SKILL_EL_EtherCharge_G1_DESC': 'Recupera 100%% do HP do seu espírito.\nHabilidade de Estigma',
    'STR_EL_ConnectBoost_G1_DESC': 'O [%e1.StatUp.StatName] seu e do seu espírito é aumentado em [%e1.StatUp.Value] e o [%e1.StatUp.StatName2] em [%e1.StatUp.Value2] por [%e1.StatUp.RemainTime].\nHabilidade de Estigma',
    
    # Apóstolos
    'STR_Classic_Item_Skill_Trans_SielApostle_01_DESC': 'Você se transforma no Apóstolo de Siel por 60 minutos.',
    'STR_Classic_Item_Skill_Trans_NezekanApostle_01_DESC': 'Você se transforma no Apóstolo de Nezekan por 60 minutos.',
    'STR_Item_Skill_Trans_ArielApostle_Ring_01_DESC': 'Você se transforma no Apóstolo de Ariel por 60 minutos.\nEnquanto transformado, você tem 20%% de chance de reduzir o dano recebido em 100%%.',

    # Forte / Onça
    'STR_LU_ForteP_G2_DESC': 'Aumenta a velocidade de ataque sua e do seu grupo em 12%% e reduz o tempo de conjuração de todas as habilidades em 12%% por 2 minutos. Aumenta a eficácia das habilidades dos membros do seu grupo uma vez por 20 segundos. Compartilha recarga com Bênção Astral.\nHabilidade de Estigma',
    'STR_LU_ForteP_AD_G1_DESC': 'Aumenta seu [%e0.LU_ForteP_AD_proc.e1.StatUp.StatName] e o de aliados próximos em [%e0.LU_ForteP_AD_proc.e1.StatUp.Value]%% e reduz o tempo de conjuração de todas as habilidades em [%e0.LU_ForteP_AD_proc.e2.BoostSkillCastingTime.CastingBonus]%% por [%e0.LU_ForteP_AD_proc.e1.StatUp.RemainTime]. Aumenta a eficácia das habilidades dos membros do seu grupo uma vez por 20 segundos.\nHabilidade de Estigma',
    'STR_LU_ForteP_G1_DESC': 'Transforma você na semelhança do General Divino por 3 minutos. Isso parece ser tudo.',

    # Lume / Dente-de-leão / Etapas
    'STR_LU_RainSword_mini_G1_DESC': 'Inflige [%e1.SpellATK_Instant.FixDamage] de dano de água a um alvo dentro de um raio de [%First_Target_Valid_Distance]m e a até 6 inimigos dentro de 3m do alvo e coloca-os no estado [%e1.SpellATK_Instant.AddEffect].\nHabilidade em Cadeia Nível 2\nRemover Choque – Pequeno Presente de Lume',
    'STR_skin_Returnhome1_skin_06_long': 'Você sopra sementes de dente-de-leão no ar.',
    'STR_RB_Proc_Reflection_G1': 'Efeito de Bônus de Vingança Final I',
    'STR_RB_Proc_Reflection_G3': 'Efeito de Bônus de Vingança Final III',
    'STR_RB_Proc_Execution': 'Efeito de Bônus de Execução Final',
    'STR_SKILL_Gu_CurbingFireChain_G6': 'Saraivada Debilitante VI (não usado)',
    'STR_SKILL_Gu_BullsEye_G6': 'Olho Mágico do Tiro Preciso VI (não usado)',
    'STR_SKILL_Gu_BacksteppingSnipe_G6': 'Disparo em Retirada VI (não utilizado)',
    'STR_Polymorph_IDEvent_02_DESC_Abnormal': 'O potencial completo do Daeva se revela por um momento.',
    
    # Shield Bakarma
    'STR_IDDF3_Dragon_Boss_Shield_DESC': 'Um escudo protetor, que tem [%e1.Escudo.ConditionProb]%% de chance de absorver todo o dano por [%e1.Escudo.RemainTime] quando o General sofre [%e1.Escudo.Condition]. (O escudo protetor pode absorver um total de [%e1.Escudo.ShieldValue] de dano antes de ser destruído.) Se o escudo não estiver quebrado, você não poderá escapar da Ira de Bakarma.',
    'STR_IDDF3_Dragon_Boss_Shield_Abnormal': 'Um escudo protetor, que tem [%e1.Escudo.ConditionProb]%% de chance de absorver todo o dano por [%e1.Escudo.RemainTime] quando o General sofre [%e1.Escudo.Condition]. (O escudo protetor pode absorver um total de [%e1.Escudo.ShieldValue] de dano antes de ser destruído.) Se o escudo não estiver quebrado, você não poderá escapar da Ira de Bakarma.',

    # Combos / Efeitos de Controle
    'STR_ST_down_DESC': 'Causa [%e1.SkillATK_Instant.MinDamage]–[%e1.SkillATK_Instant.MaxDamage] de dano físico a um alvo imobilizado no Aprisionamento do Éter e, em seguida, derruba-o no ar.',
    'STR_ST_sigkick2_DESC': 'Inflige [%e2.SkillATK_Instant.MinDamage]–[%e2.SkillATK_Instant.MaxDamage] de dano físico ao alvo e prende-o no Aprisionamento do Éter.\nReduz em 500 a defesa física de alvos com imunidade ao Aprisionamento do Éter por 40 s.\nHabilidade em Cadeia Nível 2\nGolpe do Mestre Divino – Chute de Ascensão',
    'STR_IDFist_ST_sigkick2_G1_DESC': 'Causa [%e1.NoReduceSpellATK_Instant.dano] de dano a um alvo e o coloca no Aprisionamento do Éter.\nHabilidade em Cadeia Nível 2\nGolpe do Mestre Divino – Chute de Ascensão',
    'STR_ST_upperhit_G1_DESC': 'Causa [%e1.SkillATK_Instant.MinDamage] a [%e1.SkillATK_Instant.MaxDamage] de dano físico a um alvo e prende-o no Aprisionamento do Éter por 2 segundos.\nRedefine a recarga de Golpe de Machado, Esquiva Rápida e Fuga Rápida.\nHabilidade de Estigma',
    'STR_SKILL_CH_PhoenixStep_new_G1_DESC': 'Remove todos os seus estados de Atordoamento, Derrubada, Tropeço, Giro e Aprisionamento do Éter. Aumenta [%e2.StatUp.StatName] em [%e2.StatUp.Value] por [%e2.StatUp.RemainTime].\nHabilidade em Cadeia Nível 1',
    'STR_SKILL_ALL_ShockReflect_G2_DESC': 'Remove todos os seus estados de Atordoamento, Empurrão, Tropeço, Giro, Aprisionamento do Éter e Paralisia. Aumenta [%e2.StatUp.StatName] e [%e2.StatUp.StatName2] por [%e2.StatUp.Value] por [%e2.StatUp.RemainTime].\nHabilidade em Cadeia Nível 1',
    'STR_AS_Re_RunnersStance_G1_Abnormal': 'Sua resistência a Atordoamento, Empurrão, Tropeço, Giro e Aprisionamento do Éter é aumentada.',
    'STR_Re_AS_Re_RunnersStance_G1_Abnormal': 'Sua resistência a Atordoamento, Empurrão, Tropeço, Giro e Aprisionamento do Éter é aumentada.',
    'STR_SKILL_RA_BreezeofCalm_G1_DESC': 'Aumenta a resistência a Atordoamento, Empurrão, Tropeço, Giro e Aprisionamento do Éter em 250 para você e aliados a até 10m por 10 segundos.\nHabilidade de Estigma',
    'STR_IDLDF1_TH_ElectricBind_G1_DESC': 'Causa dano mágico a um alvo a até 20m e prende-o no Aprisionamento do Éter por 10 segundos.',
    'STR_IDLDF1_TH_ElectricDrop_G1_DESC': 'Causa dano mágico a um alvo a até 20m preso no Aprisionamento do Éter e o derruba no chão.',
    'STR_SKILL_SC_SpiritofGale_AD_G1_DESC': 'Aumenta sua velocidade de movimento em 5%% e, a cada vez que [%e1.Provoker.Condition] for aplicado, reduz temporariamente a recarga de Evasão Focada e Determinação da Natureza em 3 segundos.\nHabilidade Passiva',
    'STR_SKILL_SC_SpiritofGale_AD_G1_Abnormal': 'Aumenta a velocidade de movimento em 5%%. Adicionalmente, este estado reduz temporariamente a recarga de Evasão Focada e Determinação da Natureza em 3 segundos para cada golpe recebido.',
    'STR_SKILL_Gu_MindReading_AD_G1_Desc': 'Por [%e1.StatUp.RemainTime], seu [%e1.StatUp.StatName2] é aumentado em [%e1.StatUp.Value2] (adicionalmente [%e2.StatUp.StatName] por [%e2.StatUp.Value]), e [%e1.StatUp.StatName3] e [%e1.StatUp.StatName4] são aumentados em [%e1.StatUp.Value4]%%; o dano recebido é reduzido e atacar reduz a hostilidade do inimigo.',
    'STR_SKILL_KN_GrandProtection_G1_DESC': 'Por [%e1.proteger.RemainTime], você absorve [%e1.proteger.Value]%% do dano de um aliado a até [%e1.proteger.Range]m, sempre que ele sofrer [%e1.proteger.Condition]. Enquanto isso, o [%e2.StatUp.StatName] do aliado é aumentado em [%e2.StatUp.Value_type2]%%.\nHabilidade de Estigma',
    'STR_SKILL_KN_GrandProtection_G2_DESC': 'Por [%e1.proteger.RemainTime], você absorve [%e1.proteger.Value]%% do dano de um aliado a até [%e1.proteger.Range]m, sempre que ele sofrer [%e1.proteger.Condition]. Enquanto isso, o [%e2.StatUp.StatName] do aliado é aumentado em [%e2.StatUp.Value_type2]%%.\nHabilidade de Estigma',
    'STR_SKILL_KN_GrandProtection_G3_DESC': 'Por [%e1.proteger.RemainTime], você absorve [%e1.proteger.Value]%% do dano de um aliado a até [%e1.proteger.Range]m, sempre que ele sofrer [%e1.proteger.Condition]. Enquanto isso, o [%e2.StatUp.StatName] do aliado é aumentado em [%e2.StatUp.Value_type2]%%.\nHabilidade de Estigma',
    'STR_SKILL_KN_AvengingBash_DESC': 'Você golpeia o alvo com seu escudo, causando [%e1.SkillATK_Instant.MinDamage]–[%e1.SkillATK_Instant.MaxDamage] de dano físico, aumentando a hostilidade do inimigo atingido e causando um dano físico adicional de [%e1.SkillATK_Instant.AddDamage] ao alvo se ele for um Balaur.\nCausa dano adicional quando o alvo for um PNJ.\nRequer um escudo.\nHabilidade de Combo Nível 1',
    'STR_ALL_GlideATK_PR_DESC': 'Avança contra um alvo a até [%First_Target_Valid_Distance]m e restaura uma certa quantia de HP de um membro do grupo. Por 10 s, sempre que você receber dano, gera um escudo que absorve o dano.',
    'STR_WORLD_SKILL_Dark_Avatar_G1_L_Abnormal': 'Você se transformou em um General Divino. Aumenta [%e3.StatUp.StatName2] em [%e3.StatUp.Value2], [%e3.StatUp.StatName3] em [%e3.StatUp.Value3], [%e3.StatUp.StatName4] em [%e3.StatUp.Value4], e [%e4.StatUp.StatName] em [%e4.StatUp.Value]. Também aumenta a sua velocidade de movimento e voo. Você resiste a quase todos os estados anormais e inflige dano adicional ao atacar jogadores adversários.',
}

# Adicionar Transformação: General Divino I a V
for rank in range(1, 6):
    rn = ['I', 'II', 'III', 'IV', 'V'][rank-1]
    EXACT_SKILL_REPLACEMENTS[f'STR_SKILL_Abyss_RankerSkill_Light_Avatar_G{rank}'] = f'Transformação: General Divino {rn}'
    EXACT_SKILL_REPLACEMENTS[f'STR_SKILL_Abyss_RankerSkill_Dark_Avatar_G{rank}'] = f'Transformação: General Divino {rn}'
    EXACT_SKILL_REPLACEMENTS[f'STR_SKILL_Light_Avatar_G{rank}_L'] = f'Transformação: General Divino {rn}'
    EXACT_SKILL_REPLACEMENTS[f'STR_SKILL_Dark_Avatar_G{rank}_L'] = f'Transformação: General Divino {rn}'

# Regex contextuais em habilidades
SKILL_REGEX_RULES = [
    (r'\bidéia Divino\b', 'General Divino'),
    (r'\bidéia guardião\b', 'General Guardião'),
    (r'\bdivindade idéia\b', 'General Divino'),
    (r'\[\s*idéia\s*\]', '[General]'),
    (r'\bno Éter[’\']s Manter\b', 'no Aprisionamento do Éter'),
    (r'\bao Éter[’\']s Manter\b', 'ao Aprisionamento do Éter'),
    (r'\bem Éter[’\']s Manter\b', 'no Aprisionamento do Éter'),
    (r'\be Éter[’\']s Manter\b', 'e Aprisionamento do Éter'),
    (r'\bÉter[’\']s Manter,\b', 'Aprisionamento do Éter,'),
    (r'\bÉter[’\']s Manter\b', 'Aprisionamento do Éter'),
]

# Dicionário de substituições em client_strings_item2.xml
EXACT_ITEM2_REPLACEMENTS = {
    'STR_Item_IDDokkaebi_HandMirror': 'Espelho Brilhante',
}


def read_xml_file(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    while data.startswith(b'\xff\xfe'):
        data = data[2:]
    return data.decode('utf-16le', errors='ignore')


def write_xml_file(filepath, content):
    data = content.encode('utf-16le')
    with open(filepath, 'wb') as f:
        f.write(b'\xff\xfe' + data)


def validate_xml_string(xml_str):
    clean = xml_str.strip()
    if clean.startswith('<?xml'):
        clean = clean[clean.find('?>')+2:].strip()
    return ET.fromstring(clean)


def apply_refinements(apply_changes=False):
    print("=" * 70)
    print("AUDITORIA E REFINAMENTO DE MAGIAS E HABILIDADES (PT-BR)")
    print("=" * 70)
    
    # 1. Processar client_strings_skill.xml
    skill_path = os.path.join(CLIENT_STRINGS_DIR, 'client_strings_skill.xml')
    skill_text = read_xml_file(skill_path)
    
    exact_modified = 0
    for key, rep in EXACT_SKILL_REPLACEMENTS.items():
        pat = rf'(<string>\s*<id>\d+</id>\s*<name>{re.escape(key)}</name>\s*<body>)([^<]*)(</body>\s*</string>)'
        m = re.search(pat, skill_text)
        if m:
            if m.group(2) != rep:
                skill_text = re.sub(pat, rf'\g<1>{rep}\g<3>', skill_text)
                exact_modified += 1
        else:
            print(f"[AVISO] Tag <name>{key}</name> não encontrada em client_strings_skill.xml!")
            
    regex_modified = 0
    for pat_str, rep in SKILL_REGEX_RULES:
        count = len(re.findall(pat_str, skill_text))
        if count > 0:
            skill_text = re.sub(pat_str, rep, skill_text)
            regex_modified += count
            
    print(f"[client_strings_skill.xml]: {exact_modified} strings exatas refinadas | {regex_modified} regex hits aplicados")
    
    # 2. Processar client_strings_item2.xml (para Mirror da skill 10776)
    item2_path = os.path.join(CLIENT_STRINGS_DIR, 'client_strings_item2.xml')
    item2_text = read_xml_file(item2_path)
    item2_modified = 0
    for key, rep in EXACT_ITEM2_REPLACEMENTS.items():
        pat = rf'(<string>\s*<id>\d+</id>\s*<name>{re.escape(key)}</name>\s*<body>)([^<]*)(</body>\s*</string>)'
        m = re.search(pat, item2_text)
        if m:
            if m.group(2) != rep:
                item2_text = re.sub(pat, rf'\g<1>{rep}\g<3>', item2_text)
                item2_modified += 1
                
    print(f"[client_strings_item2.xml]: {item2_modified} strings exatas refinadas")
    
    # 3. Validar se o XML gerado é perfeitamente válido
    try:
        root_sk = validate_xml_string(skill_text)
        print(f"[SUCESSO] client_strings_skill.xml é sintaticamente válido ({len(root_sk)} nós).")
    except Exception as e:
        print(f"[ERRO CRÍTICO] client_strings_skill.xml ficou inválido: {e}")
        return False
        
    try:
        root_it2 = validate_xml_string(item2_text)
        print(f"[SUCESSO] client_strings_item2.xml é sintaticamente válido ({len(root_it2)} nós).")
    except Exception as e:
        print(f"[ERRO CRÍTICO] client_strings_item2.xml ficou inválido: {e}")
        return False

    if apply_changes:
        print("\nGravando alterações nos arquivos de tradução...")
        write_xml_file(skill_path, skill_text)
        write_xml_file(item2_path, item2_text)
        print("[CONCLUÍDO] Arquivos gravados com sucesso (UTF-16 LE com BOM).")
    else:
        print("\n[MODO SIMULAÇÃO] Nenhuma alteração foi gravada em disco. Use --aplicar para salvar.")
        
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Refinamento de Nomes e Descrições de Magias/Habilidades PT-BR")
    parser.add_argument('--aplicar', action='store_true', help="Grava as alterações em disco")
    args = parser.parse_args()
    
    apply_refinements(apply_changes=args.aplicar)
