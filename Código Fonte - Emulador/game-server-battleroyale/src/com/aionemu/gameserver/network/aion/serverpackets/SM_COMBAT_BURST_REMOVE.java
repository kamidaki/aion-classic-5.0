package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0182 (386) - SM_COMBAT_BURST_REMOVE (8 bytes)
 * Official Classic 5.0 combat burst / abnormal effect visual removal.
 * Wire: writeD(effectId) + writeD(targetObjectId).
 */
public class SM_COMBAT_BURST_REMOVE extends AionServerPacket {
	private final int effectId;
	private final int targetObjectId;

	public SM_COMBAT_BURST_REMOVE() {
		this(0x00036273, 0x802e4967);
	}

	public SM_COMBAT_BURST_REMOVE(int effectId, int targetObjectId) {
		this.effectId = effectId;
		this.targetObjectId = targetObjectId;
	}

	public int getEffectId() {
		return effectId;
	}

	public int getTargetObjectId() {
		return targetObjectId;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(effectId);
		writeD(targetObjectId);
	}
}
