package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x00C5 (197) - SM_CREATURE_STATE_UPDATE (13 bytes)
 * Official Classic 5.0 creature state and action update notification.
 * Wire: writeD(targetId) + writeC(action) + writeD(val1) + writeD(val2).
 */
public class SM_CREATURE_STATE_UPDATE extends AionServerPacket {
	private final int targetId;
	private final int action;
	private final int val1;
	private final int val2;

	public SM_CREATURE_STATE_UPDATE() {
		this(0x8003236F, 3, 13, 0);
	}

	public SM_CREATURE_STATE_UPDATE(int targetId, int action, int val1, int val2) {
		this.targetId = targetId;
		this.action = action;
		this.val1 = val1;
		this.val2 = val2;
	}

	public int getTargetId() {
		return targetId;
	}

	public int getAction() {
		return action;
	}

	public int getVal1() {
		return val1;
	}

	public int getVal2() {
		return val2;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(targetId);
		writeC(action);
		writeD(val1);
		writeD(val2);
	}
}
