package com.aionemu.gameserver.controllers;

import com.aionemu.gameserver.model.EmotionType;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.state.CreatureState;
import com.aionemu.gameserver.model.gameobjects.state.FlyState;
import com.aionemu.gameserver.network.aion.serverpackets.SM_EMOTION;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.skillengine.effect.AbnormalState;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.audit.AuditLogger;

/**
 * @author Lost Academy Team & Durak
 */
public class FlyController {

	private static final long FLY_REUSE_TIME = 10000;
	/**
	 * Quick Glide (ALL_FlyBoost), medido na 5.0 oficial em Gelkmaros: a velocidade vai a 18,00 fixos, planando do chão (7,68) ou do voo (14,49),
	 * sem modificador. O G2 não foi medido e usa o mesmo valor.
	 */
	public static final int FLY_SPRINT_SPEED = 18000;
	private static final int[] FLY_SPRINT_SKILLS = { 3180, 2669 }; // ALL_FlyBoost_G2, ALL_FlyBoost_G1
	private final Player player;
	private volatile int flySprintSkillId;

	public FlyController(Player player) {
		this.player = player;
	}

	/**
	 * CM_EMOTION FLY_SPRINT. O oficial responde CHANGE_SPEED e depois FLY_SPRINT com o id da skill; o fim vem do cliente (FLY_SPRINT_END) antes de
	 * pousar.
	 */
	public boolean startFlySprint() {
		if (isFlySprinting() || !player.isInGlidingState())
			return false;
		int skillId = 0;
		for (int id : FLY_SPRINT_SKILLS) {
			if (player.getSkillList().isSkillPresent(id)) {
				skillId = id;
				break;
			}
		}
		if (skillId == 0)
			return false;
		flySprintSkillId = skillId;
		// O Quick Glide zera a recarga do planar: o cliente libera um planar novo na hora, e no oficial o personagem voltou a planar 7,9 s depois do
		// anterior (recarga de 10 s) por ter usado o boost (Quick_Glider 2026-09-14 08:47, 30,65 s e 38,53 s). Sem isso o switchToGliding recusava o
		// planar seguinte, o servidor não ficava em GLIDING e o próximo Quick Glide era ignorado até a recarga acabar.
		player.setFlyReuseTime(0);
		player.getGameStats().updateStatsAndSpeedVisually();
		PacketSendUtility.broadcastToSightedPlayers(player, new SM_EMOTION(player, EmotionType.FLY_SPRINT, skillId, 0), true);
		return true;
	}

	public boolean endFlySprint() {
		if (flySprintSkillId == 0)
			return false;
		flySprintSkillId = 0;
		player.getGameStats().updateStatsAndSpeedVisually();
		PacketSendUtility.broadcastToSightedPlayers(player, new SM_EMOTION(player, EmotionType.FLY_SPRINT_END), true);
		return true;
	}

	/**
	 * Só vale planando: morte e windstream tiram o GLIDING sem passar por aqui, e o flag que sobra não pode mexer na velocidade.
	 */
	public boolean isFlySprinting() {
		return flySprintSkillId != 0 && player.isInGlidingState();
	}

	public void onStopGliding() {
		if (player.isInGlidingState()) {
			flySprintSkillId = 0;
			player.unsetFlyState(FlyState.GLIDING);
			player.unsetState(CreatureState.GLIDING);
			if (!player.isInFlyState(FlyState.FLYING)) {
				player.getLifeStats().triggerFpRestore();
				PacketSendUtility.broadcastToSightedPlayers(player, new SM_EMOTION(player, EmotionType.STOP_GLIDE), true);
			} else {
				player.getLifeStats().triggerFpReduce();
			}
			player.getGameStats().updateStatsAndSpeedVisually();
			if (!player.isFlying()) {
				notifyNearbyNpcsOfFlightChange(false);
			}
		}
	}

	/**
	 * Ends flying 1) by CM_EMOTION (pageDown or fly button press) 2) from server side during teleport (abyss gates should not break flying) 3)
	 * when FP is decreased to 0
	 */
	public void endFly(boolean broadcastPacket) {
		flySprintSkillId = 0;
		player.unsetFlyState(FlyState.FLYING);
		player.unsetFlyState(FlyState.GLIDING);
		player.unsetState(CreatureState.FLYING);
		player.unsetState(CreatureState.GLIDING);
		player.unsetState(CreatureState.FLOATING_CORPSE);
		player.getGameStats().updateStatsAndSpeedVisually();

		if (broadcastPacket && player.isSpawned())
			PacketSendUtility.broadcastToSightedPlayers(player, new SM_EMOTION(player, EmotionType.LAND), true);
		player.getLifeStats().triggerFpRestore();
		notifyNearbyNpcsOfFlightChange(false);
	}

	/**
	 * This method is called to start flying (called by CM_EMOTION when pageUp or pressed fly button, on revive or after teleport in some cases)
	 * 
	 * @param broadcastPacket
	 *          - notify the players client, and all players in range that he started flying
	 * @param ignoreFlightCooldown
	 *          - if true, this will skip cooldown check and not set a new cooldown
	 * @return False if the player could not start flying due to some restriction, true otherwise (this method does not consider if the player was
	 *         already flying).
	 */
	public boolean startFly(boolean broadcastPacket, boolean ignoreFlightCooldown) {
		if (!canFly(player))
			return false;
		if (!ignoreFlightCooldown) {
			if (player.getFlyReuseTime() > System.currentTimeMillis()) {
				AuditLogger.log(player, "possibly using fly cooldown hack. Left cooldown time: " + ((player.getFlyReuseTime() - System.currentTimeMillis()) / 1000) + "s");
				return false;
			}
			player.setFlyReuseTime(System.currentTimeMillis() + FLY_REUSE_TIME - 100);
		}
		player.setFlyState(FlyState.FLYING);
		player.setState(CreatureState.FLYING);
		player.getLifeStats().triggerFpReduce();
		player.getGameStats().updateStatsAndSpeedVisually();

		if (broadcastPacket)
			PacketSendUtility.broadcastToSightedPlayers(player, new SM_EMOTION(player, EmotionType.FLY), true);
		notifyNearbyNpcsOfFlightChange(true);
		return true;
	}

	private static boolean canFly(Player player) {
		if (player.getEffectController().isAbnormalSet(AbnormalState.NOFLY)) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_CANT_FLY_NOW_DUE_TO_NOFLY());
			return false;
		}
		if (player.getTransformModel().cantFly()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_FLY_CANNOT_FLY_POLYMORPH_STATUS());
			return false;
		}
		return player.getStore() == null;
	}

	/**
	 * Switching to glide mode (called by CM_MOVE with VALIDATE_GLIDE movement type) 1) from standing state 2) from flying state If from stand to glide
	 * - start fp reduce + emotions/stats if from fly to glide - only emotions/stats
	 */
	public boolean switchToGliding() {
		if (player.isInGlidingState() || !player.canPerformMove())
			return false;

		if (!canGlide(player))
			return false;
		if (player.getFlyState() == 0) {
			// fly reuse time only if gliding from walking
			if (player.getFlyReuseTime() > System.currentTimeMillis()) {
				return false;
			}
			player.setFlyReuseTime(System.currentTimeMillis() + FLY_REUSE_TIME);
		}
		flySprintSkillId = 0;
		player.setFlyState(FlyState.GLIDING);
		player.setState(CreatureState.GLIDING);
		player.getLifeStats().triggerFpReduce();
		player.getGameStats().updateStatsAndSpeedVisually();
		notifyNearbyNpcsOfFlightChange(true);
		return true;
	}

	private void notifyNearbyNpcsOfFlightChange(boolean airborne) {
		if (player == null || !player.isSpawned() || player.getKnownList() == null) {
			return;
		}
		player.getKnownList().forEachNpc(npc -> {
			if (npc == null || npc.isDead() || !npc.isSpawned() || !(npc.getAi() instanceof com.aionemu.gameserver.ai.NpcAI npcAI)) {
				return;
			}
			com.aionemu.gameserver.ai.handler.AttackEventHandler.onPlayerFlightStateChanged(npcAI, player, airborne);
		});
	}

	private static boolean canGlide(Player player) {
		if (player.getTransformModel().cantFly()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_GLIDE_CANNOT_GLIDE_POLYMORPH_STATUS());
			return false;
		}
		return true;
	}
}
