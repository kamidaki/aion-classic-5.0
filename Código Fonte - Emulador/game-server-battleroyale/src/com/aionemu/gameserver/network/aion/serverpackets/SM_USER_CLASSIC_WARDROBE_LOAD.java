package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.Collection;

import com.aionemu.gameserver.model.gameobjects.player.WardrobeEntry;
import com.aionemu.gameserver.network.aion.AionConnection;

/**
 * S_USER_CLASSIC_WARDROBE_LOAD (0x122): o guarda-roupa inteiro, no login entre o 0x117 e o 0x138 (58 de 58 capturas).
 */
public class SM_USER_CLASSIC_WARDROBE_LOAD extends AbstractWardrobePacket {

	private final int extendedSlots;
	private final Collection<WardrobeEntry> entries;

	public SM_USER_CLASSIC_WARDROBE_LOAD(int extendedSlots, Collection<WardrobeEntry> entries) {
		this.extendedSlots = extendedSlots;
		this.entries = entries;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeHeader(extendedSlots, entries.size());
		for (WardrobeEntry entry : entries)
			writeEntry(entry);
	}
}
