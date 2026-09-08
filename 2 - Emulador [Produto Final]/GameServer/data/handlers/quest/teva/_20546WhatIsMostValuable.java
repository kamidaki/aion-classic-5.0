package quest.teva;

import static com.aionemu.gameserver.model.DialogAction.*;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.questEngine.handlers.AbstractQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.services.QuestService;

/**
 * Quest ID: 20546
 * Title: What Is Most Valuable?
 * Zone: Teva
 * 
 * @author Aion Classic 5.0 Parser Pipeline
 */
public class _20546WhatIsMostValuable extends AbstractQuestHandler {

	public _20546WhatIsMostValuable() {
		super(20546);
	}

	@Override
	public void register() {
		// 804718: NPC 804718
		qe.registerQuestNpc(804718).addOnTalkEvent(questId);
		// 804719: NPC 804719
		qe.registerQuestNpc(804719).addOnTalkEvent(questId);
		// 206290: Lake of Tears
		qe.registerQuestNpc(206290).addOnKillEvent(questId);
		// 206291: Karst of Desperation
		qe.registerQuestNpc(206291).addOnKillEvent(questId);
		// 206292: Craggy Heart
		qe.registerQuestNpc(206292).addOnKillEvent(questId);
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
		int[] mobs = { 206290, 206291, 206292 };
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
