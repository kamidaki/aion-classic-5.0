#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Handlers das campanhas (category1=mission) do Classic 5.0 a partir dos dados oficiais do cliente.

Fontes, todas em `Ferramentas e Documentos/Client e Coletas/Client 5.0 - Dados Extraidos/data` (extraídas com
`Ferramentas e Documentos/Ferramentas Python e PowerShell/Ferramentas Python/aion_dialogo_quest.py`):
  - `dialogs/quest/quest_qNNNNN.html`: ordem das etapas (`quest_summary`), páginas `selectN` e ações finais;
  - `Quest/quest_script_monster.csv`: var das etapas de abate, área sensorial e uso de item em área;
  - `Quest/quest_monster.csv`: var em que cada drop de quest vale (já refletida no `collecting_step` do quest_data);
  - `npcs/client_npcs.xml`: nome de modelo -> ID (`STR_DIC_N_Cainus` -> `<name>Cainus</name>` -> 798926).

Regra (conferida contra todas as restrições `Progress()` do CSV e contra as capturas subida-1-60 e outros2):
a var 0 é o índice da etapa no resumo; abates `Progress(a~!b)` ocupam as vars a..b-1 e deslocam as seguintes;
as páginas `selectN` são atribuídas em ordem às etapas de diálogo. Cada linha abaixo diz de onde veio.

As tabelas ficam aqui (e não geradas às cegas) porque algumas etapas pedem leitura do texto: quem entrega item,
ramos (`SETPRO3`/`SETPRO7`), objeto com página. O que não tem evidência vem marcado como INFERÊNCIA.

Uso:
    python "Ferramentas e Documentos/Ferramentas Python e PowerShell/parsersXML/gera_handlers_campanhas_50.py"            grava nas duas árvores
    python "Ferramentas e Documentos/Ferramentas Python e PowerShell/parsersXML/gera_handlers_campanhas_50.py" --conferir  só confere templates/spawns
"""
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
ARVORES = [
    os.path.join(RAIZ, "Código Fonte - Emulador", "game-server", "data"),
    os.path.join(RAIZ, "Emulador - Produto Final", "GameServer", "data"),
]

# ---------------------------------------------------------------------------------------------------------------------
# Tabelas. Cada missão: pacote, classe, título, pré-requisito (finished_quest_cond1 do quest.xml), linhas de defineSteps e,
# se preciso, imports + corpo extra (overrides) da classe.
# ---------------------------------------------------------------------------------------------------------------------
CAMPANHAS = {}


def campanha(qid, pacote, classe, titulo, pre, etapas, extra="", imports=(), consts=""):
    CAMPANHAS[qid] = dict(pacote=pacote, classe=classe, titulo=titulo, pre=pre, etapas=etapas, extra=extra, imports=imports, consts=consts)


# ----------------------------------------------------------------------------------------------------- Inggison (Elyos)
campanha(10160, "inggison", "_10160FirstMissionInInggison", "First Mission in Inggison", [10156], """
talk(0, 1, 1, 798926); // Cainus (Outremus)
talk(1, 2, 2, 798900); // Matias, curandeiro de alma
useObject(2, 3, 730237); // registrar o obelisco da Fortaleza da Ilusão (evento do ResurrectAI)
talk(3, 4, 4, 799052); // Steropes
talk(4, 5, 5, 799053); // Ionians
talk(5, 6, 6, 798905); // Giovani
talk(6, 7, 7, 798909); // Daniele
talkGive(7, 8, 8, 182215561, 1, 798940); // Clodia entrega o frasco vazio (quest_10160a, select8_1_1)
itemUseArea(8, 9, 182215561, "LF4_ITEMUSEAREA_Q11006A_210050000"); // CSV Progress(8) itemUseArea
talk(9, 9, 10, 798950); // Veloso recebe a água (select9)
talk(10, 10, 11, 799070); // Tramis pede as lesmas (select10)
kill(11, 7, 215502, 215503); // CSV Progress(11~!18) LF4_A_Slime_Snail_51/52_An
talk(18, 13, REWARD, 798950); // Veloso, select13 SET_SUCCEED
reward(798927); // Versetti
""")

campanha(10161, "inggison", "_10161TheMissionOverTheWindstream", "The Mission over the Windstream", [10160], """
talk(0, 1, 1, 798927); // Versetti
talk(1, 2, 2, 798938); // Aglaus
talk(2, 3, 3, 799025); // Laokoon: SETPRO3 = fazer as correntes de vento...
branch(SETPRO7, 7); // ...ou SETPRO7 = pular direto para o obelisco (select3_1_1_1)
sensory(3, 4, 206168); // CSV Progress(3) LF4_SensoryArea_Q11076A
sensory(4, 5, 206169); // CSV Progress(4) LF4_SensoryArea_Q11076B
sensory(5, 6, 206170); // CSV Progress(5) LF4_SensoryArea_Q11076C
talk(6, 7, 7, 799084); // Harami
talk(7, 8, 8, 730225); // obelisco LF4_FOBJ_Q10020C (objeto com página select8)
talk(8, 9, 9, 798951); // Ambrosini
check(9, 10, REWARD, 798951); // Ambrosini confere o dínamo (quest_monster drop@9); check_ok -> SELECT_QUEST_REWARD
reward(798951); // Ambrosini
""", imports=["static com.aionemu.gameserver.model.DialogAction.SETPRO7"])

campanha(10162, "inggison", "_10162ScarCanyonAndThePetrificationSite", "Scar Canyon and the Petrification Site", [10161], """
talk(0, 1, 1, 798951); // Ambrosini
talk(1, 2, 2, 798981); // Philon
talk(2, 3, 3, 730226); // fragmento LF4_FOBJ_Q10023A (quest_use_npc, select3)
talk(3, 4, 4, 730227); // fragmento LF4_FOBJ_Q10023B (select4)
talk(4, 5, 5, 730228); // fragmento LF4_FOBJ_Q10023C (select5)
killSection(5, 1, 1, 6, 216489); // CSV SECTION_1<1; SECTION_0==5 LF4_B1_Rhinoce_NamedQ_54_n
killSection(5, 2, 1, 6, 216490); // CSV SECTION_2<1; SECTION_0==5 LF4_B1_Baku_NamedQ_54_n
killSection(5, 3, 1, 6, 216491); // CSV SECTION_3<1; SECTION_0==5 LF4_B1_Crestlich_NamedQ_54_n
talk(6, 7, REWARD, 798981); // Philon, select7 SET_SUCCEED
reward(798983); // Croton
""")

campanha(10163, "inggison", "_10163SuspiciousBaseInWeepingValley", "Suspicious Base in Weeping Valley", [10162], """
talk(0, 1, 1, 798983); // Croton
talk(1, 2, 2, 730644); // Jeniah
talk(2, 3, 3, 799076); // Shaorun (Shugo_LF4_6)
kill(3, 7, 215599, 215600); // CSV Progress(3~!10) LF4_B_Salivado_53/54_An
kill(10, 1, 217068); // INFERÊNCIA: a Rusalka nomeada abre o fluxo; o CSV não lista, mas o drop vale só na var 11
check(11, 6, 12, 799076); // Shaorun confere o lingote (quest_monster drop@11); check_ok -> SELECT7
talk(12, 7, REWARD, 799076); // Shaorun, select7 SET_SUCCEED
reward(798975); // Sulla
""")

campanha(10164, "inggison", "_10164ShulackRefugeesInInggison", "Shulack Refugees in Inggison", [10163], """
talk(0, 1, 1, 798975); // Sulla
talk(1, 2, 2, 798986); // Setsukiki (Shulack_LF4_2)
check(2, 3, 3, 798986); // conserva e doce (quest_monster drop@2); check_ok -> FINISH_DIALOG
talk(3, 4, 4, 798985); // irmão (Shulack_LF4_1)
talkGive(4, 5, 5, 182215567, 1, 798984); // shugo Shugo_LF4_5 entrega o elixir (quest_10164c, select5_1)
talk(5, 6, 6, 798985); // irmão recebe o elixir
talkGive(6, 7, 7, 182215568, 1, 798963); // Cinisca entrega o frasco de vaga-lumes (quest_10164d, select7_1)
talk(7, 8, 8, 798985); // irmão: usar o frasco perto da Setsukiki
itemUseArea(8, 9, 182215568, "LF4_ITEMUSEAREA_Q11118A_210050000"); // CSV Progress(8) itemUseArea
talk(9, 10, 10, 798986); // Setsukiki (select10)
talk(10, 11, REWARD, 798985); // irmão, select11 SET_SUCCEED
reward(798928); // Yulia
""")

campanha(10165, "inggison", "_10165TheObeliskOfInggison", "The Obelisk of Inggison", [10164], """
talk(0, 1, 1, 798928); // Yulia
talk(1, 2, 2, 798955); // Marica
useObject(2, 3, 700628); // instalar o obelisco em LF4_FOBJ_Q10020D
useObject(3, 4, 700629); // LF4_FOBJ_Q10020E
useObject(4, 5, 700630); // LF4_FOBJ_Q10020F
check(5, 6, 6, 798955); // peça roubada pelas lupyllini (quest_monster drop@5); check_ok -> SELECT7
talk(6, 7, REWARD, 798955); // Marica, select7 SET_SUCCEED
reward(799058); // Facundus
""")

campanha(10166, "inggison", "_10166SpecialMission", "Special Mission", [10165], """
talk(0, 1, 1, 799058); // Facundus
talk(1, 2, 2, 798996); // Iaetia
talkGive(2, 3, 3, 182215572, 1, 798997); // Rollia entrega o puçá (quest_10166a) e faz a larva surgir (onAdvance)
talkGive(3, 4, 4, 182215573, 1, 799081); // larva (select4): puçá com a larva (quest_10166b)
talk(4, 5, 5, 798997); // Rollia (select5)
itemUseAt(5, 6, 182215573, 210050000, 1096.5378f, 1129.3385f, 446f, 15f); // CSV Progress(5); zona Q11147A ausente -> marcador oficial
talk(6, 7, REWARD, 798997); // Rollia, select7 SET_SUCCEED
reward(798996); // Iaetia
""", extra="""
	@Override
	protected void onAdvance(QuestEnv env, int fromVar, int next) {
		// handler 4.8 da 11147 (a quest de origem): a Rollia faz a larva surgir na frente do jogador por 5 minutos
		if (fromVar == 2)
			spawnForFiveMinutesInFrontOf(799081, env.getPlayer(), 1);
		else if (fromVar == 3 && env.getVisibleObject() instanceof Npc larva && larva.getNpcId() == 799081)
			larva.getController().delete();
	}
""", imports=["com.aionemu.gameserver.model.gameobjects.Npc", "com.aionemu.gameserver.questEngine.model.QuestEnv"])

campanha(10167, "inggison", "_10167TheSpiritOfTheAngriefWastes", "The Spirit of the Angrief Wastes", [10166], """
talk(0, 1, 1, 798996); // Iaetia
talk(1, 2, 2, 799008); // Totus
check(2, 3, 3, 799008); // enxofre das crateras (quest_monster drop@2); check_ok -> SELECT4
talkGive(3, 4, 4, 182215578, 1, 799008); // Totus (select4) entrega a tocha (quest_10167e)
kill(4, 5, 215737, 216786, 215738, 216787); // CSV Progress(4~!9) LF4_C2_DrakanWorkerFi/Pr(_Farm)_55_An
useObjects(9, 5, 700601); // queimar LF4_FOBJ_Q10022A ([%17]/5); INFERÊNCIA: vars 9..13, o CSV não lista
talk(14, 7, REWARD, 799008); // Totus, select7 SET_SUCCEED
reward(799005); // Ingnie
""")

campanha(10168, "inggison", "_10168DramataChasers", "Dramata Chasers", [10167], """
talk(0, 1, 1, 799005); // Ingnie
talk(1, 2, 2, 799010); // Wivius
check(2, 3, 3, 730645); // Mia confere os pertences (quest_monster drop@2); check_ok -> SELECT4
talk(3, 4, 4, 730645); // Mia (select4)
kill(4, 1, 216619); // CSV Progress(4~!5) LF4_DayQ_DrakanPr_55_An; entrega o cristal (onAdvance)
itemUse(5, 6, 182215583); // usar o cristal de memória ([%17]/1)
talk(6, 7, REWARD, 799010); // Wivius, select7 SET_SUCCEED
reward(798941); // Pilomenes
""", extra="""
	@Override
	protected void onAdvance(QuestEnv env, int fromVar, int next) {
		// INFERÊNCIA: o resumo manda usar o cristal do cubo logo depois do abate; nenhuma fonte diz quem entrega o doc_quest_10168e
		if (fromVar == 4)
			giveQuestItem(env, 182215583, 1);
	}
""", imports=["com.aionemu.gameserver.questEngine.model.QuestEnv"])

campanha(10169, "inggison", "_10169InSearchOfTheBalaurTowerMonument", "In Search of the Balaur Tower Monument", [10168], """
talk(0, 1, 1, 798941); // Pilomenes
useObject(1, 2, 700745); // tabuleta A
useObject(2, 3, 700746); // tabuleta B
useObject(3, 4, 700747); // tabuleta C
useObject(4, 5, 700748); // tabuleta D
useObject(5, 6, 700749); // tabuleta E
check(6, 7, REWARD, 798941); // decálques + doc_quest_10169f (quest_monster drop@6); check_ok -> SET_SUCCEED
reward(798941); // Pilomenes
""")

campanha(10170, "inggison", "_10170DefeatInggisonSBalaur", "Defeat Inggison's Balaur", [10169], """
talkGive(0, 1, 1, 182215590, 1, 798941); // Pilomenes entrega o mapa (doc_quest_10170a)
itemUse(1, 2, 182215590); // conferir o mapa no cubo
talk(2, 3, 3, 799017); // Sulinia
check(3, 4, 4, 799017); // símbolos dos quatro pontos (quest_monster drop@3); check_ok -> SELECT5
talkGive(4, 5, 5, 182215595, 1, 799017); // Sulinia (select5) entrega o disfarce (quest_10170f)
sensory(5, 6, 701568); // CSV Progress(5) LF4_SensoryArea_Q10170a
itemUseAt(6, 7, 182215595, 210050000, 2143f, 2344f, 82.6875f, 15f); // CSV Progress(6); zona Q10170A ausente -> marcador oficial
talkGive(7, 8, 8, 182215596, 1, 216498); // carcereiro LF4_C5_DrakanAs_vil_NamedQ_55_Ae (select8) entrega o relatório (quest_10170g)
talk(8, 9, REWARD, 799017); // Sulinia, select9 SET_SUCCEED
reward(798926); // Cainus
""")

# --------------------------------------------------------------------------------------------------- Gelkmaros (Asmodian)
campanha(20160, "gelkmaros", "_20160FirstAssignmentInGelkmaros", "First Assignment in Gelkmaros", [20156], """
talk(0, 1, 1, 799225); // Hler
talk(1, 2, 2, 799200); // Nikola, curandeira de alma
useObject(2, 3, 730238); // registrar o obelisco de Gelkmaros (evento do ResurrectAI)
talk(3, 4, 4, 799364); // Merhen
talk(4, 5, 5, 799365); // Gudinho
talk(5, 6, 6, 799204); // Vincenzo
talk(6, 7, 7, 799208); // Garath
talk(7, 8, 8, 799405); // Homesiane
talk(8, 9, 9, 799406); // Sherockian (select9)
check(9, 10, 10, 799406); // erva e pedra (quest_monster drop@9)
talk(10, 11, 11, 799406); // Sherockian (select11)
kill(11, 1, 216555); // CSV Progress(11~!12) DF4_Condor_DR_NmdQ_52_An
talk(12, 13, REWARD, 799406); // Sherockian, select13 SET_SUCCEED
reward(799227); // Gelastra
""")

campanha(20161, "gelkmaros", "_20161TheStormInGelkmaros", "The Storm in Gelkmaros", [20160], """
talk(0, 1, 1, 799227); // Gelastra
talk(1, 2, 2, 799322); // Herka: SETPRO2 = correntes de vento...
branch(SETPRO7, 7); // ...ou SETPRO7 = pular para a Vesvola (select2)
talk(2, 3, 3, 799340); // Vedrfonir
sensory(3, 4, 206171); // CSV Progress(3) DF4_SensoryArea_Q21080A
sensory(4, 5, 206172); // CSV Progress(4) DF4_SensoryArea_Q21080B
sensory(5, 6, 206173); // CSV Progress(5) DF4_SensoryArea_Q21080C
talk(6, 7, 7, 799427); // Vafuth
talk(7, 8, 8, 799248); // Vesvola
check(8, 9, REWARD, 799248); // esporo (quest_monster drop@8); check_ok -> SET_SUCCEED
reward(799248); // Vesvola
""", imports=["static com.aionemu.gameserver.model.DialogAction.SETPRO7"])

campanha(20162, "gelkmaros", "_20162InSearchOfShulackFugitives", "In Search of Shulack Fugitives", [20161], """
talk(0, 1, 1, 799248); // Vesvola
talk(1, 2, 2, 799280); // Shulack_DF4_3
check(2, 3, 3, 799280); // seiva do Rotron (quest_monster drop@2); check_ok -> SELECT4
talk(3, 4, 4, 799280); // Shulack_DF4_3 (select4)
talk(4, 5, 5, 799366); // Shulack_DF4_6, achado na caixa DF4_FOBJ_Q21105 (ver onDialogEvent)
talk(5, 6, 6, 799280); // Shulack_DF4_3 (select6)
talk(6, 7, REWARD, 799276); // Shulack_DF4_4, select7 SET_SUCCEED
reward(799268); // Nysdvor
""", extra="""
	@Override
	public void register() {
		super.register();
		qe.registerQuestNpc(BOX).addOnTalkEvent(questId);
		qe.registerCanAct(questId, BOX);
	}

	@Override
	public boolean onDialogEvent(QuestEnv env) {
		// handler 4.8 da 21105 (a quest de origem): a caixa solta o shulack ou um monstro e volta depois
		if (env.getTargetId() == BOX && env.getDialogActionId() == USE_OBJECT) {
			QuestState qs = env.getPlayer().getQuestStateList().getQuestState(questId);
			if (qs == null || qs.getStatus() != QuestStatus.START || qs.getQuestVarById(0) != 4)
				return false;
			Npc box = (Npc) env.getVisibleObject();
			spawnForFiveMinutes(Rnd.nextBoolean() ? 799366 : 216086, box.getPosition());
			box.getController().deleteAndScheduleRespawn();
			return true;
		}
		return super.onDialogEvent(env);
	}
""", imports=["static com.aionemu.gameserver.model.DialogAction.USE_OBJECT", "com.aionemu.commons.utils.Rnd",
              "com.aionemu.gameserver.model.gameobjects.Npc", "com.aionemu.gameserver.questEngine.model.QuestEnv",
              "com.aionemu.gameserver.questEngine.model.QuestState", "com.aionemu.gameserver.questEngine.model.QuestStatus"])

campanha(20163, "gelkmaros", "_20163FarbinSResearch", "Farbin's Research", [20162], """
talk(0, 1, 1, 799268); // Nysdvor
talk(1, 2, 2, 799282); // Martinez
check(2, 3, 3, 799282); // amostras (quest_monster drop@2); check_ok -> SELECT4
talkGive(3, 4, 4, 182215607, 1, 799282); // Martinez (select4) entrega a pedra de invocação (quest_20163e)
useObject(4, 5, 700702); // destruir DF4_DranaSuctionDevice_B3_Q20022
itemUseArea(5, 6, 182215607, "DF4_ITEMUSEAREA_Q20022_220070000"); // CSV Progress(5) itemUseArea
talk(6, 7, REWARD, 799282); // Martinez, select7 SET_SUCCEED
reward(799226); // Barretta
""")

campanha(20164, "gelkmaros", "_20164WarRemnantsOfTheAntagorBattlefield", "War Remnants of the Antagor Battlefield", [20163], """
talk(0, 1, 1, 799226); // Barretta
talk(1, 2, 2, 799245); // Vyuin
check(2, 3, 3, 799245); // restos do Drakan (quest_monster drop@2); check_ok -> SELECT4
talkGive(3, 4, 4, 182215609, 1, 799245); // Vyuin (select4) entrega o item de uso (quest_20164b)
itemUseArea(4, 5, 182215609, "DF4_ITEMUSEAREA_Q20020_220070000"); // CSV Progress(4) itemUseArea
sensory(5, 6, 206128); // CSV Progress(5) DF4_SensoryArea_Q20020
kill(6, 1, 218987, 216545); // CSV Progress(6) DF4_Drakan_Runner01_Q_55_An ou DF4_DrakanFi_NmdQ_52_An
talk(7, 8, REWARD, 799245); // Vyuin, select8 SET_SUCCEED
reward(799226); // Barretta
""")

campanha(20165, "gelkmaros", "_20165GelkmarosGeysers", "Gelkmaros Geysers", [20164], """
talk(0, 1, 1, 799226); // Barretta
talk(1, 2, 2, 799256); // Carabel
check(2, 3, 3, 799256); // ametista (quest_monster drop@2); check_ok -> SELECT4
talk(3, 4, 4, 799256); // Carabel (select4)
talk(4, 5, 5, 730646); // Ehtys
talk(5, 6, 6, 730647); // Tuca
kill(6, 5, 216412); // CSV Progress(6~!11) DF4_FGriffon_DR_52_An
talk(11, 8, REWARD, 730646); // Ehtys, select8 SET_SUCCEED
reward(799371); // Vetus
""")

campanha(20166, "gelkmaros", "_20166WanderingReianSouls", "Wandering Reian Souls", [20165], """
talk(0, 1, 1, 799371); // Vetus
talk(1, 2, 2, 799289); // Mamalia
talk(2, 3, 3, 799292); // Belik
talk(3, 4, 4, 799293); // Stephano
check(4, 5, 5, 799293); // lembrança (quest_monster drop@4); check_ok -> SELECT6
talk(5, 6, 6, 799293); // Stephano (select6)
talk(6, 7, REWARD, 799292); // Belik, select7 SET_SUCCEED
reward(799289); // Mamalia
""")

campanha(20167, "gelkmaros", "_20167InjuredBalaurResearcher", "Injured Balaur Researcher", [20166], """
talk(0, 1, 1, 799289); // Mamalia
talk(1, 2, 2, 799317); // Tanar
talk(2, 3, 3, 799341); // Anilmo
kill(3, 5, 215982); // CSV Progress(3~!8) DF4_Elementalair4_55_An
talk(8, 5, 9, 799341); // Anilmo (select5)
check(9, 6, 10, 799317); // dínamo do sugador (quest_monster drop@9); check_ok -> SELECT7
talk(10, 7, REWARD, 799317); // Tanar, select7 SET_SUCCEED
reward(799328); // Hrimfaxi
""")

campanha(20168, "gelkmaros", "_20168GelkmarosPetralith", "Gelkmaros Petralith", [20167], """
talk(0, 1, 1, 799328); // Hrimfaxi
talk(1, 2, 2, 799320); // Helen
kill(2, 7, 216021); // CSV Progress(2~!9) DF4_Nepilim_55_An; entrega a sucata (onAdvance)
itemUse(9, 10, 182215614); // usar a sucata enferrujada ([%11]/1)
sensory(10, 11, 701566); // CSV Progress(10) DF4_SensoryArea_Q20168a
check(11, 6, 12, 799318); // fragmentos do gigante (quest_monster drop@11); check_ok -> SELECT7
talk(12, 7, REWARD, 799318); // Batalrion, select7 SET_SUCCEED
reward(799320); // Helen
""", extra="""
	@Override
	protected void onAdvance(QuestEnv env, int fromVar, int next) {
		// INFERÊNCIA: o resumo manda usar a sucata do cubo logo depois dos abates; nenhuma fonte diz quem entrega o quest_20168a
		if (fromVar == 2)
			giveQuestItem(env, 182215614, 1);
	}
""", imports=["com.aionemu.gameserver.questEngine.model.QuestEnv"])

campanha(20169, "gelkmaros", "_20169TheSecretOfTheNadukaBiolab", "The Secret of the Naduka Biolab", [20168], """
talk(0, 1, 1, 799320); // Helen
talk(1, 2, 2, 799417); // Javis
talk(2, 3, 3, 799416); // Tonistar
check(3, 4, 4, 799416); // arma e armadura (quest_monster drop@3); check_ok -> SELECT5
talk(4, 5, 5, 799416); // Tonistar (select5)
talk(5, 6, 6, 799529); // Tonistar disfarçado no Biolab de Naduka
talk(6, 7, REWARD, 799417); // Javis, select7 SET_SUCCEED
reward(799308); // Ankea
""")

campanha(20170, "gelkmaros", "_20170PoisonToPoison", "Poison to Poison", [20169], """
talk(0, 1, 1, 799308); // Ankea
talk(1, 2, 2, 799298); // Geeze
check(2, 3, 3, 799298); // glândula (quest_monster drop@2); check_ok -> SELECT4
talkGive(3, 4, 4, 182215619, 1, 799298); // Geeze (select4) entrega o sachê de néctar de newt (quest_20170b)
itemUseArea(4, 5, 182215619, "DF4_ITEMUSEAREA_Q20024_220070000"); // CSV Progress(4) itemUseArea
useObject(5, 6, 700707); // destruir DF4_Facilities_Q20024
talk(6, 7, 7, 799298); // Geeze (select7)
talk(7, 8, REWARD, 799226); // Barretta, select8 SET_SUCCEED
reward(799225); // Hler
""")


# ------------------------------------------------------------------------------------- Cloister / Convent (nível 5)
campanha(10155, "cloister_of_kaisinel", "_10155LavirintosSCall", "Lavirintos's Call", [], """
talk(0, 1, 1, 203701); // Lavirintos
talk(1, 2, REWARD, 203795); // Demodocos (STR_DIC_LA204), estátua de teletransporte; select2 SET_SUCCEED
reward(798600); // Eremitia, no Cloister of Kaisinel
""")

campanha(10156, "cloister_of_kaisinel", "_10156BoundForInggison", "Bound for Inggison", [10155], """
talk(0, 1, 1, 798600); // Eremitia
talk(1, 2, 2, 798513); // Calimachos
talk(2, 3, 3, 203760); // Bellia
talkGive(3, 4, 4, 182215556, 1, 203782); // Bacchus entrega a pedra de onda de éter (quest_10156a, select4)
talk(4, 5, 5, 798408); // Sibylle
talkGive(5, 6, 6, 182215557, 1, 203709); // Clymene entrega a chave do navio (quest_10156b, select6_1)
talk(6, 7, 7, 798408); // Sibylle recebe a chave (select7)
talk(7, 8, REWARD, 798408); // Sibylle, select8 SET_SUCCEED: embarca para Inggison (onAdvance)
reward(798926); // Cainus, em Inggison
""", extra="""
	@Override
	protected void onAdvance(QuestEnv env, int fromVar, int next) {
		if (next == REWARD)
			toInggison(env);
	}

	@Override
	public boolean onDialogEvent(QuestEnv env) {
		// select8_1 (SETPRO10): quem voltou sem falar com o Cainus embarca de novo
		QuestState qs = env.getPlayer().getQuestStateList().getQuestState(questId);
		if (qs != null && qs.getStatus() == QuestStatus.REWARD && env.getTargetId() == SIBYLLE) {
			if (env.getDialogActionId() == QUEST_SELECT)
				return sendQuestDialog(env, 3399);
			if (env.getDialogActionId() == SETPRO10) {
				toInggison(env);
				return closeDialogWindow(env);
			}
		}
		return super.onDialogEvent(env);
	}

	private static void toInggison(QuestEnv env) {
		// destino do handler 4.8 da 10031 (sem captura 5.0 desta viagem)
		TeleportService.teleportTo(env.getPlayer(), 210050000, 1440, 408, 553, (byte) 77, TeleportAnimation.FADE_OUT_BEAM);
	}
""", imports=["static com.aionemu.gameserver.model.DialogAction.QUEST_SELECT", "static com.aionemu.gameserver.model.DialogAction.SETPRO10",
              "com.aionemu.gameserver.model.animations.TeleportAnimation", "com.aionemu.gameserver.questEngine.model.QuestEnv",
              "com.aionemu.gameserver.questEngine.model.QuestState", "com.aionemu.gameserver.questEngine.model.QuestStatus",
              "com.aionemu.gameserver.services.teleport.TeleportService"], consts="SIBYLLE = 798408")

campanha(20155, "convent_of_marchutan", "_20155VidarSCall", "Vidar's Call", [], """
talk(0, 1, 1, 204052); // Vidar
talk(1, 2, REWARD, 204092); // Gulinbursti, estátua de teletransporte; select2 SET_SUCCEED
reward(798800); // Agehia, no Convent of Marchutan
""")

campanha(20156, "convent_of_marchutan", "_20156TravelingToGelkmaros", "Traveling to Gelkmaros", [20155], """
talk(0, 1, 1, 798800); // Agehia
talk(1, 2, 2, 798409); // Tigrina
talk(2, 3, 3, 204202); // Nekai
talk(3, 4, 4, 204073); // Grer
talk(4, 5, 5, 204283); // Shugo_DC1_19
talk(5, 6, 6, 798409); // Tigrina, select6_1 SETPRO6: embarca para Gelkmaros (onAdvance)
rewardAt(6, 799225); // Hler, em Gelkmaros: só select_success
""", extra="""
	@Override
	protected void onAdvance(QuestEnv env, int fromVar, int next) {
		if (next == 6)
			toGelkmaros(env);
	}

	@Override
	public boolean onDialogEvent(QuestEnv env) {
		// select6_2 (SETPRO10): quem voltou sem falar com o Hler embarca de novo
		QuestState qs = env.getPlayer().getQuestStateList().getQuestState(questId);
		if (qs != null && qs.getStatus() == QuestStatus.START && qs.getQuestVarById(0) == 6 && env.getTargetId() == TIGRINA) {
			if (env.getDialogActionId() == QUEST_SELECT)
				return sendQuestDialog(env, 2718);
			if (env.getDialogActionId() == SETPRO10) {
				toGelkmaros(env);
				return closeDialogWindow(env);
			}
		}
		return super.onDialogEvent(env);
	}

	private static void toGelkmaros(QuestEnv env) {
		// destino do handler 4.8 da 20031 (sem captura 5.0 desta viagem)
		TeleportService.teleportTo(env.getPlayer(), 220070000, 1868, 2746, 531, (byte) 20, TeleportAnimation.FADE_OUT_BEAM);
	}
""", imports=["static com.aionemu.gameserver.model.DialogAction.QUEST_SELECT", "static com.aionemu.gameserver.model.DialogAction.SETPRO10",
              "com.aionemu.gameserver.model.animations.TeleportAnimation", "com.aionemu.gameserver.questEngine.model.QuestEnv",
              "com.aionemu.gameserver.questEngine.model.QuestState", "com.aionemu.gameserver.questEngine.model.QuestStatus",
              "com.aionemu.gameserver.services.teleport.TeleportService"], consts="TIGRINA = 798409")

# --------------------------------------------------------------------------------------------- Tiamaranta Mesa (60)
campanha(10540, "tiamaranta_mesa", "_10540ThePathIsClear", "The Path Is Clear", [], """
talk(0, 1, 1, 798926); // Cainus
talkGive(1, 2, 2, 182215355, 1, 798928); // Yulia entrega a recomendação (quest_10540a)
enterWorld(2, 3, 800040000); // chegar a Tiamaranta Mesa (LF4_Combine_LDF4b_Teleport_01 ou outra rota)
rewardAt(3, 205769); // Ancanus: só select_success
""")

campanha(10541, "tiamaranta_mesa", "_10541TrustworthyComrades", "Trustworthy Comrades", [10540], """
talk(0, 1, 1, 205769); // Ancanus
talk(1, 2, 2, 205765); // Celesia
talk(2, 3, 3, 205821); // Erasmus
talk(3, 4, 4, 802388); // Retinoa
talk(4, 5, 5, 205769); // Ancanus
talk(5, 6, 6, 802386); // Adela
killSection(6, 1, 10, 7, 220625, 220626, 220628, 220629, 220630, 220631, 220632, 220633, 220634, 220635); // CSV SECTION_0==6; SECTION_1<10
useObject(7, 8, 701475); // lápide A (barra de 12 s; mesma mecânica da C na captura outros2)
talk(8, 9, REWARD, 802386); // Adela, select9 SET_SUCCEED
reward(205769); // Ancanus
""")

campanha(10542, "tiamaranta_mesa", "_10542InSearchOfBloodDrana", "In Search of Blood Drana", [10541], """
talk(0, 1, 1, 205769); // Ancanus
talk(1, 2, 2, 205771); // Karuti
check(2, 3, 3, 205771); // rastreadores de drana negra (quest_monster drop@2); check_ok -> SELECT4
talk(3, 4, 4, 205771); // Karuti (select4)
sensory(4, REWARD, 206281); // LDF4b_SensoryArea_Q10542; captura da 20542: REWARD com var 4
reward(205769); // Ancanus
""")

campanha(20540, "tiamaranta_mesa", "_20540DestinationTiamaranta", "Destination Tiamaranta", [], """
talk(0, 1, 1, 799225); // Hler
talkGive(1, 2, 2, 182215361, 1, 799226); // Barretta entrega a recomendação (quest_20540a)
enterWorld(2, 3, 800040000); // chegar a Tiamaranta Mesa (DF4_Combine_LDF4b_Teleport_01 ou outra rota)
rewardAt(3, 205778); // Udvi: só select_success
""")

campanha(20541, "tiamaranta_mesa", "_20541ReliableComrades", "Reliable Comrades", [20540], """
talk(0, 1, 1, 205778); // Udvi
talk(1, 2, 2, 205774); // Motogut
talk(2, 3, 3, 205780); // Asraphis
talk(3, 4, 4, 802389); // Thiamin
talk(4, 5, 5, 205778); // Udvi
talk(5, 6, 6, 802387); // Adela
killSection(6, 1, 10, 7, 220684, 220685, 220690, 220691, 220695, 220696, 220697, 220698, 220699, 220700); // CSV SECTION_0==6; SECTION_1<10
useObject(7, 8, 701477); // lápide C: captura outros2, barra de 12000 ms e S_QUEST var 8
talk(8, 9, REWARD, 802387); // Adela: captura, 3739..3742 e 10255 -> st=4
reward(205778); // Udvi: captura, 10002 -> 1009 -> 5 -> 23 -> st=5 e 20542 LOCKED -> START
""")

campanha(20542, "tiamaranta_mesa", "_20542LocationOfTheBloodDrana", "Location of the Blood Drana", [20541], """
talk(0, 1, 1, 205778); // Udvi: captura, 1011..1013 e 10000 -> var 1
talk(1, 2, 2, 205779); // Kusir: captura, 1352..1355 e 10001 -> var 2
check(2, 3, 3, 205779); // rastreadores (quest_monster drop@2); captura: var 3; check_ok -> SELECT4
talk(3, 4, 4, 205779); // Kusir: captura, var 4 três segundos depois
sensory(4, REWARD, 206281); // captura: REWARD com var 4
reward(205778); // Udvi
""")

# -------------------------------------------------------------------------------------------------------- Teva (65)
campanha(10545, "teva", "_10545SetSailRunar", "Set Sail, Runar!", [], """
talk(0, 1, 1, 798926); // Cainus
talk(1, 2, 2, 803131); // Lunaring, em Tiamaranta
enterWorld(2, 3, 800060000); // chegar a Teva (LDF4b_to_Teva_Teleport_01)
rewardAt(3, 803133); // Lunaring em Teva: só select_success
""")

campanha(10546, "teva", "_10546TheMostPrecious", "The Most Precious", [10545], """
talkGive(0, 1, 1, 182215481, 1, 803133); // Lunaring entrega a Bússola do Tempo (quest_10546a)
sensory(1, 2, 206290); // CSV Progress(1) LDF4_Teva_SensoryArea_Q10546a
sensory(2, 3, 206291); // CSV Progress(2) ...Q10546b
sensory(3, 4, 206292); // CSV Progress(3) ...Q10546c
talk(4, 5, REWARD, 730637); // livro de Moros LDF4_Teva_FOBJ_Moros_Book_Q10546a, select5 SET_SUCCEED
reward(803133); // Lunaring
""")

campanha(20545, "teva", "_20545InPursuitLuna", "In Pursuit of Luna", [], """
talk(0, 1, 1, 799225); // Hler
talk(1, 2, 2, 803131); // Lunaring, em Tiamaranta
enterWorld(2, 3, 800060000); // chegar a Teva (LDF4b_to_Teva_Teleport_01)
rewardAt(3, 803133); // Lunaring em Teva: só select_success
""")

campanha(20546, "teva", "_20546WhatIsMostValuable", "What Is Most Valuable", [20545], """
talkGive(0, 1, 1, 182215482, 1, 803133); // Lunaring entrega a Bússola do Tempo (quest_20546a)
sensory(1, 2, 206290); // CSV Progress(1)
sensory(2, 3, 206291); // CSV Progress(2)
sensory(3, 4, 206292); // CSV Progress(3)
talk(4, 5, REWARD, 730637); // livro de Moros, select5 SET_SUCCEED
reward(803133); // Lunaring
""")


PVP_EXTRA = """
	@Override
	public void register() {
		super.register();
		qe.registerOnKillRanked(AbyssRankEnum.GRADE5_SOLDIER, questId); // "5급병 이상": patente soldado grau 5 ou maior
	}

	@Override
	public boolean onKillRankedEvent(QuestEnv env) {
		// ([%5]/1000): o contador não cabe numa var de 6 bits; vai nas vars 1 e 2 (12 bits)
		QuestState qs = env.getPlayer().getQuestStateList().getQuestState(questId);
		if (qs == null || qs.getStatus() != QuestStatus.START || qs.getQuestVarById(0) != 1)
			return false;
		int kills = (qs.getQuestVarById(1) | qs.getQuestVarById(2) << 6) + 1;
		if (kills >= 1000) {
			qs.setQuestVar(2);
		} else {
			qs.setQuestVarById(1, kills & 0x3F);
			qs.setQuestVarById(2, kills >> 6);
		}
		updateQuestStatus(env);
		return true;
	}
"""
PVP_IMPORTS = ["com.aionemu.gameserver.questEngine.model.QuestEnv", "com.aionemu.gameserver.questEngine.model.QuestState",
               "com.aionemu.gameserver.questEngine.model.QuestStatus", "com.aionemu.gameserver.utils.stats.AbyssRankEnum"]

# ------------------------------------------------------------------------------------------------ Tutorial (nível 1)
TUTORIAL_EXTRA = """
	@Override
	protected void onAdvance(QuestEnv env, int fromVar, int next) {
		if (fromVar == 0 && next == 1) { // subida-1-60, 1216.65 s: S_QUEST var 1 e S_REQ_TELEPORT no mesmo instante
			WorldMapInstance trial = InstanceService.getNextAvailableInstance(LAND_OF_SHADOWS, env.getPlayer());
			TeleportService.teleportTo(env.getPlayer(), trial, 730.58f, 513.26f, 338.25f, (byte) 60, TeleportAnimation.FADE_OUT_BEAM);
		}
	}

	@Override
	public boolean onDialogEvent(QuestEnv env) {
		QuestState qs = env.getPlayer().getQuestStateList().getQuestState(questId);
		if (qs != null && qs.getStatus() == QuestStatus.START) {
			int var = qs.getQuestVarById(0);
			int action = env.getDialogActionId();
			// select10: o guarda, depois do teste, só manda falar com o sumo sacerdote (SETPRO10 não muda a etapa)
			if (env.getTargetId() == GUARD && var >= 3) {
				if (action == QUEST_SELECT)
					return sendQuestDialog(env, 4080);
				if (action == SETPRO10)
					return closeDialogWindow(env);
			}
			// select8 só com estigma equipado; sem ele, select8_2 (FINISH_DIALOG)
			if (env.getTargetId() == STIGMA_MASTER && var == 7 && action == QUEST_SELECT
				&& env.getPlayer().getEquipment().getEquippedItemsAllStigma().isEmpty())
				return sendQuestDialog(env, 3400);
		}
		return super.onDialogEvent(env);
	}
"""
TUTORIAL_IMPORTS = ["static com.aionemu.gameserver.model.DialogAction.QUEST_SELECT", "static com.aionemu.gameserver.model.DialogAction.SETPRO10",
                    "static com.aionemu.gameserver.model.DialogAction.SETPRO6",
                    "com.aionemu.gameserver.model.animations.TeleportAnimation", "com.aionemu.gameserver.questEngine.model.QuestEnv",
                    "com.aionemu.gameserver.questEngine.model.QuestState", "com.aionemu.gameserver.questEngine.model.QuestStatus",
                    "com.aionemu.gameserver.services.instance.InstanceService", "com.aionemu.gameserver.services.teleport.TeleportService",
                    "com.aionemu.gameserver.world.WorldMapInstance"]

campanha(10153, "custom", "_10153MomentOfLightAndShadow", "Moment of Light and Shadow", [], """
talk(0, 1, 1, 730648); // guarda de Sanctum (LC1a_LGuard_GUIDE_01): select1 -> SETPRO1 e teletransporte (onAdvance)
enterWorld(1, 2, 390000000); // chegar à Land of Shadows (subida-1-60: var 2 no CM_LEVEL_READY da instância)
enterWorld(2, 3, 110010000); // voltar a Sanctum (subida-1-60: var 3 ao chegar na capital, pelo teletransporte do NPC da instância)
talk(3, 4, 4, 203752); // Jucleas (select4)
talk(4, 5, 5, 203701); // Lavirintos (STR_DIC_LA80): SETPRO5 = treino de idiomas...
branch(SETPRO6, 6); // ...ou SETPRO6 = pular a Fuchsia (select5_1_1_1)
talk(5, 6, 6, 203830); // Fuchsia (STR_DIC_LA205, modelo Vatonia)
talk(6, 7, 7, 203711); // Orphe, mestre de estigma (select7)
talk(7, 8, 8, 203711); // Orphe com estigma equipado (select8; sem estigma, select8_2 no onDialogEvent)
talk(8, 9, REWARD, 203701); // Lavirintos, select9 SET_SUCCEED
reward(203700); // Fasimedes
""", extra=TUTORIAL_EXTRA, imports=TUTORIAL_IMPORTS, consts="GUARD = 730648, STIGMA_MASTER = 203711, LAND_OF_SHADOWS = 390000000")

campanha(20153, "custom", "_20153TheMomentOfLightAndShadow", "The Moment of Light and Shadow", [], """
talk(0, 1, 1, 730649); // guarda de Pandaemonium (DC1a_DGuard_GUIDE_01): subida-1-60, 1011..1013 e 10000 -> var 1 + teletransporte
enterWorld(1, 2, 390000000); // subida-1-60, 1219.11 s: var 2 ao chegar à Land of Shadows
enterWorld(2, 3, 120010000); // subida-1-60, 2669.86 s: var 3 ao chegar a Pandaemonium (ação 104 da Inggril 804135)
talk(3, 4, 4, 204075); // Balder (select4)
talk(4, 5, 5, 204053); // Kvasir: SETPRO5 = ir ao Mimir...
branch(SETPRO6, 6); // ...ou SETPRO6 = pular o Mimir
talk(5, 6, 6, 204206); // Mimir
talk(6, 7, 7, 204061); // Aud, mestre de estigma (select7)
talk(7, 8, 8, 204061); // Aud com estigma equipado (select8; sem estigma, select8_2 no onDialogEvent)
talk(8, 9, REWARD, 204053); // Kvasir, select9 SET_SUCCEED
reward(204052); // Vidar
""", extra=TUTORIAL_EXTRA, imports=TUTORIAL_IMPORTS, consts="GUARD = 730649, STIGMA_MASTER = 204061, LAND_OF_SHADOWS = 390000000")

# ------------------------------------------------------------------------------------------ Lady's Prophecy (58-60)
PROFECIA_EXTRA = """
	@Override
	public boolean onDialogEvent(QuestEnv env) {
		// quest_refuse_1 e FINISH_DIALOG: recusar a profecia só fecha a conversa
		if (env.getDialogActionId() == QUEST_REFUSE_1)
			return closeDialogWindow(env);
		return super.onDialogEvent(env);
	}
"""

campanha(10232, "ladys_prophecy", "_10232JucleasSummons", "Jucleas' Summons", [], """
rewardAtPage(0, 1, 203752); // Jucleas: select1 -> select1_1 -> SELECT_QUEST_REWARD (ou QUEST_REFUSE_1)
""", extra=PROFECIA_EXTRA, imports=["static com.aionemu.gameserver.model.DialogAction.QUEST_REFUSE_1", "com.aionemu.gameserver.questEngine.model.QuestEnv"])

campanha(20232, "ladys_prophecy", "_20232BalderSSummons", "Balder's Summons", [], """
rewardAtPage(0, 1, 204075); // Balder: select1 -> select1_1 -> SELECT_QUEST_REWARD (ou QUEST_REFUSE_1); capturas: START var 0 no login
""", extra=PROFECIA_EXTRA, imports=["static com.aionemu.gameserver.model.DialogAction.QUEST_REFUSE_1", "com.aionemu.gameserver.questEngine.model.QuestEnv"])

campanha(10233, "ladys_prophecy", "_10233WinningTheBet", "Winning the Bet", [10232], """
talk(0, 1, 1, 203752); // Jucleas (select1)
killSection(1, 1, 3, 2, 217837); // CSV SECTION_0==1; SECTION_1<3 IDArena_Solo_B1_Kirca_55An
rewardAtPage(2, 2, 203752); // Jucleas: select2 -> SELECT_QUEST_REWARD
""")

campanha(20233, "ladys_prophecy", "_20233WinningTheBet", "Winning the Bet", [20232], """
talk(0, 1, 1, 204075); // Balder (select1); capturas: START var 1
killSection(1, 1, 3, 2, 217837); // CSV SECTION_0==1; SECTION_1<3 IDArena_Solo_B1_Kirca_55An
rewardAtPage(2, 2, 204075); // Balder: select2 -> SELECT_QUEST_REWARD
""")

campanha(10235, "ladys_prophecy", "_10235DestroyerOfChests", "Destroyer of Chests", [10233], """
talk(0, 1, 1, 203752); // Jucleas (select1)
checkReward(1, 2, 5, 203752); // relíquias x5 dos baús de Teva (quest_monster drop@1): select2 CHECK; falha -> select5
""")

campanha(20235, "ladys_prophecy", "_20235DestroyerOfChests", "Destroyer of Chests", [20233], """
talk(0, 1, 1, 204075); // Balder (select1)
checkReward(1, 2, 5, 204075); // relíquias x5 dos baús de Teva (quest_monster drop@1): select2 CHECK; falha -> select5
""")

campanha(10234, "ladys_prophecy", "_10234Warmonger", "Warmonger", [10233], """
talk(0, 1, 1, 203752); // Jucleas (select1)
rewardAtPage(2, 2, 203752); // Jucleas: select2 -> SELECT_QUEST_REWARD
""", extra=PVP_EXTRA, imports=PVP_IMPORTS)

campanha(20234, "ladys_prophecy", "_20234Warmonger", "Warmonger", [20233], """
talk(0, 1, 1, 204075); // Balder (select1)
rewardAtPage(2, 2, 204075); // Balder: select2 -> SELECT_QUEST_REWARD
""", extra=PVP_EXTRA, imports=PVP_IMPORTS)

# 10236/20236 (Dredgion ou Black Dranium, vitória por menos de 1000 pontos) e 10237/20237 (dado 100 em item raro, 7 vezes):
# o servidor não dispara evento de quest no fim do Dredgion (onDredgionReward não tem chamador) nem na rolagem de dado, e
# nenhuma captura mostra o pacote do placar. Só a conversa de início e a entrega estão aqui; a etapa do evento fica pendente.
campanha(10236, "ladys_prophecy", "_10236DramaticVictory", "Dramatic Victory", [10234], """
talk(0, 1, 1, 203752); // Jucleas (select1)
rewardAtPage(2, 2, 203752); // Jucleas: select2 -> SELECT_QUEST_REWARD (var 2 depende do evento do Dredgion, PENDENTE)
""")

campanha(20236, "ladys_prophecy", "_20236DramaticVictory", "Dramatic Victory", [20234], """
talk(0, 1, 1, 204075); // Balder (select1)
rewardAtPage(2, 2, 204075); // Balder: select2 -> SELECT_QUEST_REWARD (var 2 depende do evento do Dredgion, PENDENTE)
""")

campanha(10237, "ladys_prophecy", "_10237LuckyDaeva", "Lucky Daeva", [10235], """
talk(0, 1, 1, 203752); // Jucleas (select1)
rewardAtPage(2, 2, 203752); // Jucleas: select2 -> SELECT_QUEST_REWARD (var 2 depende da rolagem de dado, PENDENTE)
""")

campanha(20237, "ladys_prophecy", "_20237LuckyDaeva", "Lucky Daeva", [20235], """
talk(0, 1, 1, 204075); // Balder (select1)
rewardAtPage(2, 2, 204075); // Balder: select2 -> SELECT_QUEST_REWARD (var 2 depende da rolagem de dado, PENDENTE)
""")

# ---------------------------------------------------------------------------------------- Lords' Conversation (50)
# Etapas 2-8 acontecem em IDGods_Descent_Q (300620000 no WorldId.xml do cliente); no servidor o 300620000 é Occupied_Rentus_Base,
# herança 4.8, e a instância não existe. Só as conversas de Sanctum/Pandaemonium estão aqui; o resto fica PENDENTE.
campanha(10301, "high_daeva", "_10301TheLordSPromise", "The Lord's Promise", [], """
talk(0, 1, 1, 203700); // Fasimedes (select1)
talk(1, 2, 2, 203752); // Jucleas (select2): a entrada na instância IDGods_Descent_Q fica PENDENTE
""")

campanha(20301, "high_daeva", "_20301ThePromiseOfPower", "The Promise of Power", [], """
talk(0, 1, 1, 204052); // Vidar (select1)
talk(1, 2, 2, 204075); // Balder (select2): a entrada na instância IDGods_Descent_Q fica PENDENTE
""")


# ---------------------------------------------------------------------------------------------------------------------
def java(qid, c):
    imports = ["com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler"] + list(c["imports"])
    estaticos = sorted(i for i in imports if i.startswith("static "))
    normais = sorted(i for i in imports if not i.startswith("static "))
    linhas = [f"package quest.{c['pacote']};", ""]
    if estaticos:
        linhas += [f"import {i};" for i in estaticos] + [""]
    linhas += [f"import {i};" for i in normais] + [""]
    const = ""
    if "BOX" in c["extra"]:
        const = "\n\tprivate static final int BOX = 700812; // DF4_FOBJ_Q21105\n"
    if c["consts"]:
        const += "\n\tprivate static final int " + c["consts"] + ";\n"
    pre = "".join(f", {p}" for p in c["pre"])
    corpo = "\n".join("\t\t" + l for l in c["etapas"].strip().splitlines())
    linhas.append(f"""/**
 * Campanha {qid} {c['titulo']}. Tabela gerada por Ferramentas e Documentos/Ferramentas Python e PowerShell/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q{qid}.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class {c['classe']} extends CampaignQuestHandler {{
{const}
	public {c['classe']}() {{
		super({qid}{pre});
	}}

	@Override
	protected void defineSteps() {{
{corpo}
	}}
{c['extra']}}}
""")
    return "\n".join(linhas)


def ids_usados(c):
    txt = c["etapas"] + c["extra"]
    return sorted({int(x) for x in re.findall(r"\b(?:[2-8]\d{5})\b", txt) if not x.startswith("18")})


def confere():
    base = ARVORES[0]
    t = open(os.path.join(base, "static_data", "npcs", "npc_templates.xml"), encoding="utf-8").read()
    templates = set(int(x) for x in re.findall(r'<npc_template npc_id="(\d+)"', t))
    spawns = set()
    pasta = os.path.join(base, "static_data", "spawns")
    for raiz, _d, arqs in os.walk(pasta):
        for a in arqs:
            if a.endswith(".xml"):
                spawns.update(int(x) for x in re.findall(r'npc_id="(\d+)"', open(os.path.join(raiz, a), encoding="utf-8").read()))
    faltas = 0
    for qid, c in sorted(CAMPANHAS.items()):
        for i in ids_usados(c):
            if i >= 210000000:
                continue
            if i not in templates:
                print(f"  {qid}: NPC {i} sem template"); faltas += 1
            elif i not in spawns and i not in (799081, 799366, 216086):  # surgem por script
                print(f"  {qid}: NPC {i} sem spawn"); faltas += 1
    return faltas


def main(argv):
    faltas = confere()
    print(f"conferência: {faltas} pendências em {len(CAMPANHAS)} campanhas")
    if "--conferir" in argv:
        return 0
    for qid, c in sorted(CAMPANHAS.items()):
        codigo = java(qid, c)
        for arvore in ARVORES:
            pasta = os.path.join(arvore, "handlers", "quest", c["pacote"])
            os.makedirs(pasta, exist_ok=True)
            with open(os.path.join(pasta, c["classe"] + ".java"), "w", encoding="utf-8", newline="\n") as f:
                f.write(codigo)
        print(f"  {qid} -> quest/{c['pacote']}/{c['classe']}.java")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
