package quest.gelkmaros;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20167 Injured Balaur Researcher. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20167.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20167InjuredBalaurResearcher extends CampaignQuestHandler {

	public _20167InjuredBalaurResearcher() {
		super(20167, 20166);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 799289); // Mamalia
		talk(1, 2, 2, 799317); // Tanar
		talk(2, 3, 3, 799341); // Anilmo
		kill(3, 5, 215982); // CSV Progress(3~!8) DF4_Elementalair4_55_An
		talk(8, 5, 9, 799341); // Anilmo (select5)
		check(9, 6, 10, 799317); // dínamo do sugador (quest_monster drop@9); check_ok -> SELECT7
		talk(10, 7, REWARD, 799317); // Tanar, select7 SET_SUCCEED
		reward(799328); // Hrimfaxi
	}
}
