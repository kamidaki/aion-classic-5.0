package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_BUILDER_CONTROL extends AbstractGmCommandPacket {

	public CM_BUILDER_CONTROL(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}
}
