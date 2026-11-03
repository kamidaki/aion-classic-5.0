package quest.ladys_prophecy;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10236 Dramatic Victory. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10236.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10236DramaticVictory extends CampaignQuestHandler {

	public _10236DramaticVictory() {
		super(10236, 10234);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 203752); // Jucleas (select1)
		rewardAtPage(2, 2, 203752); // Jucleas: select2 -> SELECT_QUEST_REWARD (var 2 depende do evento do Dredgion, PENDENTE)
	}
}
