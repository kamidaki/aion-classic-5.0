package quest.ladys_prophecy;

import static com.aionemu.gameserver.model.DialogAction.QUEST_REFUSE_1;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;

/**
 * Campanha 20232 Balder's Summons. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q20232.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _20232BalderSSummons extends CampaignQuestHandler {

	public _20232BalderSSummons() {
		super(20232);
	}

	@Override
	protected void defineSteps() {
		rewardAtPage(0, 1, 204075); // Balder: select1 -> select1_1 -> SELECT_QUEST_REWARD (ou QUEST_REFUSE_1); capturas: START var 0 no login
	}

	@Override
	public boolean onDialogEvent(QuestEnv env) {
		// quest_refuse_1 e FINISH_DIALOG: recusar a profecia só fecha a conversa
		if (env.getDialogActionId() == QUEST_REFUSE_1)
			return closeDialogWindow(env);
		return super.onDialogEvent(env);
	}
}
