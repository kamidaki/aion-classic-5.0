package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Lista de zonas nomeadas do mapa com o estado de cada uma (0x19D, decodificado): {@code [H n][n x (S zona, C estado)]}.
 * <p>
 * Medido na captura oficial 5.0 de 2026-09-16: ao entrar em Tiamaranta Mesa vem em dois pacotes (48 + 26 zonas, 2422 e
 * 924 bytes), sem sobra. E o estado completo de que o {@link SM_CAMP_PVP_ZONE} (0x187) e a atualizacao de uma zona so.
 *
 * @author Lost Academy Team & Durak
 */
public class SM_ZONE_STATE_LIST extends AionServerPacket {

	/** Nome da zona e estado (0/1). */
	public record ZoneState(String name, int state) {
	}

	private final List<ZoneState> zones;

	public SM_ZONE_STATE_LIST(List<ZoneState> zones) {
		this.zones = zones;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(zones.size());
		for (ZoneState zone : zones) {
			writeS(zone.name());
			writeC(zone.state());
		}
	}
}
