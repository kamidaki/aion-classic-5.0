package quest.ladys_prophecy;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10237 Lucky Daeva. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10237.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10237LuckyDaeva extends CampaignQuestHandler {

	public _10237LuckyDaeva() {
		super(10237, 10235);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 203752); // Jucleas (select1)
		rewardAtPage(2, 2, 203752); // Jucleas: select2 -> SELECT_QUEST_REWARD (var 2 depende da rolagem de dado, PENDENTE)
	}
}
