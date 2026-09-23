package quest.ladys_prophecy;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10235 Destroyer of Chests. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10235.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10235DestroyerOfChests extends CampaignQuestHandler {

	public _10235DestroyerOfChests() {
		super(10235, 10233);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 203752); // Jucleas (select1)
		checkReward(1, 2, 5, 203752); // relíquias x5 dos baús de Teva (quest_monster drop@1): select2 CHECK; falha -> select5
	}
}
