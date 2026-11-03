package quest.ladys_prophecy;

import static com.aionemu.gameserver.model.DialogAction.QUEST_REFUSE_1;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;

/**
 * Campanha 10232 Jucleas' Summons. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10232.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10232JucleasSummons extends CampaignQuestHandler {

	public _10232JucleasSummons() {
		super(10232);
	}

	@Override
	protected void defineSteps() {
		rewardAtPage(0, 1, 203752); // Jucleas: select1 -> select1_1 -> SELECT_QUEST_REWARD (ou QUEST_REFUSE_1)
	}

	@Override
	public boolean onDialogEvent(QuestEnv env) {
		// quest_refuse_1 e FINISH_DIALOG: recusar a profecia só fecha a conversa
		if (env.getDialogActionId() == QUEST_REFUSE_1)
			return closeDialogWindow(env);
		return super.onDialogEvent(env);
	}
}
