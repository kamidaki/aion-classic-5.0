package quest.inggison;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10160 First Mission in Inggison. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10160.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10160FirstMissionInInggison extends CampaignQuestHandler {

	public _10160FirstMissionInInggison() {
		super(10160, 10156);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 798926); // Cainus (Outremus)
		talk(1, 2, 2, 798900); // Matias, curandeiro de alma
		useObject(2, 3, 730237); // registrar o obelisco da Fortaleza da Ilusão (evento do ResurrectAI)
		talk(3, 4, 4, 799052); // Steropes
		talk(4, 5, 5, 799053); // Ionians
		talk(5, 6, 6, 798905); // Giovani
		talk(6, 7, 7, 798909); // Daniele
		talkGive(7, 8, 8, 182215561, 1, 798940); // Clodia entrega o frasco vazio (quest_10160a, select8_1_1)
		itemUseArea(8, 9, 182215561, "LF4_ITEMUSEAREA_Q11006A_210050000"); // CSV Progress(8) itemUseArea
		talk(9, 9, 10, 798950); // Veloso recebe a água (select9)
		talk(10, 10, 11, 799070); // Tramis pede as lesmas (select10)
		kill(11, 7, 215502, 215503); // CSV Progress(11~!18) LF4_A_Slime_Snail_51/52_An
		talk(18, 13, REWARD, 798950); // Veloso, select13 SET_SUCCEED
		reward(798927); // Versetti
	}
}
