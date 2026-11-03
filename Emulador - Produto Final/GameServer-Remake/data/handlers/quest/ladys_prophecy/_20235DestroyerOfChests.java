package quest.ladys_prophecy;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20235 Destroyer of Chests. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20235.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20235DestroyerOfChests extends CampaignQuestHandler {

	public _20235DestroyerOfChests() {
		super(20235, 20233);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 204075); // Balder (select1)
		checkReward(1, 2, 5, 204075); // relíquias x5 dos baús de Teva (quest_monster drop@1): select2 CHECK; falha -> select5
	}
}
