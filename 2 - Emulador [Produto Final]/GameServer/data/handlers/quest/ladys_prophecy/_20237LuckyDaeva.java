package quest.ladys_prophecy;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20237 Lucky Daeva. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20237.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20237LuckyDaeva extends CampaignQuestHandler {

	public _20237LuckyDaeva() {
		super(20237, 20235);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 204075); // Balder (select1)
		rewardAtPage(2, 2, 204075); // Balder: select2 -> SELECT_QUEST_REWARD (var 2 depende da rolagem de dado, PENDENTE)
	}
}
