package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * SM_RANKING_READY (opcode 437 / dec 0x01B5).
 * Enviado pelo servidor oficial Classic 5.0 em resposta a CM_SHOW_BLOCKLIST (0x00A8),
 * junto com SM_NPSHOP_GOODS_COUNT, SM_TIME_CHECK e SM_SECURITY_TOKEN.
 * Observado duas vezes no PCAP com corpo: 0xFFFFFFFF 0xFFFFFFFF 0xFFFFFFFF (12 bytes).
 * Provavelmente é uma notificação de "ranking não disponível" ou "lista pronta".
 *
 * @author Lost Academy Team / Durak
 */
public class SM_RANKING_READY extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		// Corpo exato do PCAP oficial Classic 5.0: 3 DWORDs = -1
		writeD(-1);
		writeD(-1);
		writeD(-1);
	}
}
