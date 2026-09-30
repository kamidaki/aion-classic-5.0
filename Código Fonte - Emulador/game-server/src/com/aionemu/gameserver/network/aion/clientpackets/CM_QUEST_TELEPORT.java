package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.spawns.SpawnSearchResult;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;
import com.aionemu.gameserver.services.teleport.TeleportService;
import com.aionemu.gameserver.utils.PacketSendUtility;
import com.aionemu.gameserver.utils.ThreadPoolManager;

import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

public class CM_QUEST_TELEPORT extends AionClientPacket {

	private static final ConcurrentHashMap<Integer, Long> cooldowns = new ConcurrentHashMap<>();
	private static final long COOLDOWN_MILLIS = 5_000L; // 5s de tolerância para reutilizar

	private int questId;
	private int npcId;

	public CM_QUEST_TELEPORT(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_QUEST_TELEPORT(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		this.questId = readD();
		this.npcId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null || !player.isSpawned() || player.isDead()) {
			return;
		}

		final int playerId = player.getObjectId();
		final long now = System.currentTimeMillis();

		// Checagem de cooldown para evitar flood do botão de teleporte (5s de tolerância)
		Long expireAt = cooldowns.get(playerId);
		if (expireAt != null) {
			if (now < expireAt) {
				return;
			}
			cooldowns.remove(playerId, expireAt);
		}

		// Checagem se o jogador está em combate
		if (player.getController().isInCombat()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_CANNOT_TELEPORT_IN_COMBAT_MODE());
			return;
		}

		// Checagem se o jogador está se movendo ou voando
		if (player.getMoveController().isInMove() || player.isFlying()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_CANNOT_TELEPORT_IN_THIS_STATE());
			return;
		}

		if (npcId <= 0) {
			return;
		}

		// Checagem se o NPC existe e se pertence ao mesmo mapa do jogador
		SpawnSearchResult searchResult = DataManager.SPAWNS_DATA.getFirstSpawnByNpcId(player.getWorldId(), npcId);
		if (searchResult == null) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_CANNOT_TELEPORT_TARGET_NOT_APPEARED());
			return;
		}

		if (searchResult.getWorldId() != player.getWorldId()) {
			PacketSendUtility.sendPacket(player, SM_SYSTEM_MESSAGE.STR_MSG_CANNOT_TELEPORT_TARGET_IN_OTHER_REGION());
			return;
		}

		// Aplica cooldown de 5 segundos com limpeza agendada apropriada
		final long newExpireAt = now + COOLDOWN_MILLIS;
		cooldowns.put(playerId, newExpireAt);
		ThreadPoolManager.getInstance().schedule(() -> cooldowns.remove(playerId, newExpireAt), COOLDOWN_MILLIS, TimeUnit.MILLISECONDS);

		TeleportService.teleportToNpc(player, npcId);
	}

	public static void onPlayerLogout(int playerId) {
		cooldowns.remove(playerId);
	}
}
