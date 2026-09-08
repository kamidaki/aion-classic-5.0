package quest.tiamaranta_mesa;

import static com.aionemu.gameserver.model.DialogAction.*;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.questEngine.handlers.AbstractQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.services.QuestService;

/**
 * Quest ID: 20541
 * Title: Reliable Comrades
 * Zone: Tiamaranta Mesa
 * 
 * @author Aion Classic 5.0 Parser Pipeline
 */
public class _20541ReliableComrades extends AbstractQuestHandler {

	public _20541ReliableComrades() {
		super(20541);
	}

	@Override
	public void register() {
		// 800360: Mine!
		qe.registerQuestNpc(800360).addOnTalkEvent(questId);
		// 800361: Mine!
		qe.registerQuestNpc(800361).addOnTalkEvent(questId);
		// 220684: Avad Scout
		qe.registerQuestNpc(220684).addOnKillEvent(questId);
		// 220685: Avad Scout
		qe.registerQuestNpc(220685).addOnKillEvent(questId);
		// 220690: Avad Fighter
		qe.registerQuestNpc(220690).addOnKillEvent(questId);
		// 220691: Avad Fighter
		qe.registerQuestNpc(220691).addOnKillEvent(questId);
		// 220695: Avad Priest
		qe.registerQuestNpc(220695).addOnKillEvent(questId);
		// 220696: Avad Priest
		qe.registerQuestNpc(220696).addOnKillEvent(questId);
		// 220697: Avad Searcher
		qe.registerQuestNpc(220697).addOnKillEvent(questId);
		// 220698: Avad Searcher
		qe.registerQuestNpc(220698).addOnKillEvent(questId);
		// 220699: Avad Mage
		qe.registerQuestNpc(220699).addOnKillEvent(questId);
		// 220700: Avad Mage
		qe.registerQuestNpc(220700).addOnKillEvent(questId);
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
		int[] mobs = { 220684, 220685, 220690, 220691, 220695, 220696, 220697, 220698, 220699, 220700 };
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
