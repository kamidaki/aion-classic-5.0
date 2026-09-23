package quest.inggison;

import static com.aionemu.gameserver.model.DialogAction.*;

import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.questEngine.handlers.AbstractQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;

/**
 * Quest ID: 10161
 * Title: A missão além do Windstream
 * Zone: Inggison
 * 
 * Auto-generated with Classic 5.0 campaign engine standards.
 */
public class _10161TheMissionOverTheWindstream extends AbstractQuestHandler {

	private static final int START_NPC = 798927;
	private static final int END_NPC = 798927;
	private static final int[] MOBS = { 206168, 206169, 206170 };

	public _10161TheMissionOverTheWindstream() {
		super(10161);
	}

	@Override
	public void register() {
		qe.registerOnLevelChanged(questId);
		qe.registerOnQuestCompleted(questId);
		qe.registerQuestNpc(START_NPC).addOnQuestStart(questId);
		qe.registerQuestNpc(START_NPC).addOnTalkEvent(questId);
		for (int mob : MOBS) {
			qe.registerQuestNpc(mob).addOnKillEvent(questId);
		}
	}

	@Override
	public boolean onDialogEvent(QuestEnv env) {
		final Player player = env.getPlayer();
		if (player.getRace() != Race.ELYOS) {
			return false;
		}

		final QuestState qs = player.getQuestStateList().getQuestState(questId);
		int targetId = env.getTargetId();
		int dialogActionId = env.getDialogActionId();

		if (qs == null || qs.isStartable()) {
			if (targetId == START_NPC) {
				if (dialogActionId == QUEST_SELECT) {
					return sendQuestDialog(env, 1011);
				} else {
					return sendQuestStartDialog(env);
				}
			}
			return false;
		}

		if (qs.getStatus() == QuestStatus.START) {
			int var = qs.getQuestVarById(0);
			if (targetId == START_NPC) {
				switch (dialogActionId) {
					case QUEST_SELECT:
						return sendQuestDialog(env, 1011);
					case SETPRO1:
					case SETPRO2:
					case SET_SUCCEED:
						qs.setQuestVar(var + 1);
						updateQuestStatus(env);
						return closeDialogWindow(env);
				}
			} else if (targetId == END_NPC) {
				switch (dialogActionId) {
					case QUEST_SELECT:
						return sendQuestDialog(env, 2375);
					case SELECT_QUEST_REWARD:
						qs.setStatus(QuestStatus.REWARD);
						updateQuestStatus(env);
						return sendQuestEndDialog(env);
				}
			}
		} else if (qs.getStatus() == QuestStatus.REWARD) {
			if (targetId == END_NPC || targetId == START_NPC) {
				return sendQuestEndDialog(env);
			}
		}
		return false;
	}

	@Override
	public boolean onKillEvent(QuestEnv env) {
		return defaultOnKillEvent(env, MOBS, 0, 1);
	}

	@Override
	public void onLevelChangedEvent(Player player) {
		if (player.getRace() == Race.ELYOS) {
			defaultOnLevelChangedEvent(player, 10160);
		}
	}

	@Override
	public void onQuestCompletedEvent(QuestEnv env) {
		Player player = env.getPlayer();
		if (player.getRace() == Race.ELYOS) {
			defaultOnQuestCompletedEvent(env, 10160);
		}
	}
}
