package com.aionemu.gameserver.network.aion.serverpackets;

import java.nio.charset.StandardCharsets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Resposta de autenticação / token do bloco de notas (MemoPad) no Classic 5.0.
 * Opcode servidor: 382 (0x017E), no fio 0x0296.
 * Formato oficial (abriritemetc.pcapng pacote 3608): [D comprimento=18][18 bytes token ASCII]
 */
public class SM_MEMO_TOKEN extends AionServerPacket {

	private static final byte[] TOKEN = "#3ogd6RW\u000f\u00c4U)GTQZ12".getBytes(StandardCharsets.ISO_8859_1);

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(TOKEN.length);
		writeB(TOKEN);
	}
}
