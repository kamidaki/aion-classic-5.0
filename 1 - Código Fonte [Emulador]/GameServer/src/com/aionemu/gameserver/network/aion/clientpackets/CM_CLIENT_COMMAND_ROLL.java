package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.commons.utils.Rnd;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.S_MESSAGE_CODE;
import com.aionemu.gameserver.utils.PacketSendUtility;


public class CM_CLIENT_COMMAND_ROLL extends AionClientPacket {

	private int maxRoll;
	private int roll;

	public CM_CLIENT_COMMAND_ROLL(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	@Override
	protected void readImpl() {
		maxRoll = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();

		roll = Rnd.get(1, maxRoll);
		PacketSendUtility.sendPacket(player, new S_MESSAGE_CODE(1400126, roll, maxRoll));
		PacketSendUtility.broadcastPacket(player, new S_MESSAGE_CODE(1400127, player.getName(), roll, maxRoll));
	}
}
