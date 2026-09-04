package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.S_PING;

/**
 * This packet is sent when player write /ping
 * 
 */
public class CM_PING_REQUEST extends AionClientPacket {

	/**
	 * Constructs new instance of <tt>CM_PING_REQUEST </tt> packet
	 * 
	 * @param opcode
	 */
	public CM_PING_REQUEST(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void readImpl() {
		// empty
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void runImpl() {
		sendPacket(new S_PING());
	}
}
