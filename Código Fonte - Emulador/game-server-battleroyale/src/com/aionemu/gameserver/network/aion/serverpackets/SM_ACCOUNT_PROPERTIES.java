package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.configs.administration.AdminConfig;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * 5.0 Classic S_BUILDER_LEVEL (opcode 0xEE / 238)
 */
public class SM_ACCOUNT_PROPERTIES extends AionServerPacket {

	private boolean isGM;

	public SM_ACCOUNT_PROPERTIES() {
	}

	public SM_ACCOUNT_PROPERTIES(boolean isGM) {
		this.isGM = isGM;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		boolean gm = isGM || (con.getAccount() != null && con.getAccount().getAccessLevel() >= AdminConfig.GM_PANEL);
		writeH(gm ? 3 : 0);
		writeB(new byte[27]);
	}
}

