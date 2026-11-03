package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x165, saldo de moedas pessoais da Legion: [D moedas]. Sobe o reward_coin_cnt de cada produção (Kodra: +440 por poção, 22/09).
 */
public class SM_LEGION_COIN extends AionServerPacket {

	private final int coins;

	public SM_LEGION_COIN(int coins) {
		this.coins = coins;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(coins);
	}
}
