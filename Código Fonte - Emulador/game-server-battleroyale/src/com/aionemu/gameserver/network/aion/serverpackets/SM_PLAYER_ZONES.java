package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * SM_PLAYER_ZONES (opcode 215 / 0xD7).
 * Enviado pelo servidor oficial Classic 5.0 após SM_ABNORMAL_STATE e antes de SM_MOTION,
 * durante o fluxo de resposta ao CM_LEVEL_READY. Carrega informações de penalidade de
 * habilidade de zona (skill penalty region) para o próprio jogador.
 *
 * Formato observado no PCAP oficial Classic 5.0 (11 bytes de corpo):
 *   writeH(flags)         — sempre 0 nas capturas conhecidas
 *   writeD(penaltyRegionA)— hash do nome da zona de penalidade (0 = sem penalidade)
 *   writeD(penaltyRegionB)— mesmo valor duplicado (convenção do servidor oficial)
 *
 * @author Lost Academy Team / Durak
 */
public class SM_PLAYER_ZONES extends AionServerPacket {

	private final int penaltyRegionId;

	/**
	 * @param penaltyRegionId hash da zona de penalidade de habilidade (0 = sem penalidade)
	 */
	public SM_PLAYER_ZONES(int penaltyRegionId) {
		this.penaltyRegionId = penaltyRegionId;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(0);                 // flags / tipo (sempre 0)
		writeD(penaltyRegionId);  // id da região de penalidade (A)
		writeD(penaltyRegionId);  // id da região de penalidade (B, mesmo valor)
	}
}
