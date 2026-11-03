package quest.ascension;

import static com.aionemu.gameserver.model.DialogAction.*;

import com.aionemu.gameserver.model.PlayerClass;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.questEngine.handlers.AbstractQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.services.ClassChangeService;
import com.aionemu.gameserver.services.QuestService;

/**
 * Quest ID: 2010
 * Title: Ascend
 * Zone: Sub-Class Selection (Asmodians)
 */
public class _2010Ascend extends AbstractQuestHandler {

	public _2010Ascend() {
		super(2010);
	}

	@Override
	public void register() {
		qe.registerOnLevelChanged(questId);
		qe.registerOnEnterWorld(questId);
	}

	@Override
	public boolean onDialogEvent(QuestEnv env) {
		final Player player = env.getPlayer();
		if (player.getRace() != Race.ASMODIANS) {
			return false;
		}
		final QuestState qs = player.getQuestStateList().getQuestState(questId);
		if (qs == null) {
			return false;
		}

		int dialogActionId = env.getDialogActionId();

		if (qs.getStatus() == QuestStatus.START) {
			if (dialogActionId == QUEST_SELECT) {
				ClassChangeService.showClassChangeDialog(player);
				return true;
			}
		} else if (qs.getStatus() == QuestStatus.REWARD) {
			return sendQuestEndDialog(env);
		}
		return false;
	}

	@Override
	public boolean onEnterWorldEvent(QuestEnv env) {
		Player player = env.getPlayer();
		if (player.getRace() == Race.ASMODIANS && player.getPlayerClass().getStartingClass() == player.getPlayerClass()) {
			QuestState qs = player.getQuestStateList().getQuestState(questId);
			if (qs == null) {
				return QuestService.startQuest(env);
			}
		}
		return false;
	}

	@Override
	public void onLevelChangedEvent(Player player) {
		if (player.getRace() == Race.ASMODIANS && player.getPlayerClass().getStartingClass() == player.getPlayerClass()) {
			QuestState qs = player.getQuestStateList().getQuestState(questId);
			if (qs == null) {
				QuestService.addOrUpdateQuest(player, questId, QuestStatus.START);
			}
			if (player.getLevel() >= 5) {
				ClassChangeService.showClassChangeDialog(player);
			}
		}
	}
}
