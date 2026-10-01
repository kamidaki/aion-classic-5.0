package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_FRIEND_RESPONSE;
import com.aionemu.gameserver.utils.Util;
import com.aionemu.gameserver.world.World;

/**
 * Sistema de busca / localização de jogador no Classic 5.0 (Locate / Find Player).
 * Opcode decodificado: 206 (0x00CE), no fio 0x01A4.
 */
public class CM_LOCATE_PLAYER extends AionClientPacket {

	private int unk;
	private int targetCharId;
	private String targetName;

	public CM_LOCATE_PLAYER(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		unk = readD();
		targetCharId = readD();
		targetName = readS();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null)
			return;

		Player target = null;
		if (targetName != null && !targetName.isEmpty()) {
			target = World.getInstance().getPlayer(Util.convertName(targetName));
		}
		if (target == null && targetCharId > 0) {
			target = World.getInstance().getPlayer(targetCharId);
		}
		if (target == null || !target.isOnline()) {
			sendPacket(SM_FRIEND_RESPONSE.TARGET_OFFLINE);
		}
	}
}
