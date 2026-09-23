package quest.tiamaranta_mesa;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10540 The Path Is Clear. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10540.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10540ThePathIsClear extends CampaignQuestHandler {

	public _10540ThePathIsClear() {
		super(10540);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 798926); // Cainus
		talkGive(1, 2, 2, 182215355, 1, 798928); // Yulia entrega a recomendação (quest_10540a)
		enterWorld(2, 3, 800040000); // chegar a Tiamaranta Mesa (LF4_Combine_LDF4b_Teleport_01 ou outra rota)
		rewardAt(3, 205769); // Ancanus: só select_success
	}
}
