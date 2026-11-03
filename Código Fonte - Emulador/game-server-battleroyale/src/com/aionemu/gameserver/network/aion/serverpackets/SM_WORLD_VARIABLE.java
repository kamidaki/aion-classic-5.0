package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Variavel de mundo do mapa (0x180, decodificado): {@code [D mapa][S nome][D valor]}.
 * <p>
 * Medido na captura oficial 5.0 de 2026-09-16 ao entrar em Tiamaranta Mesa: {@code disable_pvp}, {@code disable_pvp_e}
 * e {@code disable_pvp_w} com valor 1 (32 e 36 bytes). Na de 2026-09-15 vem ainda {@code DOWN_PVP_Mark} = -1.
 *
 * @author Lost Academy Team & Durak
 */
public class SM_WORLD_VARIABLE extends AionServerPacket {

	private final int worldId;
	private final String name;
	private final int value;

	public SM_WORLD_VARIABLE(int worldId, String name, int value) {
		this.worldId = worldId;
		this.name = name;
		this.value = value;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(worldId);
		writeS(name);
		writeD(value);
	}
}
