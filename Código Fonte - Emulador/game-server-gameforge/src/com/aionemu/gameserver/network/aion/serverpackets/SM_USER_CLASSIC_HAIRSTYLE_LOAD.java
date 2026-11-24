package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.Collection;
import java.util.List;

import com.aionemu.gameserver.model.gameobjects.player.WardrobeEntry;
import com.aionemu.gameserver.network.aion.AionConnection;

/**
 * Lista de cabelo do Wardrobe 5.0 (0x177; sem nome na tabela de pacotes do Game.dll), no login logo depois do S 0x169: [H entradas] + os
 * registros ({@link AbstractHairstylePacket#writeHairstyle}) + [H slots gratuitos][H slots comprados].
 * <p>
 * Leitor do Game.dll: 0x8D3DB0 (lista em 0x8D89E0). A captura de 2026-09-21 14:56 traz 1 registro e 1/0 nos slots; o cliente guarda os slots
 * como gratuitos e gratuitos + comprados (0x8CC5F4).
 */
public class SM_USER_CLASSIC_HAIRSTYLE_LOAD extends AbstractHairstylePacket {

	private final int ownerObjectId;
	private final Collection<WardrobeEntry> entries;
	private final int freeSlots;
	private final int extendedSlots;

	public SM_USER_CLASSIC_HAIRSTYLE_LOAD(int ownerObjectId, Collection<WardrobeEntry> entries, int freeSlots, int extendedSlots) {
		this.ownerObjectId = ownerObjectId;
		this.entries = entries == null ? List.of() : entries;
		this.freeSlots = freeSlots;
		this.extendedSlots = extendedSlots;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(entries.size());
		for (WardrobeEntry entry : entries)
			writeHairstyle(ownerObjectId, entry);
		writeH(freeSlots);
		writeH(extendedSlots);
	}
}
