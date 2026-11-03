package quest.ladys_prophecy;

import com.aionemu.gameserver.questEngine.handlers.CampaignQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.utils.stats.AbyssRankEnum;

/**
 * Campanha 10234 Warmonger. Tabela gerada por 6 - Ferramentas/parsersXML/gera_handlers_campanhas_50.py a partir de
 * dialogs/quest/quest_q10234.html e Quest/quest_script_monster.csv do cliente 5.0.
 */
public class _10234Warmonger extends CampaignQuestHandler {

	public _10234Warmonger() {
		super(10234, 10233);
	}

	@Override
	protected void defineSteps() {
		talk(0, 1, 1, 203752); // Jucleas (select1)
		rewardAtPage(2, 2, 203752); // Jucleas: select2 -> SELECT_QUEST_REWARD
	}

	@Override
	public void register() {
		super.register();
		qe.registerOnKillRanked(AbyssRankEnum.GRADE5_SOLDIER, questId); // "5급병 이상": patente soldado grau 5 ou maior
	}

	@Override
	public boolean onKillRankedEvent(QuestEnv env) {
		// ([%5]/1000): o contador não cabe numa var de 6 bits; vai nas vars 1 e 2 (12 bits)
		QuestState qs = env.getPlayer().getQuestStateList().getQuestState(questId);
		if (qs == null || qs.getStatus() != QuestStatus.START || qs.getQuestVarById(0) != 1)
			return false;
		int kills = (qs.getQuestVarById(1) | qs.getQuestVarById(2) << 6) + 1;
		if (kills >= 1000) {
			qs.setQuestVar(2);
		} else {
			qs.setQuestVarById(1, kills & 0x3F);
			qs.setQuestVarById(2, kills >> 6);
		}
		updateQuestStatus(env);
		return true;
	}
}
