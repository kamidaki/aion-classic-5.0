package quest.tiamaranta_mesa;

import static com.aionemu.gameserver.model.DialogAction.*;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.questEngine.handlers.AbstractQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.services.QuestService;

/**
 * Quest ID: 10541
 * Title: Trustworthy Comrades
 * Zone: Tiamaranta Mesa
 * 
 * @author Aion Classic 5.0 Parser Pipeline
 */
public class _10541TrustworthyComrades extends AbstractQuestHandler {

	public _10541TrustworthyComrades() {
		super(10541);
	}

	@Override
	public void register() {
		// 800360: Mine!
		qe.registerQuestNpc(800360).addOnTalkEvent(questId);
		// 800361: Mine!
		qe.registerQuestNpc(800361).addOnTalkEvent(questId);
		// 220625: Traitorous Reian Assassin
		qe.registerQuestNpc(220625).addOnKillEvent(questId);
		// 220626: Traitorous Reian Assassin
		qe.registerQuestNpc(220626).addOnKillEvent(questId);
		// 220628: Traitorous Reian Warrior
		qe.registerQuestNpc(220628).addOnKillEvent(questId);
		// 220629: Traitorous Reian Warrior
		qe.registerQuestNpc(220629).addOnKillEvent(questId);
		// 220630: Traitorous Reian Priest
		qe.registerQuestNpc(220630).addOnKillEvent(questId);
		// 220631: Traitorous Reian Priest
		qe.registerQuestNpc(220631).addOnKillEvent(questId);
		// 220632: Traitorous Reian Scout
		qe.registerQuestNpc(220632).addOnKillEvent(questId);
		// 220633: Traitorous Reian Scout
		qe.registerQuestNpc(220633).addOnKillEvent(questId);
		// 220634: Traitorous Reian Mage
		qe.registerQuestNpc(220634).addOnKillEvent(questId);
		// 220635: Traitorous Reian Mage
		qe.registerQuestNpc(220635).addOnKillEvent(questId);
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
		int[] mobs = { 220625, 220626, 220628, 220629, 220630, 220631, 220632, 220633, 220634, 220635 };
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
