package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.model.gameobjects.BlackCloudGoods;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * [S_RESPONSE_NPSHOP_GOODS_LIST] (0x10C): aba "Black Cloud" da janela do correio, resposta ao C_SA_GOODSLIST (0x9D).
 * <p>
 * Layout medido em 06_Sistemas_Novos_Black_Cloud_Mail (4 mercadorias, 589 b) e em Outros/express (lista vazia, 7 b):
 * {@code [D 0][C 1][H n]} e, por mercadoria, {@code [Q id][S nome][3 b 0][Q reembolso][D chegada][12 b 0][C 1][H 1][D item][Q qtd]
 * [D 0][D 0x7FFF][D 2][D 0][D 0x50]}. Os campos sem nome vieram iguais nas 4 mercadorias e são escritos como na captura. O Q de reembolso
 * é a coluna "tempo restante de reembolso" do mailbox_dialog; o oficial manda {@code 0 - agora} (negativo) para mercadoria sem
 * reembolso, que é o único caso do emulador.
 */
public class SM_NPSHOP_GOODS_LIST extends AionServerPacket {

	public static final int STATIC_BODY_SIZE = 7;

	private final List<BlackCloudGoods> goods;

	public SM_NPSHOP_GOODS_LIST(List<BlackCloudGoods> goods) {
		this.goods = goods;
	}

	public static int bodySize(BlackCloudGoods goods) {
		return 70 + byteLengthForString(goods.name());
	}

	@Override
	protected void writeImpl(AionConnection con) {
		long now = System.currentTimeMillis() / 1000;
		writeD(0);
		writeC(1);
		writeH(goods.size());
		for (BlackCloudGoods g : goods) {
			writeQ(g.id());
			writeS(g.name());
			writeB(new byte[3]);
			writeQ(-now); // tempo restante de reembolso: sem reembolso no emulador
			writeD(g.registerTime());
			writeB(new byte[12]);
			writeC(1);
			writeH(1); // um item por mercadoria
			writeD(g.itemId());
			writeQ(g.itemCount());
			writeD(0);
			writeD(0x7FFF);
			writeD(2);
			writeD(0);
			writeD(0x50);
		}
	}
}
