package quest.gelkmaros;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20165 Gelkmaros Geysers. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20165.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20165GelkmarosGeysers extends CampaignQuestHandler {

	public _20165GelkmarosGeysers() {
		super(20165, 20164);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 799226); // Barretta
		talk(1, 2, 2, 799256); // Carabel
		check(2, 3, 3, 799256); // ametista (quest_monster drop@2); check_ok -> SELECT4
		talk(3, 4, 4, 799256); // Carabel (select4)
		talk(4, 5, 5, 730646); // Ehtys
		talk(5, 6, 6, 730647); // Tuca
		kill(6, 5, 216412); // CSV Progress(6~!11) DF4_FGriffon_DR_52_An
		talk(11, 8, REWARD, 730646); // Ehtys, select8 SET_SUCCEED
		reward(799371); // Vetus
	}
}
