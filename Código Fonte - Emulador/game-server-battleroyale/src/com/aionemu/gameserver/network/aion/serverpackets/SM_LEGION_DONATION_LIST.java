package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.Map;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x159, lista de produção do dia da Legion: [H n] n x ([D grupo][D índice]), 66 b com os 8 grupos (27 de 27 nas capturas oficiais).
 */
public class SM_LEGION_DONATION_LIST extends AionServerPacket {

	private final Map<Integer, Integer> selection;

	public SM_LEGION_DONATION_LIST(Map<Integer, Integer> selection) {
		this.selection = selection;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(selection.size());
		selection.forEach((group, index) -> {
			writeD(group);
			writeD(index);
		});
	}
}
