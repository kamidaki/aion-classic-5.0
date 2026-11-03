package quest.tiamaranta_mesa;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20540 Destination Tiamaranta. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20540.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20540DestinationTiamaranta extends CampaignQuestHandler {

	public _20540DestinationTiamaranta() {
		super(20540);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 799225); // Hler
		talkGive(1, 2, 2, 182215361, 1, 799226); // Barretta entrega a recomendação (quest_20540a)
		enterWorld(2, 3, 800040000); // chegar a Tiamaranta Mesa (DF4_Combine_LDF4b_Teleport_01 ou outra rota)
		rewardAt(3, 205778); // Udvi: só select_success
	}
}
