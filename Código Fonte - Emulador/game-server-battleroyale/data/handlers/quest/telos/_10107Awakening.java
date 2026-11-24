package quest.telos;

import static com.aionemu.gameserver.model.DialogAction.*;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.questEngine.handlers.AbstractQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.services.QuestService;

/**
 * Quest ID: 10107
 * Title: Awakening
 * Zone: Telos
 * 
 * @author Aion Classic 5.0 Parser Pipeline
 */
public class _10107Awakening extends AbstractQuestHandler {

	public _10107Awakening() {
		super(10107);
	}

	@Override
	public void register() {
		// 800641: No. 573
		qe.registerQuestNpc(800641).addOnTalkEvent(questId);
		// 800649: No. 270
		qe.registerQuestNpc(800649).addOnTalkEvent(questId);
		// 219288: Brohum Cliff Warrior
		qe.registerQuestNpc(219288).addOnKillEvent(questId);
		// 219289: Brohum Cliff Warrior
		qe.registerQuestNpc(219289).addOnKillEvent(questId);
		// 219290: Brohum Cliff Warrior
		qe.registerQuestNpc(219290).addOnKillEvent(questId);
		// 219291: Brohum Cliff Warrior
		qe.registerQuestNpc(219291).addOnKillEvent(questId);
		// 219292: Brohum Cliff Warrior
		qe.registerQuestNpc(219292).addOnKillEvent(questId);
		// 219293: Brohum Cliff Soldier
		qe.registerQuestNpc(219293).addOnKillEvent(questId);
		// 219294: Brohum Cliff Soldier
		qe.registerQuestNpc(219294).addOnKillEvent(questId);
		// 219295: Brohum Cliff Soldier
		qe.registerQuestNpc(219295).addOnKillEvent(questId);
		// 219296: Brohum Cliff Soldier
		qe.registerQuestNpc(219296).addOnKillEvent(questId);
		// 219297: Brohum Cliff Soldier
		qe.registerQuestNpc(219297).addOnKillEvent(questId);
		// 219298: Brohum Cliff Fighter
		qe.registerQuestNpc(219298).addOnKillEvent(questId);
		// 219299: Brohum Cliff Fighter
		qe.registerQuestNpc(219299).addOnKillEvent(questId);
		// 219300: Brohum Cliff Fighter
		qe.registerQuestNpc(219300).addOnKillEvent(questId);
		// 219301: Brohum Cliff Fighter
		qe.registerQuestNpc(219301).addOnKillEvent(questId);
		// 219302: Brohum Cliff Fighter
		qe.registerQuestNpc(219302).addOnKillEvent(questId);
		// 219303: Brohum Cliff Scout
		qe.registerQuestNpc(219303).addOnKillEvent(questId);
		// 219304: Brohum Cliff Scout
		qe.registerQuestNpc(219304).addOnKillEvent(questId);
		// 219305: Brohum Cliff Scout
		qe.registerQuestNpc(219305).addOnKillEvent(questId);
		// 219306: Brohum Cliff Scout
		qe.registerQuestNpc(219306).addOnKillEvent(questId);
		// 219307: Brohum Cliff Scout
		qe.registerQuestNpc(219307).addOnKillEvent(questId);
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
		int[] mobs = { 219288, 219289, 219290, 219291, 219292, 219293, 219294, 219295, 219296, 219297, 219298, 219299, 219300, 219301, 219302, 219303, 219304, 219305, 219306, 219307 };
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
