package quest.bare_truth;

import static com.aionemu.gameserver.model.DialogAction.*;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.questEngine.handlers.AbstractQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.services.QuestService;

/**
 * Quest ID: 1099
 * Title: An Important Choice
 * Zone: The Hidden Truth
 * 
 * @author Aion Classic 5.0 Parser Pipeline
 */
public class _1099AnImportantChoice extends AbstractQuestHandler {

	public _1099AnImportantChoice() {
		super(1099);
	}

	@Override
	public void register() {
		// 215396: Draconute Raider
		qe.registerQuestNpc(215396).addOnKillEvent(questId);
		// 215397: Draconute Legionary
		qe.registerQuestNpc(215397).addOnKillEvent(questId);
		// 215398: Draconute Archer
		qe.registerQuestNpc(215398).addOnKillEvent(questId);
		// 215399: Draconute Bloodbinder
		qe.registerQuestNpc(215399).addOnKillEvent(questId);
		// 215400: Gruesome Oris
		qe.registerQuestNpc(215400).addOnKillEvent(questId);
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
		int[] mobs = { 215396, 215397, 215398, 215399, 215400 };
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
