package quest.gelkmaros;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;

/**
 * Campanha 20168 Gelkmaros Petralith. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20168.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20168GelkmarosPetralith extends CampaignQuestHandler {

	public _20168GelkmarosPetralith() {
		super(20168, 20167);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 799328); // Hrimfaxi
		talk(1, 2, 2, 799320); // Helen
		kill(2, 7, 216021); // CSV Progress(2~!9) DF4_Nepilim_55_An; entrega a sucata (onAdvance)
		itemUse(9, 10, 182215614); // usar a sucata enferrujada ([%11]/1)
		sensory(10, 11, 701566); // CSV Progress(10) DF4_SensoryArea_Q20168a
		check(11, 6, 12, 799318); // fragmentos do gigante (quest_monster drop@11); check_ok -> SELECT7
		talk(12, 7, REWARD, 799318); // Batalrion, select7 SET_SUCCEED
		reward(799320); // Helen
	}

	@Override
	protected void onAdvance(QuestEnv env, int fromVar, int next) {
		// INFERÊNCIA: o resumo manda usar a sucata do cubo logo depois dos abates; nenhuma fonte diz quem entrega o quest_20168a
		if (fromVar == 2)
			giveQuestItem(env, 182215614, 1);
	}
}
