package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_CHANNEL_CHATTING_PERMISSION (0x128, nome e numero da tabela de registro de pacotes do Game.dll 5.0). O oficial manda [C 1] em toda
 * entrada no mundo, logo depois do S_CHANNEL_CHATTING_BLACKLIST_SETTING (aionlook.pcapng e subida-1-60). O 0x128 estava ocupado pelo
 * SM_BIND_POINT_TELEPORT, que e o S_HOTSPOT (0x1AF), e a permissao nunca era enviada: o cliente nao chegava a autenticar no chat.
 */
public class SM_CHANNEL_CHATTING_PERMISSION extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(1);
	}
}
