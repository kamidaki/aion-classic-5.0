package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x154, resposta ao aceite (C_GUILD 0x11) ou à recusa (0x12) de um candidato: [D personagem][C 1 aceito, 2 recusado] (Nova Pasta 2026-09-29
 * 16:49, 2 de 2).
 */
public class SM_LEGION_APPLICANT_RESULT extends AionServerPacket {

	public static final int ACCEPTED = 1;
	public static final int REFUSED = 2;

	private final int playerId;
	private final int result;

	public SM_LEGION_APPLICANT_RESULT(int playerId, int result) {
		this.playerId = playerId;
		this.result = result;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(playerId);
		writeC(result);
	}
}
