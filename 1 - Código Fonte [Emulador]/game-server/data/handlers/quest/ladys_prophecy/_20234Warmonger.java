package quest.ladys_prophecy;

import static com.aionemu.gameserver.model.DialogAction.*;

import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.questEngine.handlers.AbstractQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;

/**
 * Quest ID: 20234
 * Title: Warmonger
 * Zone: The Ladys Prophecy
 * 
 * Auto-generated with Classic 5.0 campaign engine standards.
 */
public class _20234Warmonger extends AbstractQuestHandler {

	private static final int START_NPC = 204075;
	private static final int END_NPC = 204075;

	public _20234Warmonger() {
		super(20234);
	}

	@Override
	public void register() {
		qe.registerOnLevelChanged(questId);
		qe.registerOnQuestCompleted(questId);
		qe.registerQuestNpc(START_NPC).addOnQuestStart(questId);
		qe.registerQuestNpc(START_NPC).addOnTalkEvent(questId);

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
	public void onLevelChangedEvent(Player player) {
		if (player.getRace() == Race.ASMODIANS) {
			defaultOnLevelChangedEvent(player, 20233);
		}
	}

	@Override
	public void onQuestCompletedEvent(QuestEnv env) {
		Player player = env.getPlayer();
		if (player.getRace() == Race.ASMODIANS) {
			defaultOnQuestCompletedEvent(env, 20233);
		}
	}
}
