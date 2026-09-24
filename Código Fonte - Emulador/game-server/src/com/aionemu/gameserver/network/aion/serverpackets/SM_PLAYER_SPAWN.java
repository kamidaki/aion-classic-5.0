package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * SM_PLAYER_SPAWN / S_WORLD (Opcode 15 / 0x000F).
 * Payload de 42 bytes oficial do Classic 5.0 para inicialização e carregamento do mapa/mundo.
 *
 * @author Lost Academy Team & Durak
 */
public class SM_PLAYER_SPAWN extends AionServerPacket {

	/**
	 * Player that is entering game.
	 */
	private final Player player;

	public SM_PLAYER_SPAWN(Player player) {
		this.player = player;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(player.getWorldId());
		writeD(player.getWorldId());
		writeB(new byte[5]);
		writeF(player.getX());
		writeF(player.getY());
		writeF(player.getZ());
		writeC(player.getHeading());
		writeC(0x14);
		writeB(new byte[15]);
	}

}
