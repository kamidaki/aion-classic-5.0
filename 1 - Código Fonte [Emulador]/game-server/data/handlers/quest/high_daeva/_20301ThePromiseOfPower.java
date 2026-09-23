package quest.high_daeva;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20301 The Promise of Power. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20301.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20301ThePromiseOfPower extends CampaignQuestHandler {

	public _20301ThePromiseOfPower() {
		super(20301);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 204052); // Vidar (select1)
		talk(1, 2, 2, 204075); // Balder (select2): a entrada na instância IDGods_Descent_Q fica PENDENTE
	}
}
