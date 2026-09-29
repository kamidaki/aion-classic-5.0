package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x163, essência da Legion: [D essências][D 0][D fragmentos][D 0], em totais (Lost Academy 22/09: 0/10 depois da recompensa da missão;
 * depois 0/0 e 1/0 quando 10 fragmentos viraram uma essência, receita 1 do client_guild_craft).
 */
public class SM_LEGION_ESSENCE extends AionServerPacket {

	private final int essence;
	private final int essencePiece;

	public SM_LEGION_ESSENCE(int essence, int essencePiece) {
		this.essence = essence;
		this.essencePiece = essencePiece;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(essence);
		writeD(0);
		writeD(essencePiece);
		writeD(0);
	}
}
