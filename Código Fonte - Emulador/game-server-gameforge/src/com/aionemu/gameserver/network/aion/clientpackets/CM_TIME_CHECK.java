package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_TIME_CHECK;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_TIME_CHECK extends AionClientPacket {

	/**
	 * Nano time / 1000000
	 */
	private int nanoTime;
	private int stat;

	/**
	 * Constructs new instance of <tt>CM_TIME_CHECK</tt> packet
	 * 
	 * @param opcode
	 */
	public CM_TIME_CHECK(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		nanoTime = readD();
		if (getRemainingBytes() > 0) {
			stat = readC();
		}
		if (getRemainingBytes() >= 8) {
			readD();
			readD();
		}
	}

	@Override
	protected void runImpl() {
		AionConnection client = getConnection();
		if (stat == 0) {
			client.sendPacket(new SM_TIME_CHECK(nanoTime));
		}
	}
}
