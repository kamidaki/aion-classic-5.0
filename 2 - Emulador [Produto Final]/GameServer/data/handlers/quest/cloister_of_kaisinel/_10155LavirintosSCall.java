package quest.cloister_of_kaisinel;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10155 Lavirintos's Call. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10155.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10155LavirintosSCall extends CampaignQuestHandler {

	public _10155LavirintosSCall() {
		super(10155);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 203701); // Lavirintos
		talk(1, 2, REWARD, 203795); // Demodocos (STR_DIC_LA204), estátua de teletransporte; select2 SET_SUCCEED
		reward(798600); // Eremitia, no Cloister of Kaisinel
	}
}
