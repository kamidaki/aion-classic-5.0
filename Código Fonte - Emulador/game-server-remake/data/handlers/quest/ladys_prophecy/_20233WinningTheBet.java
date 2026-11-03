package quest.ladys_prophecy;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20233 Winning the Bet. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20233.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20233WinningTheBet extends CampaignQuestHandler {

	public _20233WinningTheBet() {
		super(20233, 20232);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 204075); // Balder (select1); capturas: START var 1
		killSection(1, 1, 3, 2, 217837); // CSV SECTION_0==1; SECTION_1<3 IDArena_Solo_B1_Kirca_55An
		rewardAtPage(2, 2, 204075); // Balder: select2 -> SELECT_QUEST_REWARD
	}
}
