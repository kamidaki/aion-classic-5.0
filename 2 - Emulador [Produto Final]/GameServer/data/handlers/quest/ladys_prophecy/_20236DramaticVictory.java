package quest.ladys_prophecy;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20236 Dramatic Victory. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20236.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20236DramaticVictory extends CampaignQuestHandler {

	public _20236DramaticVictory() {
		super(20236, 20234);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 204075); // Balder (select1)
		rewardAtPage(2, 2, 204075); // Balder: select2 -> SELECT_QUEST_REWARD (var 2 depende do evento do Dredgion, PENDENTE)
	}
}
