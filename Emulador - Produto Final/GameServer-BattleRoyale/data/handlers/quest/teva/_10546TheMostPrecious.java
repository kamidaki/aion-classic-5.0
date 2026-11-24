package quest.teva;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 10546 The Most Precious. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10546.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10546TheMostPrecious extends CampaignQuestHandler {

	public _10546TheMostPrecious() {
		super(10546, 10545);
	}

	@Override
	protected void defineSteps() {
		talkGive(0, 1, 1, 182215481, 1, 803133); // Lunaring entrega a Bússola do Tempo (quest_10546a)
		sensory(1, 2, 206290); // CSV Progress(1) LDF4_Teva_SensoryArea_Q10546a
		sensory(2, 3, 206291); // CSV Progress(2) ...Q10546b
		sensory(3, 4, 206292); // CSV Progress(3) ...Q10546c
		talk(4, 5, REWARD, 730637); // livro de Moros LDF4_Teva_FOBJ_Moros_Book_Q10546a, select5 SET_SUCCEED
		reward(803133); // Lunaring
	}
}
