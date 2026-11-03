package quest.inggison;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10169 In Search of the Balaur Tower Monument. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10169.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10169InSearchOfTheBalaurTowerMonument extends CampaignQuestHandler {

	public _10169InSearchOfTheBalaurTowerMonument() {
		super(10169, 10168);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 798941); // Pilomenes
		useObject(1, 2, 700745); // tabuleta A
		useObject(2, 3, 700746); // tabuleta B
		useObject(3, 4, 700747); // tabuleta C
		useObject(4, 5, 700748); // tabuleta D
		useObject(5, 6, 700749); // tabuleta E
		check(6, 7, REWARD, 798941); // decálques + doc_quest_10169f (quest_monster drop@6); check_ok -> SET_SUCCEED
		reward(798941); // Pilomenes
	}
}
