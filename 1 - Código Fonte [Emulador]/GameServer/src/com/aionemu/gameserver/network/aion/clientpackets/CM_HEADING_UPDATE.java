package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.S_CHANGE_DIRECTION;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * Heading / rotation update packet from client (decOp 0x003B, wire 0x00C9 in 5.0 Classic).
 * Sent when player changes camera heading or turns around.
 */
public class CM_HEADING_UPDATE extends AionClientPacket {

	private byte heading;

	public CM_HEADING_UPDATE(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
		heading = (byte) readC();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player == null || !player.isSpawned()) {
			return;
		}
		player.getPosition().setH(heading);
		PacketSendUtility.broadcastPacketAndReceive(player, new S_CHANGE_DIRECTION(player.getObjectId(), heading));
	}
}
