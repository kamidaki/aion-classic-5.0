package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.craft.SielAnvilService;

/** C_CANCLE_SPECIAL_COMBINE: wire 0x1FB, one recipe id. */
public class CM_SIEL_ANVIL_CANCEL extends AionClientPacket {
	private int recipeId;
	private boolean valid;
	public CM_SIEL_ANVIL_CANCEL(int opcode, Set<State> states) { super(opcode, states); }
	@Override
	protected void readImpl() {
		valid = getRemainingBytes() == 4;
		if (valid) recipeId = readD();
	}
	@Override
	protected void runImpl() {
		var player = getConnection().getActivePlayer();
		if (valid && player != null) SielAnvilService.cancel(player, recipeId);
	}
}
