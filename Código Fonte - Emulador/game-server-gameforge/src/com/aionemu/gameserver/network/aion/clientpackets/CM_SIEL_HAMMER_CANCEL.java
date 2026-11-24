package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.craft.SielHammerService;

/** C_CANCEL_ITEM_CRUSH, decoded 0x152 / wire 0x220, empty payload. */
public class CM_SIEL_HAMMER_CANCEL extends AionClientPacket {
	private boolean valid;
	public CM_SIEL_HAMMER_CANCEL(int opcode, Set<State> states) { super(opcode, states); }
	@Override
	protected void readImpl() { valid = getRemainingBytes() == 0; }
	@Override
	protected void runImpl() {
		var player = getConnection().getActivePlayer();
		if (valid && player != null) SielHammerService.cancel(player);
	}
}
