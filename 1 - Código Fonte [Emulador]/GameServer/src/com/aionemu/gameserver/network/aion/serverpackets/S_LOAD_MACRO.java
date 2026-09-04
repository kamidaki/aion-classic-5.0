package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

import java.util.Map;

/**
 * Packet with macro list.
 * 
 */
public class S_LOAD_MACRO extends AionServerPacket {

	private Player player;
	private boolean secondPart;

	/**
	 * Constructs new <tt>SM_MACRO_LIST </tt> packet
	 */
	public S_LOAD_MACRO(Player player, boolean secondPart) {
		this.player = player;
		this.secondPart = secondPart;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	protected void writeImpl(AionConnection con) {
		writeD(player.getObjectId());// player id
		
		Map<Integer, String> macrosToSend = player.getMacroList().getMarcosPart(secondPart);
		int size = macrosToSend.size();
		
		if(secondPart) {
			writeC(0x00);
			writeH(size);
		}
		else {
			writeC(0x01);
			writeH(-size);
		}
		
		if (size != 0) {
			for (Map.Entry<Integer, String> entry : macrosToSend.entrySet()) {
				writeC(entry.getKey());// order
				writeS(entry.getValue());// xml
			}
		}
	}
}
