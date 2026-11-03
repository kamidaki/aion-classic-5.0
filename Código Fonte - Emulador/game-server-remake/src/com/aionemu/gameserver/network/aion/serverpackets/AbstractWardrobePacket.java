package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.WardrobeEntry;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Cabeçalho e entrada comuns aos pacotes do Wardrobe 5.0 (0x122, 0x123 e 0x124). O 0x122 é o cabeçalho seguido das entradas; o 0x124 é a ação
 * seguida de uma entrada, no mesmo formato.
 */
public abstract class AbstractWardrobePacket extends AionServerPacket {

	/**
	 * [H 1][H slots comprados][H n][C 1]. Nos 58 0x122 capturados: 1/0/0/1, 1/0/1/1 e 1/2/3/1; n nunca passa dos slots comprados + 1 (o
	 * free_slot_num do client_wardrobe_config). Os dois campos fixos em 1 não mudaram em nenhuma captura.
	 */
	protected final void writeHeader(int extendedSlots, int count) {
		writeH(1);
		writeH(extendedSlots);
		writeH(count);
		writeC(1);
	}

	/**
	 * [D objeto][D item][C tingido][R][G][B][D 0][C favorito], 17 b. O objeto é da entrada, não do item registrado (o 0xEE com 3e0882c0 criou
	 * 840a82c0). A tinta turquesa 169200001 (198d94) virou 01 19 8d 94. O D depois da cor foi 0 nas 58 cargas e nos 5 0x124.
	 */
	protected final void writeEntry(WardrobeEntry entry) {
		writeD(entry.getObjectId());
		writeD(entry.getItemId());
		writeDyeInfo(entry.getColor());
		writeD(0);
		writeC(entry.isLiked() ? 1 : 0);
	}
}
