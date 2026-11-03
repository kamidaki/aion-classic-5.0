package quest.teva;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20545 In Pursuit of Luna. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20545.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20545InPursuitLuna extends CampaignQuestHandler {

	public _20545InPursuitLuna() {
		super(20545);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 799225); // Hler
		talk(1, 2, 2, 803131); // Lunaring, em Tiamaranta
		enterWorld(2, 3, 800060000); // chegar a Teva (LDF4b_to_Teva_Teleport_01)
		rewardAt(3, 803133); // Lunaring em Teva: só select_success
	}
}
