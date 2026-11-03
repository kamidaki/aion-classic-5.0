package quest.convent_of_marchutan;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20155 Vidar's Call. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20155.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20155VidarSCall extends CampaignQuestHandler {

	public _20155VidarSCall() {
		super(20155);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 204052); // Vidar
		talk(1, 2, REWARD, 204092); // Gulinbursti, estátua de teletransporte; select2 SET_SUCCEED
		reward(798800); // Agehia, no Convent of Marchutan
	}
}
