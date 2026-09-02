package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Pacote com opcode e payload arbitrarios.
 * <p>
 * Serve para reproduzir pacotes cujo formato ainda nao foi implementado campo a campo,
 * usando o payload medido na captura oficial. O opcode de registro na tabela e apenas um
 * lugar vago exigido pelo construtor de {@link AionServerPacket}: o valor real e definido
 * por {@code setOpcode} logo em seguida.
 *
 * @see com.aionemu.gameserver.dataholders.EnterWorldPackets
 */
public class S_RAW extends AionServerPacket {

	private final byte[] payload;

	public S_RAW(int opcode, byte[] payload) {
		super();
		setOpcode(opcode);
		this.payload = payload;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeB(payload);
	}
}
