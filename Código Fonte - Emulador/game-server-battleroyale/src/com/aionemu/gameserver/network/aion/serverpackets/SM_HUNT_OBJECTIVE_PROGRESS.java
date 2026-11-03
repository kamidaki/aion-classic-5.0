package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01BD (445) - SM_HUNT_OBJECTIVE_PROGRESS (27 bytes)
 * Official Classic 5.0 quest/instance hunt objective progress notification.
 */
public class SM_HUNT_OBJECTIVE_PROGRESS extends AionServerPacket {
	public static final int BOSS = 0x15;
	public static final int NAMED = 0x16;
	public static final int NORMAL = 0x17;

	private final int objective;
	private final int counter;

	public SM_HUNT_OBJECTIVE_PROGRESS() {
		this(NORMAL, 1);
	}

	public SM_HUNT_OBJECTIVE_PROGRESS(int counter) {
		this(NORMAL, counter);
	}

	public SM_HUNT_OBJECTIVE_PROGRESS(int objective, int counter) {
		this.objective = objective;
		this.counter = counter;
	}

	public int getObjective() {
		return objective;
	}

	public int getCounter() {
		return counter;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(1);
		writeD(11);
		writeC(2);
		writeD(objective);
		writeD(0);
		writeD(counter);
		writeD(0);
		writeC(0);
	}
}
