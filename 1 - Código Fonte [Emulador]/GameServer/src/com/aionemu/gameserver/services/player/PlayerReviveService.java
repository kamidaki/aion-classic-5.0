/*
 * This file is part of aion-unique <aion-unique.org>.
 *
 *  aion-unique is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  aion-unique is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with aion-unique.  If not, see <http://www.gnu.org/licenses/>.
 */

package com.aionemu.gameserver.services.player;

import com.aionemu.gameserver.configs.administration.AdminConfig;
import com.aionemu.gameserver.model.EmotionType;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.Kisk;
import com.aionemu.gameserver.model.gameobjects.VisibleObject;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.team2.alliance.PlayerAllianceService;
import com.aionemu.gameserver.model.team2.common.legacy.GroupEvent;
import com.aionemu.gameserver.model.team2.common.legacy.PlayerAllianceEvent;
import com.aionemu.gameserver.model.team2.group.PlayerGroupService;
import com.aionemu.gameserver.model.templates.item.ItemUseLimits;
import com.aionemu.gameserver.model.templates.revive_start_points.InstanceReviveStartPoints;
import com.aionemu.gameserver.network.aion.serverpackets.S_ACTION;
import com.aionemu.gameserver.network.aion.serverpackets.S_MESSAGE_CODE;
import com.aionemu.gameserver.network.aion.serverpackets.S_TARGET_INFO;
import com.aionemu.gameserver.network.aion.serverpackets.S_USE_ITEM;
import com.aionemu.gameserver.services.teleport.TeleportService2;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.audit.AuditLogger;
import com.aionemu.gameserver.world.World;
import com.aionemu.gameserver.world.WorldMap;
import com.aionemu.gameserver.world.WorldPosition;
import com.aionemu.gameserver.world.knownlist.Visitor;

public class PlayerReviveService
{
	public static final void duelRevive(Player player) {
		revive(player, 25, 25, false, 0);
		PacketSendUtility.broadcastPacket(player, new S_ACTION(player, EmotionType.RESURRECT), true);
		if (player.getIsFlyingBeforeDeath()) {
			player.getFlyController().startFly();
		}
		player.getGameStats().updateStatsAndSpeedVisually();
		player.unsetResPosState();
	}
	
	public static final void skillRevive(Player player) {
		if (!player.getResStatus()) {
			AuditLogger.info(player, "PlayerReviveService: possibly tried to use a skill revive hack (resStatus false)");
			return;
		}
		revive(player, 25, 25, true, player.getResurrectionSkill());
		PacketSendUtility.broadcastPacket(player, new S_ACTION(player, EmotionType.RESURRECT), true);
		PacketSendUtility.sendPacket(player, S_MESSAGE_CODE.STR_REBIRTH_MASSAGE_ME);
		if (player.getIsFlyingBeforeDeath()) {
			player.getFlyController().startFly();
		}
		player.getGameStats().updateStatsAndSpeedVisually();
		if (player.isInPrison()) {
			TeleportService2.teleportToPrison(player);
		} else if (player.isInResPostState()) {
			TeleportService2.teleportTo(player, player.getWorldId(), player.getInstanceId(), player.getResPosX(), player.getResPosY(), player.getResPosZ());
		}
		player.unsetResPosState();
		player.setIsFlyingBeforeDeath(false);
	}
	
	public static final void handOfReincarnation(Player player) {
		if (!player.getController().isHandOfReincarnationEffect()) {
			AuditLogger.info(player, "PlayerReviveService: handOfReincarnation called without active effect");
			return;
		}
		int rebirthSkill = player.getRebirthSkill();
		revive(player, 50, 50, true, rebirthSkill);
		if (rebirthSkill > 0) {
			player.getEffectController().removeEffect(rebirthSkill);
		}
		player.setRebirthRevive(false);
		player.setRebirthSkill(0);
		player.setRebirthResurrectPercent(0);
		PacketSendUtility.broadcastPacket(player, new S_ACTION(player, EmotionType.RESURRECT), true);
		PacketSendUtility.sendPacket(player, S_MESSAGE_CODE.STR_REBIRTH_MASSAGE_ME);
		if (player.getIsFlyingBeforeDeath()) {
			player.getFlyController().startFly();
		}
		player.getGameStats().updateStatsAndSpeedVisually();
		if (player.isInPrison()) {
			TeleportService2.teleportToPrison(player);
		}
		player.unsetResPosState();
		player.setIsFlyingBeforeDeath(false);
	}
	
	public static final void rebirthRevive(Player player) {
		if (!player.canUseRebirthRevive()) {
			return;
		}
		int rebirthResurrectPercent = player.getRebirthResurrectPercent();
		if (rebirthResurrectPercent <= 0) {
			rebirthResurrectPercent = 5;
		}
		boolean soulSickness = true;
		if (player.getAccessLevel() >= AdminConfig.ADMIN_AUTO_RES) {
			rebirthResurrectPercent = 100;
			soulSickness = false;
		}
		revive(player, rebirthResurrectPercent, rebirthResurrectPercent, soulSickness, player.getRebirthSkill());
		player.setRebirthRevive(false);
		player.setRebirthSkill(0);
		player.setRebirthResurrectPercent(0);
		PacketSendUtility.broadcastPacket(player, new S_ACTION(player, EmotionType.RESURRECT), true);
		PacketSendUtility.sendPacket(player, S_MESSAGE_CODE.STR_REBIRTH_MASSAGE_ME);
		if (player.getIsFlyingBeforeDeath()) {
			player.getFlyController().startFly();
		}
		player.getGameStats().updateStatsAndSpeedVisually();
		if (player.isInPrison()) {
			TeleportService2.teleportToPrison(player);
		}
		player.unsetResPosState();
		player.setIsFlyingBeforeDeath(false);
	}
	
	public static final void bindRevive(Player player) {
		bindRevive(player, 0);
	}
	
	public static final void bindRevive(Player player, int skillId) {
		revive(player, 25, 25, true, skillId);
		if (skillId > 0) {
			PacketSendUtility.sendPacket(player, S_MESSAGE_CODE.STR_REBIRTH_MASSAGE_ME);
		}
		player.getGameStats().updateStatsAndSpeedVisually();
		player.unsetResPosState();
		player.setIsFlyingBeforeDeath(false);
		if (player.isInPrison()) {
			TeleportService2.teleportToPrison(player);
		} else {
			TeleportService2.moveToBindLocation(player, true);
		}
	}
	
	public static final void kiskRevive(Player player) {
		kiskRevive(player, 0);
	}
	
	public static final void kiskRevive(Player player, int skillId) {
		Kisk kisk = player.getKisk();
		if (kisk == null || !kisk.isActive()) {
			bindRevive(player, skillId);
			return;
		}
		if (player.isInPrison()) {
			TeleportService2.teleportToPrison(player);
			return;
		}
		WorldPosition bind = kisk.getPosition();
		kisk.resurrectionUsed();
		revive(player, 25, 25, false, skillId);
		if (skillId > 0) {
			PacketSendUtility.sendPacket(player, S_MESSAGE_CODE.STR_REBIRTH_MASSAGE_ME);
		}
		player.getGameStats().updateStatsAndSpeedVisually();
		player.unsetResPosState();
		player.setIsFlyingBeforeDeath(false);
		TeleportService2.moveToKiskLocation(player, bind);
	}
	
	public static final void instanceRevive(Player player) {
		instanceRevive(player, 0);
	}
	
	public static final void instanceRevive(Player player, int skillId) {
		if (player.getPosition().getWorldMapInstance().getInstanceHandler().onReviveEvent(player)) {
			return;
		}
		WorldMap map = World.getInstance().getWorldMap(player.getWorldId());
		if (map == null || !map.isInstanceType()) {
			bindRevive(player, skillId);
			return;
		}
		revive(player, 25, 25, true, skillId);
		if (skillId > 0) {
			PacketSendUtility.sendPacket(player, S_MESSAGE_CODE.STR_REBIRTH_MASSAGE_ME);
		}
		player.getGameStats().updateStatsAndSpeedVisually();
		InstanceReviveStartPoints revivePoint = TeleportService2.getReviveInstanceStartPoints(map.getMapId());
		if (revivePoint != null) {
			TeleportService2.teleportTo(player, revivePoint.getReviveWorld(), player.getInstanceId(), revivePoint.getX(), revivePoint.getY(), revivePoint.getZ(), revivePoint.getH());
		} else {
			bindRevive(player, skillId);
		}
		player.unsetResPosState();
		player.setIsFlyingBeforeDeath(false);
	}
	
	public static final void revive(final Player player, int hpPercent, int mpPercent, boolean setSoulsickness, int resurrectionSkill) {
		synchronized (player) {
			if (!player.getLifeStats().isAlreadyDead()) {
				return;
			}
			player.getKnownList().doOnAllPlayers(new Visitor<Player>() {
				@Override
				public void visit(Player visitor) {
					VisibleObject target = visitor.getTarget();
					if (target != null && target.getObjectId() == player.getObjectId() && (visitor.getRace() != player.getRace())) {
						visitor.setTarget(null);
						PacketSendUtility.sendPacket(visitor, new S_TARGET_INFO(null));
					}
				}
			});
			boolean isNoResurrectPenalty = player.getController().isNoResurrectPenaltyInEffect();
			player.getMoveController().stopFalling();
			player.setPlayerResActivate(false);
			player.getLifeStats().setCurrentHpPercent(isNoResurrectPenalty ? 100 : hpPercent);
			player.getLifeStats().setCurrentMpPercent(isNoResurrectPenalty ? 100 : mpPercent);
			if (player.getCommonData().getDp() > 0 && !isNoResurrectPenalty) {
				player.getCommonData().setDp(0);
			}
			player.getLifeStats().triggerRestoreOnRevive();
			if (!isNoResurrectPenalty && setSoulsickness) {
				player.getController().updateSoulSickness(resurrectionSkill);
			}
			player.setResurrectionSkill(0);
			player.getController().startProtectionActiveTask();
			player.setPortAnimation(4);
			player.getAggroList().clear();
			player.getController().onBeforeSpawn(false);
			if (player.isInGroup2()) {
				PlayerGroupService.updateGroup(player, GroupEvent.MOVEMENT);
			}
			if (player.isInAlliance2()) {
				PlayerAllianceService.updateAlliance(player, PlayerAllianceEvent.MOVEMENT);
			}
		}
	}
	
	public static final void itemSelfRevive(Player player) {
		Item item = player.getSelfRezStone();
		if (item == null) {
			cancelRes(player);
			return;
		}
		ItemUseLimits useLimits = item.getItemTemplate().getUseLimits();
		int useDelay = useLimits.getDelayTime();
		player.addItemCoolDown(useLimits.getDelayId(), System.currentTimeMillis() + useDelay, useDelay / 1000);
		player.getController().cancelUseItem();
		PacketSendUtility.broadcastPacket(player, new S_USE_ITEM(player.getObjectId(), item.getObjectId(), item.getItemTemplate().getTemplateId()), true);
		if (!player.getInventory().decreaseByObjectId(item.getObjectId(), 1)) {
			cancelRes(player);
			return;
		}
		revive(player, 25, 25, true, player.getResurrectionSkill());
		PacketSendUtility.broadcastPacket(player, new S_ACTION(player, EmotionType.RESURRECT), true);
		PacketSendUtility.sendPacket(player, S_MESSAGE_CODE.STR_REBIRTH_MASSAGE_ME);
		if (player.getIsFlyingBeforeDeath()) {
			player.getFlyController().startFly();
		}
		player.getGameStats().updateStatsAndSpeedVisually();
		if (player.isInPrison()) {
			TeleportService2.teleportToPrison(player);
		}
		player.unsetResPosState();
		player.setIsFlyingBeforeDeath(false);
	}
	
	public static final void startPositionRevive(Player player) {
		startPositionRevive(player, 0);
	}
	
	public static final void startPositionRevive(Player player, int skillId) {
		revive(player, 25, 25, true, skillId);
		if (skillId > 0) {
			PacketSendUtility.sendPacket(player, S_MESSAGE_CODE.STR_REBIRTH_MASSAGE_ME);
		}
		player.getGameStats().updateStatsAndSpeedVisually();
		player.unsetResPosState();
		player.setIsFlyingBeforeDeath(false);
		if (player.isInPrison()) {
			TeleportService2.teleportToPrison(player);
		} else {
			TeleportService2.teleportWorldStartPoint(player, player.getWorldId());
		}
	}
	
	private static final void cancelRes(Player player) {
		AuditLogger.info(player, "Possible selfres hack.");
		player.getController().sendDie();
	}
}