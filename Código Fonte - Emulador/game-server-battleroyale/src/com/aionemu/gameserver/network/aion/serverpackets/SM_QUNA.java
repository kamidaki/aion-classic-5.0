package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Saldo de Quna da conta (0x11B): [H código][Q saldo], 10 b. Oficial: só depois de gastar (5 de 5), com H 0x15C no retune, 0x12F na compra da
 * Auction House e 0x149 na troca de cabelo. Não se sabe se o H é código de contexto ou saldo de FREE_QUNA; nos contextos sem captura vai 0,
 * que serve nos dois casos.
 * <p>
 * O cliente oficial lê o saldo do STS da NCSoft (porta 6600) e não o recebe no login; o emulador manda este pacote no login porque é o único
 * canal que o cliente tem aqui.
 */
public class SM_QUNA extends AionServerPacket {

	private final int code;
	private final long balance;

	public SM_QUNA(int code, long balance) {
		this.code = code;
		this.balance = balance;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(code);
		writeQ(balance);
	}
}
