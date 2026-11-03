package quest.altgard;

import static com.aionemu.gameserver.model.DialogAction.*;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.questEngine.handlers.AbstractQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.services.QuestService;

/**
 * Quest ID: 2015
 * Title: Take the Initiative
 * Zone: Altgard
 * 
 * @author Aion Classic 5.0 Parser Pipeline
 */
public class _2015TakeTheInitiative extends AbstractQuestHandler {

	public _2015TakeTheInitiative() {
		super(2015);
	}

	@Override
	public void register() {
		// 210510: Comrade Sumarhon
		qe.registerQuestNpc(210510).addOnKillEvent(questId);
		// 210506: Grave Robbing Fencer
		qe.registerQuestNpc(210506).addOnKillEvent(questId);
		// 210507: Grave Robbing Fencer
		qe.registerQuestNpc(210507).addOnKillEvent(questId);
		// 210504: Grave Robbing Sentry
		qe.registerQuestNpc(210504).addOnKillEvent(questId);
		// 210505: Grave Robbing Sentry
		qe.registerQuestNpc(210505).addOnKillEvent(questId);
		qe.registerOnLevelChanged(questId);
		qe.registerOnEnterWorld(questId);
	}

	@Override
	public boolean onDialogEvent(QuestEnv env) {
		final Player player = env.getPlayer();
		final QuestState qs = player.getQuestStateList().getQuestState(questId);
		if (qs == null) {
			return false;
		}

		int targetId = env.getTargetId();
		int dialogActionId = env.getDialogActionId();

		if (qs.getStatus() == QuestStatus.START) {
			if (dialogActionId == QUEST_SELECT) {
				return sendQuestDialog(env, 1011);
			}
			if (dialogActionId == SET_SUCCEED) {
				qs.setStatus(QuestStatus.REWARD);
				updateQuestStatus(env);
				return closeDialogWindow(env);
			}
		} else if (qs.getStatus() == QuestStatus.REWARD) {
			if (dialogActionId == USE_OBJECT) {
				return sendQuestDialog(env, 10002);
			}
			return sendQuestEndDialog(env);
		}
		return false;
	}

	@Override
	public boolean onKillEvent(QuestEnv env) {
		int[] mobs = { 210510, 210506, 210507, 210504, 210505 };
		return defaultOnKillEvent(env, mobs, 0, 1);
	}

	@Override
	public boolean onEnterWorldEvent(QuestEnv env) {
		Player player = env.getPlayer();
		if (!player.getQuestStateList().hasQuest(questId)) {
			return QuestService.startQuest(env);
		}
		return false;
	}

	@Override
	public void onLevelChangedEvent(Player player) {
		defaultOnLevelChangedEvent(player);
	}
}
