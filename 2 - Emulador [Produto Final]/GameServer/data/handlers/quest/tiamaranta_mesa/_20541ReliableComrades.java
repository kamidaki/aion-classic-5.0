package quest.tiamaranta_mesa;

import static com.aionemu.gameserver.model.DialogAction.*;

import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.questEngine.handlers.AbstractQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;

/**
 * Quest ID: 20541
 * Title: Reliable Comrades
 * Zone: Tiamaranta Mesa
 * 
 * Auto-generated with Classic 5.0 campaign engine standards.
 */
public class _20541ReliableComrades extends AbstractQuestHandler {

	private static final int START_NPC = 799226;
	private static final int END_NPC = 799226;
	private static final int[] MOBS = { 220684, 220685, 220690, 220691, 220695, 220696, 220697, 220698, 220699, 220700 };

	public _20541ReliableComrades() {
		super(20541);
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
		if (player.getRace() != Race.ASMODIANS) {
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
		if (player.getRace() == Race.ASMODIANS) {
			defaultOnLevelChangedEvent(player, 20540);
		}
	}

	@Override
	public void onQuestCompletedEvent(QuestEnv env) {
		Player player = env.getPlayer();
		if (player.getRace() == Race.ASMODIANS) {
			defaultOnQuestCompletedEvent(env, 20540);
		}
	}
}
