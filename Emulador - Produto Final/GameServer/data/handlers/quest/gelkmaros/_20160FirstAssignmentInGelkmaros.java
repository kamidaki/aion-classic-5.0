package quest.gelkmaros;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20160 First Assignment in Gelkmaros. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20160.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20160FirstAssignmentInGelkmaros extends CampaignQuestHandler {

	public _20160FirstAssignmentInGelkmaros() {
		super(20160, 20156);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 799225); // Hler
		talk(1, 2, 2, 799200); // Nikola, curandeira de alma
		useObject(2, 3, 730238); // registrar o obelisco de Gelkmaros (evento do ResurrectAI)
		talk(3, 4, 4, 799364); // Merhen
		talk(4, 5, 5, 799365); // Gudinho
		talk(5, 6, 6, 799204); // Vincenzo
		talk(6, 7, 7, 799208); // Garath
		talk(7, 8, 8, 799405); // Homesiane
		talk(8, 9, 9, 799406); // Sherockian (select9)
		check(9, 10, 10, 799406); // erva e pedra (quest_monster drop@9)
		talk(10, 11, 11, 799406); // Sherockian (select11)
		kill(11, 1, 216555); // CSV Progress(11~!12) DF4_Condor_DR_NmdQ_52_An
		talk(12, 13, REWARD, 799406); // Sherockian, select13 SET_SUCCEED
		reward(799227); // Gelastra
	}
}
