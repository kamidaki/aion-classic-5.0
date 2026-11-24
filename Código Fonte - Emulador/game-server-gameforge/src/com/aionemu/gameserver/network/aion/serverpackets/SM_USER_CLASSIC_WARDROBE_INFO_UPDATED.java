package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_USER_CLASSIC_WARDROBE_INFO_UPDATED (0x123, nome e número da tabela de pacotes do Game.dll), a resposta da expansão de slot: [H slots
 * comprados]. Sem captura oficial.
 * <p>
 * O tratador do Game.dll (0x8C9300) lê só esse H e o grava no mesmo global que o 2º H do S_USER_CLASSIC_WARDROBE_LOAD (0x16BB850, slots
 * comprados), depois marca a janela para redesenhar. O emulador mandava o cabeçalho do LOAD ([H 1][H slots][H n][C 1]): o cliente lia o 1
 * fixo e passava a mostrar só os gratuitos + 1 até o próximo login.
 */
public class SM_USER_CLASSIC_WARDROBE_INFO_UPDATED extends AionServerPacket {

	private final int extendedSlots;

	public SM_USER_CLASSIC_WARDROBE_INFO_UPDATED(int extendedSlots) {
		this.extendedSlots = extendedSlots;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(extendedSlots);
	}
}
