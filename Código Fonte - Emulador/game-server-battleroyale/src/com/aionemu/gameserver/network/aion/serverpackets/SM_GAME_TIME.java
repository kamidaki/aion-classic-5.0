package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.services.GameTimeService;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_GAME_TIME extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(GameTimeService.getInstance().getGameTime().getTime()); // Minutes since 1/1/00 00:00:00
	}
}
