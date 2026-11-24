package quest.inggison;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10162 Scar Canyon and the Petrification Site. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10162.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10162ScarCanyonAndThePetrificationSite extends CampaignQuestHandler {

	public _10162ScarCanyonAndThePetrificationSite() {
		super(10162, 10161);
	}

	@Override
	protected void defineSteps() {
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
	}
}
