package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * SM_WORLD_SCENE_STATUS (Opcode 0x008B / 139 dec).
 * Comanda o cliente Classic 5.0 a fechar a cena/HUD de carregamento e entrar no modo de jogo.
 *
 * @author Lost Academy Team & Durak
 */
public class SM_WORLD_SCENE_STATUS extends AionServerPacket {

	private final int type;
	private final int sceneId;
	private final int unk;

	public SM_WORLD_SCENE_STATUS(int type, int sceneId, int unk) {
		this.type = type;
		this.sceneId = sceneId;
		this.unk = unk;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(type);
		writeD(sceneId);
		writeD(unk);
	}
}
