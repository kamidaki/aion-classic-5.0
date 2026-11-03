package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Slots da lista de cabelo do Wardrobe 5.0 (0x179; sem nome na tabela de pacotes do Game.dll), a resposta da expansão (C 0xEA): [H slots
 * gratuitos][H slots comprados]. Sem captura oficial.
 * <p>
 * O tratador do Game.dll (0x8CCCD0) grava os mesmos dois campos que o fim do S 0x177 (gratuitos e gratuitos + comprados) e chama o retorno que
 * o clique de expansão deixou pendente (0x702D47), que redesenha a aba.
 */
public class SM_USER_CLASSIC_HAIRSTYLE_SLOTS extends AionServerPacket {

	private final int freeSlots;
	private final int extendedSlots;

	public SM_USER_CLASSIC_HAIRSTYLE_SLOTS(int freeSlots, int extendedSlots) {
		this.freeSlots = freeSlots;
		this.extendedSlots = extendedSlots;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(freeSlots);
		writeH(extendedSlots);
	}
}
