package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;

/**
 * S_USER_CLASSIC_WARDROBE_INFO_UPDATED (0x123, nome e número da tabela de pacotes do Game.dll), a resposta da expansão de slot. Sem captura
 * oficial.
 * <p>
 * O layout é dedução: o 0x122 (LOAD) é cabeçalho + entradas e o 0x124 (DATA_UPDATED) é ação + uma entrada no formato do LOAD, então o INFO
 * repete o cabeçalho do LOAD, com os slots comprados já somados. O cliente real aceitou em 21/09: depois de expandir para 2 slots, registrou o
 * segundo item.
 */
public class SM_USER_CLASSIC_WARDROBE_INFO_UPDATED extends AbstractWardrobePacket {

	private final int extendedSlots;
	private final int count;

	public SM_USER_CLASSIC_WARDROBE_INFO_UPDATED(int extendedSlots, int count) {
		this.extendedSlots = extendedSlots;
		this.count = count;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeHeader(extendedSlots, count);
	}
}
