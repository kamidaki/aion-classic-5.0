package quest.tiamaranta_mesa;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20542 Location of the Blood Drana. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20542.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20542LocationOfTheBloodDrana extends CampaignQuestHandler {

	public _20542LocationOfTheBloodDrana() {
		super(20542, 20541);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 205778); // Udvi: captura, 1011..1013 e 10000 -> var 1
		talk(1, 2, 2, 205779); // Kusir: captura, 1352..1355 e 10001 -> var 2
		check(2, 3, 3, 205779); // rastreadores (quest_monster drop@2); captura: var 3; check_ok -> SELECT4
		talk(3, 4, 4, 205779); // Kusir: captura, var 4 três segundos depois
		sensory(4, REWARD, 206281); // captura: REWARD com var 4
		reward(205778); // Udvi
	}
}
