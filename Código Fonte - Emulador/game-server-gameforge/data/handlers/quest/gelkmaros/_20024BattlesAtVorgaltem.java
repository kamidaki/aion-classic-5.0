package quest.gelkmaros;

import static com.aionemu.gameserver.model.DialogAction.*;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.questEngine.handlers.AbstractQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.services.QuestService;

/**
 * Quest ID: 20024
 * Title: Battles at Vorgaltem
 * Zone: Gelkmaros
 * 
 * @author Aion Classic 5.0 Parser Pipeline
 */
public class _20024BattlesAtVorgaltem extends AbstractQuestHandler {

	public _20024BattlesAtVorgaltem() {
		super(20024);
	}

	@Override
	public void register() {
		// 216033: Naduka Wardrake
		qe.registerQuestNpc(216033).addOnKillEvent(questId);
		// 216034: Naduka Wardrake
		qe.registerQuestNpc(216034).addOnKillEvent(questId);
		// 216101: Naduka Crusader
		qe.registerQuestNpc(216101).addOnKillEvent(questId);
		// 216107: Naduka Raider
		qe.registerQuestNpc(216107).addOnKillEvent(questId);
		// 216108: Naduka Stalker
		qe.registerQuestNpc(216108).addOnKillEvent(questId);
		// 216109: Naduka Stalker
		qe.registerQuestNpc(216109).addOnKillEvent(questId);
		// 216104: Naduka Battlemage
		qe.registerQuestNpc(216104).addOnKillEvent(questId);
		// 216112: Naduka Geomancer
		qe.registerQuestNpc(216112).addOnKillEvent(questId);
		// 216448: Naduka Crusader
		qe.registerQuestNpc(216448).addOnKillEvent(questId);
		// 216450: Naduka Raider
		qe.registerQuestNpc(216450).addOnKillEvent(questId);
		// 216451: Naduka Geomancer
		qe.registerQuestNpc(216451).addOnKillEvent(questId);
		// 216449: Naduka Battlemage
		qe.registerQuestNpc(216449).addOnKillEvent(questId);
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
		int[] mobs = { 216033, 216034, 216101, 216107, 216108, 216109, 216104, 216112, 216448, 216450, 216451, 216449 };
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
