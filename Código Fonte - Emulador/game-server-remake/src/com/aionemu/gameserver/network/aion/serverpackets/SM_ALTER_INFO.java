package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Atualiza o estado de Altar / FFA, cooldown e pontuação/baixas do jogador (Opcode 0x016B / 363 dec).
 * Processado nativamente por Game.dll 0x1808CBD70:
 *  - readD(): playerObjectId
 *  - readQ(): cooldownTimestamp (timestamp de término em millisegundos)
 *  - readD(): alterPoints (baixas / pontos do Livro de Eltar)
 * 
 * @author Lost Academy Team & Durak
 */
public class SM_ALTER_INFO extends AionServerPacket {

	private final int playerObjectId;
	private final long cooldownTimestamp;
	private final int alterPoints;

	public SM_ALTER_INFO(int playerObjectId, long cooldownTimestamp, int alterPoints) {
		this.playerObjectId = playerObjectId;
		this.cooldownTimestamp = cooldownTimestamp;
		this.alterPoints = alterPoints;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(playerObjectId);
		writeQ(cooldownTimestamp);
		writeD(alterPoints);
	}
}
