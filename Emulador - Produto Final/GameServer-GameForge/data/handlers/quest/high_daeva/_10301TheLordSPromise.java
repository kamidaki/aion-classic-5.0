package quest.high_daeva;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10301 The Lord's Promise. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10301.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10301TheLordSPromise extends CampaignQuestHandler {

	public _10301TheLordSPromise() {
		super(10301);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 203700); // Fasimedes (select1)
		talk(1, 2, 2, 203752); // Jucleas (select2): a entrada na instância IDGods_Descent_Q fica PENDENTE
	}
}
