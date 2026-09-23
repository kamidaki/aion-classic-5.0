package quest.custom;

import static com.aionemu.gameserver.model.DialogAction.*;

import com.aionemu.gameserver.model.ChatType;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.animations.TeleportAnimation;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.questEngine.handlers.AbstractQuestHandler;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.questEngine.model.QuestState;
import com.aionemu.gameserver.questEngine.model.QuestStatus;
import com.aionemu.gameserver.services.QuestService;
import com.aionemu.gameserver.services.instance.InstanceService;
import com.aionemu.gameserver.services.teleport.TeleportService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.world.WorldMapInstance;

/**
 * Quest ID: 20153
 * Title: The Moment of Light and Shadow
 * Zone: Land of Shadows (390000000 / IDTutorialQ)
 * 
 * Flow:
 * 1. Talk to High Priest Balder (204075) in Pandaemonium.
 * 2. Accept trial -> teleport to Land of Shadows (390000000).
 * 3. Azphel blessing granted upon entering Land of Shadows.
 * 4. Defeat invading Balaur creatures (224321..224328).
 * 5. Speak with Inggril, Daeva of Time (804135) to receive rewards and return to Pandaemonium.
 */
public class _20153TheMomentOfLightAndShadow extends AbstractQuestHandler {

	private static final int BALDER = 204075;
	private static final int INGGRIL = 804135;
	private static final int MAP_LAND_OF_SHADOWS = 390000000;
	private static final int MAP_PANDAEMONIUM = 120010000;

	private static final int[] MOBS = {
		224321, 224322, 224323, 224324, 224325, 224326, 224327, 224328
	};

	public _20153TheMomentOfLightAndShadow() {
		super(20153);
	}

	@Override
	public void register() {
		qe.registerOnLevelChanged(questId);
		qe.registerOnEnterWorld(questId);
		qe.registerQuestNpc(BALDER).addOnQuestStart(questId);
		qe.registerQuestNpc(BALDER).addOnTalkEvent(questId);
		qe.registerQuestNpc(INGGRIL).addOnTalkEvent(questId);
		for (int mob : MOBS) {
			qe.registerQuestNpc(mob).addOnKillEvent(questId);
		}
	}

	@Override
	public boolean onDialogEvent(QuestEnv env) {
		Player player = env.getPlayer();
		QuestState qs = player.getQuestStateList().getQuestState(questId);
		int dialogActionId = env.getDialogActionId();
		int targetId = env.getTargetId();

		if (qs == null || qs.isStartable()) {
			if (targetId == BALDER) {
				if (dialogActionId == QUEST_SELECT) {
					return sendQuestDialog(env, 1011);
				} else if (dialogActionId == ASK_QUEST_ACCEPT || dialogActionId == QUEST_ACCEPT_1) {
					QuestService.startQuest(env);
					qs = player.getQuestStateList().getQuestState(questId);
					if (qs != null) {
						qs.setQuestVar(1);
						updateQuestStatus(env);
						teleportToLandOfShadows(player);
						return closeDialogWindow(env);
					}
				} else {
					return sendQuestStartDialog(env);
				}
			}
		} else if (qs.getStatus() == QuestStatus.START) {
			int var = qs.getQuestVarById(0);
			if (targetId == BALDER) {
				switch (dialogActionId) {
					case QUEST_SELECT:
						return sendQuestDialog(env, 1011);
					case SETPRO1:
					case SET_SUCCEED:
						qs.setQuestVar(1);
						updateQuestStatus(env);
						teleportToLandOfShadows(player);
						return closeDialogWindow(env);
				}
			} else if (targetId == INGGRIL) {
				switch (dialogActionId) {
					case QUEST_SELECT:
						if (var >= 1) {
							return sendQuestDialog(env, 2375);
						}
						return false;
					case SELECT_QUEST_REWARD:
						qs.setStatus(QuestStatus.REWARD);
						updateQuestStatus(env);
						return sendQuestEndDialog(env);
				}
			}
		} else if (qs.getStatus() == QuestStatus.REWARD) {
			if (targetId == INGGRIL) {
				TeleportService.teleportTo(player, MAP_PANDAEMONIUM, 1275.37f, 1168.61f, 215.215f, (byte) 30, TeleportAnimation.FADE_OUT_BEAM);
				return sendQuestEndDialog(env);
			}
		}
		return false;
	}

	@Override
	public boolean onEnterWorldEvent(QuestEnv env) {
		Player player = env.getPlayer();
		if (player.getWorldId() == MAP_LAND_OF_SHADOWS) {
			player.getLifeStats().setCurrentHpPercent(100);
			player.getLifeStats().setCurrentMpPercent(100);
			PacketSendUtility.sendMessage(player, "Hmm, let us see how this develops. I hope the Daeva will not buckle under a minor trial.", ChatType.YELLOW_CENTER);
			return true;
		}
		QuestState qs = player.getQuestStateList().getQuestState(questId);
		if (qs == null && player.getRace() == Race.ASMODIANS && player.getLevel() == 1) {
			env.setQuestId(questId);
			return QuestService.startQuest(env);
		}
		return false;
	}

	@Override
	public boolean onKillEvent(QuestEnv env) {
		Player player = env.getPlayer();
		QuestState qs = player.getQuestStateList().getQuestState(questId);
		if (qs != null && qs.getStatus() == QuestStatus.START) {
			int var = qs.getQuestVarById(0);
			if (player.getWorldId() == MAP_LAND_OF_SHADOWS && var == 1) {
				int kills = qs.getQuestVarById(1);
				if (kills < 5) {
					kills++;
					qs.setQuestVarById(1, kills);
					if (kills >= 5) {
						qs.setQuestVar(2);
						PacketSendUtility.sendMessage(player, "Trial combat complete! Speak with Inggril, Daeva of Time, to exit the Land of Shadows.", ChatType.YELLOW_CENTER);
					}
					updateQuestStatus(env);
					return true;
				}
			}
		}
		return false;
	}

	@Override
	public void onLevelChangedEvent(Player player) {
		defaultOnLevelChangedEvent(player);
	}

	private void teleportToLandOfShadows(Player player) {
		WorldMapInstance newInstance = InstanceService.getNextAvailableInstance(MAP_LAND_OF_SHADOWS, player);
		TeleportService.teleportTo(player, newInstance, 680.0f, 520.0f, 358.4f, (byte) 60, TeleportAnimation.FADE_OUT_BEAM);
	}
}
