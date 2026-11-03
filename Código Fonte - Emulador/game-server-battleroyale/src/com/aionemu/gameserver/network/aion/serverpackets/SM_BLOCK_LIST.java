package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.BlockList;
import com.aionemu.gameserver.model.gameobjects.player.BlockedPlayer;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_BLOCK_LIST extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		BlockList list = con.getActivePlayer().getBlockList();
		writeH(-list.getSize());
		writeC(0); // Unk
		for (BlockedPlayer player : list) {
			writeS(player.getName());
			writeS(player.getReason());
		}
	}
}
