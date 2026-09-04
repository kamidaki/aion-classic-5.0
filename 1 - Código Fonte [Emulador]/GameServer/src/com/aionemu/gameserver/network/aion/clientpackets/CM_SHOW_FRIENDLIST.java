package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.S_BUDDY_LIST;

/**
 * Send when the client requests the friendlist
 * 
 */
public class CM_SHOW_FRIENDLIST extends AionClientPacket {

	public CM_SHOW_FRIENDLIST(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void readImpl() {

	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void runImpl() {
		sendPacket(new S_BUDDY_LIST());

	}

}
