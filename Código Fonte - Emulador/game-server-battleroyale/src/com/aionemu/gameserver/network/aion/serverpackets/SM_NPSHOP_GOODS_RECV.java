package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * [S_RESPONSE_NPSHOP_GOODS_RECV] (0x10D): resposta a cada C_SA_CONFIRMGOODS (0x9E), {@code [Q id][D resultado]}. A captura oficial só tem
 * sucesso (resultado 0, 4 de 4). O botão "Receber tudo" do mailbox_dialog manda o próximo 0x9E só depois desta resposta, então a falha
 * também precisa ser respondida; o código 1 não foi visto em captura.
 */
public class SM_NPSHOP_GOODS_RECV extends AionServerPacket {

	public static final int SUCCESS = 0;
	public static final int FAILURE = 1;

	private final long goodsId;
	private final int result;

	public SM_NPSHOP_GOODS_RECV(long goodsId, int result) {
		this.goodsId = goodsId;
		this.result = result;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeQ(goodsId);
		writeD(result);
	}
}
