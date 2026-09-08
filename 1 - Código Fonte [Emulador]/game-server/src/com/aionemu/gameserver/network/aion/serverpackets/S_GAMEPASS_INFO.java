package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.account.AccountSielEnergy;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

public class S_GAMEPASS_INFO extends AionServerPacket {

	private final AccountSielEnergy accountSielEnergy;

	public S_GAMEPASS_INFO(AccountSielEnergy accountSielEnergy) {
		this.accountSielEnergy = accountSielEnergy;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		if (accountSielEnergy == null) {
			writeD(1);
			writeQ(0);
			writeQ(0);
			writeQ(0);
			writeC(0);
			return;
		}
		writeD(accountSielEnergy.getType().getId());
		switch (accountSielEnergy.getType().getId()) {
			case 1 -> {
				writeQ(accountSielEnergy.getChargeTime() != null ? -accountSielEnergy.getChargeTime().getTime() / 1000 : 0);
				writeQ(0);
				writeQ(0);
			}
			case 2 -> {
				writeQ(accountSielEnergy.getChargeTime() != null ? -accountSielEnergy.getChargeTime().getTime() / 1000 : 0);
				writeQ(accountSielEnergy.getRemain());
				writeQ(0);
			}
			case 3 -> {
				writeQ(accountSielEnergy.getEnd() != null ? (accountSielEnergy.getEnd().getTime() - System.currentTimeMillis()) / 1000 : 864000L);
				writeQ(0);
				writeQ(0);
			}
		}
		// Trailing alignment byte: classic 5.0 client packet length = 29 bytes
		writeC(0x00);
	}
}
