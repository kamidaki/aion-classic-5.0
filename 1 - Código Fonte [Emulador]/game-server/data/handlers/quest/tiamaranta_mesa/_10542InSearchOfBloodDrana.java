package quest.tiamaranta_mesa;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10542 In Search of Blood Drana. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10542.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10542InSearchOfBloodDrana extends CampaignQuestHandler {

	public _10542InSearchOfBloodDrana() {
		super(10542, 10541);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 205769); // Ancanus
		talk(1, 2, 2, 205771); // Karuti
		check(2, 3, 3, 205771); // rastreadores de drana negra (quest_monster drop@2); check_ok -> SELECT4
		talk(3, 4, 4, 205771); // Karuti (select4)
		sensory(4, REWARD, 206281); // LDF4b_SensoryArea_Q10542; captura da 20542: REWARD com var 4
		reward(205769); // Ancanus
	}
}
