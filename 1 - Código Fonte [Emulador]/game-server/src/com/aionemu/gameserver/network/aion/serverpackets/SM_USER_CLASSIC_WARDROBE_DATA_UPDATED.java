package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.WardrobeEntry;
import com.aionemu.gameserver.network.aion.AionConnection;

/**
 * S_USER_CLASSIC_WARDROBE_DATA_UPDATED (0x124): [C ação] + a entrada no formato do 0x122, com o estado depois da ação (5 de 5 nas capturas).
 */
public class SM_USER_CLASSIC_WARDROBE_DATA_UPDATED extends AbstractWardrobePacket {

	/** Resposta ao C 0xEE, depois do S 0x1C do item (motivo 0x81) e da msg 1401541. */
	public static final int REGISTERED = 1;
	/** Resposta ao C 0xEF, antes da msg 1401542. */
	public static final int DELETED = 2;
	/** Resposta ao C 0xF8, depois do S 0x1C da tinta (motivo 0x82) e antes da msg 1401565. */
	public static final int DYED = 3;
	/** Resposta ao C 0xF9, antes da msg 1401543. */
	public static final int FAVORITE = 4;

	private final int action;
	private final WardrobeEntry entry;

	public SM_USER_CLASSIC_WARDROBE_DATA_UPDATED(int action, WardrobeEntry entry) {
		this.action = action;
		this.entry = entry;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(action);
		writeEntry(entry);
	}
}
