package ai.worlds;

import static com.aionemu.gameserver.model.DialogAction.*;

import com.aionemu.gameserver.ai.AIName;
import com.aionemu.gameserver.model.Race;
import com.aionemu.gameserver.model.gameobjects.Creature;
import com.aionemu.gameserver.model.gameobjects.Npc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.serverpackets.SM_DIALOG_WINDOW;
import com.aionemu.gameserver.network.aion.serverpackets.SM_ITEM_USAGE_ANIMATION;
import com.aionemu.gameserver.questEngine.QuestEngine;
import com.aionemu.gameserver.questEngine.model.QuestEnv;
import com.aionemu.gameserver.skillengine.SkillEngine;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.PositionUtil;
import com.aionemu.gameserver.utils.ThreadPoolManager;
import com.aionemu.gameserver.world.WorldMapType;

import java.util.concurrent.Future;

import ai.GeneralNpcAI;

/**
 * @author xTz, bobobear, Lost Academy port
 */
@AIName("world_blesser")
public class WorldBlesserAI extends GeneralNpcAI {

	private static final int WORLD_BLESSER_NPC_ID = 282858;
	private static final int WORLD_BLESSING_SKILL_ID = 50052;
	private static final float WORLD_BLESSING_RADIUS = 3.0f;

	private Future<?> checkTask;

	public WorldBlesserAI(Npc owner) {
		super(owner);
	}

	@Override
	protected void handleSpawned() {
		super.handleSpawned();
		if (getNpcId() == WORLD_BLESSER_NPC_ID) {
			startCheckTask();
		}
	}

	@Override
	protected void handleDespawned() {
		stopCheckTask();
		super.handleDespawned();
	}

	private void startCheckTask() {
		checkTask = ThreadPoolManager.getInstance().scheduleAtFixedRate(() -> {
			try {
				Npc owner = getOwner();
				if (owner == null || !owner.isSpawned()) {
					stopCheckTask();
					return;
				}

				owner.getKnownList().forEachPlayer(player -> {
					if (player == null || player.isDead()) {
						return;
					}

					tryApplyWorldBlessing(player);
				});
			} catch (Exception e) {
				// Silently ignore
			}
		}, 100, 250);
	}

	private void stopCheckTask() {
		if (checkTask != null) {
			checkTask.cancel(true);
			checkTask = null;
		}
	}

	private void tryApplyWorldBlessing(Player player) {
		if (player == null || player.getEffectController().hasAbnormalEffect(WORLD_BLESSING_SKILL_ID)) {
			return;
		}

		if (PositionUtil.getDistance(getOwner(), player) > WORLD_BLESSING_RADIUS) {
			return;
		}

		int worldId = getOwner().getWorldId();
		if ((worldId == WorldMapType.GELKMAROS.getId() && player.getRace() == Race.ELYOS) ||
			(worldId == WorldMapType.INGGISON.getId() && player.getRace() == Race.ASMODIANS)) {
			return;
		}

		SkillEngine.getInstance().getSkill(getOwner(), WORLD_BLESSING_SKILL_ID, 1, player).useSkill();
		broadcastHeartAnimation(player);
	}

	private void broadcastHeartAnimation(Player player) {
		PacketSendUtility.broadcastPacket(
			player,
			new SM_ITEM_USAGE_ANIMATION(player.getObjectId(), 0, 160010340),
			true
		);
	}

	@Override
	protected void handleCreatureSee(Creature creature) {
		super.handleCreatureSee(creature);
		if (getNpcId() == WORLD_BLESSER_NPC_ID && creature instanceof Player) {
			tryApplyWorldBlessing((Player) creature);
		}
	}

	@Override
	protected void handleCreatureMoved(Creature creature) {
		super.handleCreatureMoved(creature);
		if (getNpcId() == WORLD_BLESSER_NPC_ID && creature instanceof Player) {
			tryApplyWorldBlessing((Player) creature);
		}
	}

	@Override
	protected void handleDialogStart(Player player) {
		switch (getNpcId()) {
			case 831030: // Netalion
			case 831024: // Renniah
			case 831025: // Erdat
			case 831026: // Erdat
			case 831028: // Erdat
			case 831027: // Karzanke
				super.handleDialogStart(player);
				break;
			case WORLD_BLESSER_NPC_ID:
				tryApplyWorldBlessing(player);
				break;
			default: {
				PacketSendUtility.sendPacket(player, new SM_DIALOG_WINDOW(getObjectId(), 1011));
				break;
			}
		}
	}

	@Override
	public boolean onDialogSelect(Player player, int dialogActionId, int questId, int extendedRewardIndex) {
		QuestEnv env = new QuestEnv(getOwner(), player, questId, dialogActionId);
		env.setExtendedRewardIndex(extendedRewardIndex);
		if (QuestEngine.getInstance().onDialog(env) && dialogActionId != SETPRO1) {
			return true;
		}
		if (dialogActionId == SETPRO1) {
			SkillEngine.getInstance().getSkill(getOwner(), 20950, 1, player).useWithoutPropSkill();
		} else if (dialogActionId == QUEST_SELECT && questId != 0) {
			PacketSendUtility.sendPacket(player, new SM_DIALOG_WINDOW(getObjectId(), 10, questId));
		}
		return true;
	}

}
