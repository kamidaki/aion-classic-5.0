package quest.teva;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;

/**
 * Campanha 20546 What Is Most Valuable. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20546.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20546WhatIsMostValuable extends CampaignQuestHandler {

	public _20546WhatIsMostValuable() {
		super(20546, 20545);
	}

	@Override
	protected void defineSteps() {
		talkGive(0, 1, 1, 182215482, 1, 803133); // Lunaring entrega a Bússola do Tempo (quest_20546a)
		sensory(1, 2, 206290); // CSV Progress(1)
		sensory(2, 3, 206291); // CSV Progress(2)
		sensory(3, 4, 206292); // CSV Progress(3)
		talk(4, 5, REWARD, 730637); // livro de Moros, select5 SET_SUCCEED
		reward(803133); // Lunaring
	}
}
