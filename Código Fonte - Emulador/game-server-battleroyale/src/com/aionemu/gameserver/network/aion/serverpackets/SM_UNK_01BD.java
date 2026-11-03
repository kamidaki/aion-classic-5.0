package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;

/**
 * Legacy alias for SM_HUNT_OBJECTIVE_PROGRESS (0x01BD).
 * @deprecated Use {@link SM_HUNT_OBJECTIVE_PROGRESS} instead.
 */
@Deprecated
public class SM_UNK_01BD extends SM_HUNT_OBJECTIVE_PROGRESS {

	public SM_UNK_01BD() {
		super();
	}

	public SM_UNK_01BD(int counter) {
		super(counter);
	}

	public SM_UNK_01BD(int objective, int counter) {
		super(objective, counter);
	}

	@Override
	protected void writeImpl(AionConnection con) {
		super.writeImpl(con);
	}
}
