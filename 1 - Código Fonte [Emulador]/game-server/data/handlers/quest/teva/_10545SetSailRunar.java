package quest.teva;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10545 Set Sail, Runar!. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10545.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10545SetSailRunar extends CampaignQuestHandler {

	public _10545SetSailRunar() {
		super(10545);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 798926); // Cainus
		talk(1, 2, 2, 803131); // Lunaring, em Tiamaranta
		enterWorld(2, 3, 800060000); // chegar a Teva (LDF4b_to_Teva_Teleport_01)
		rewardAt(3, 803133); // Lunaring em Teva: só select_success
	}
}
