package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Liga e desliga uma zona PvP nomeada do mapa (0x187, decodificado).
 * <p>
 * Layout medido nas capturas oficiais 5.0 de Tiamaranta: string UTF-16 terminada em zero, <b>sem</b> prefixo de
 * tamanho, seguida de um byte 0/1. Exemplo de 57 bytes:
 * {@code "LDF4b_TowerWar_PvPArea_4413\0" + 01}.
 * <p>
 * O nome vem do {@code client_world_ldf4b.xml}; 1 liga (torre vulneravel, PvP liberado na area), 0 desliga.
 *
 * @author Lost Academy Team & Durak
 */
public class SM_CAMP_PVP_ZONE extends AionServerPacket {

	private final String zoneName;
	private final boolean enabled;

	public SM_CAMP_PVP_ZONE(String zoneName, boolean enabled) {
		this.zoneName = zoneName;
		this.enabled = enabled;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeS(zoneName);
		writeC(enabled ? 1 : 0);
	}
}
