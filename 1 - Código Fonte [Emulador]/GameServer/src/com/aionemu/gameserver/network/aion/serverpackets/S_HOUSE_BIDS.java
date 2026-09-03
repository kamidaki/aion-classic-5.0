package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Resposta de Lista de Habitações em Leilão para o Cliente Classic 5.0.
 * Opcode: 0x0100 (S_AUCTION_LIST)
 */
public class S_HOUSE_BIDS extends AionServerPacket {

    private final boolean isFirst;
    private final boolean isLast;

    public S_HOUSE_BIDS() {
        this.isFirst = true;
        this.isLast = true;
    }

    public S_HOUSE_BIDS(boolean isFirst, boolean isLast) {
        this.isFirst = isFirst;
        this.isLast = isLast;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeC(isFirst ? 1 : 0);
        writeC(isLast ? 1 : 0);

        // Ultimo lance do jogador
        writeD(0); // listIndex
        writeQ(0); // kinah

        // Casa registrada para leilao pelo jogador
        writeD(0); // listIndex
        writeQ(0); // starting kinah

        // Quantidade de casas na lista de leilao
        writeH(0);
    }
}
