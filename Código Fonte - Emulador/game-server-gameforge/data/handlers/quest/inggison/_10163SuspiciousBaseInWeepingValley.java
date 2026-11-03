package quest.inggison;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10163 Suspicious Base in Weeping Valley. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10163.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10163SuspiciousBaseInWeepingValley extends CampaignQuestHandler {

	public _10163SuspiciousBaseInWeepingValley() {
		super(10163, 10162);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 798983); // Croton
		talk(1, 2, 2, 730644); // Jeniah
		talk(2, 3, 3, 799076); // Shaorun (Shugo_LF4_6)
		kill(3, 7, 215599, 215600); // CSV Progress(3~!10) LF4_B_Salivado_53/54_An
		kill(10, 1, 217068); // INFERÊNCIA: a Rusalka nomeada abre o fluxo; o CSV não lista, mas o drop vale só na var 11
		check(11, 6, 12, 799076); // Shaorun confere o lingote (quest_monster drop@11); check_ok -> SELECT7
		talk(12, 7, REWARD, 799076); // Shaorun, select7 SET_SUCCEED
		reward(798975); // Sulla
	}
}
