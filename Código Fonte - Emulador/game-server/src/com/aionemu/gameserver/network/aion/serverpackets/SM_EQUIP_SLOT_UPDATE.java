package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x0173 (371) - SM_EQUIP_SLOT_UPDATE (4 bytes)
 * Official Classic 5.0 equipment slot state update dispatched after item movement / slot change.
 * Wire: writeD(slotId).
 */
public class SM_EQUIP_SLOT_UPDATE extends AionServerPacket {
	private final int slotId;

	public SM_EQUIP_SLOT_UPDATE() {
		this(7);
	}

	public SM_EQUIP_SLOT_UPDATE(int slotId) {
		this.slotId = slotId;
	}

	public int getSlotId() {
		return slotId;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(slotId);
	}
}
