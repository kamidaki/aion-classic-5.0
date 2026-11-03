package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Resultado da escolha numa caixa selectable (S_SELECT_DISASSEMBLY_ITEM_RESULT, 0x105 na 5.0): [D obj][D 0][C resultado].
 * Subida 1-60 oficial: {@link #OK} com o objeto da caixa depois de entregar o item; {@link #CANCELED} com objeto 0 quando o jogador fecha a
 * janela (o cliente manda C_USE_ITEM com objeto 0) ou interrompe a barra de uso.
 *
 * @author Lost Academy Team & Durak
 */
public class SM_SECONDARY_SHOW_DECOMPOSABLE extends AionServerPacket {

	public static final int OK = 0;
	public static final int CANCELED = 3;

	private final int objectId;
	private final int result;

	public SM_SECONDARY_SHOW_DECOMPOSABLE(int objectId, int result) {
		this.objectId = objectId;
		this.result = result;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(objectId);
		writeD(0);
		writeC(result);
	}

}
