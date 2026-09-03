package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.S_HOUSE_BIDS;
import com.aionemu.gameserver.utils.PacketSendUtility;

import java.util.Set;

/**
 * Requisicao da Lista de Leilao de Casas (C_REQUEST_AUCTION_LIST).
 * Wire Opcode: 0x01A8 (Dec: 0x00DA)
 */
public class CM_GET_HOUSE_BIDS extends AionClientPacket {

    public CM_GET_HOUSE_BIDS(int opcode, State state, State... restStates) {
        super(opcode, state, restStates);
    }

    @Override
    protected void readImpl() {
        // Sem payload adicional na requisicao base
    }

    @Override
    protected void runImpl() {
        Player player = getConnection().getActivePlayer();
        if (player == null) {
            return;
        }
        PacketSendUtility.sendPacket(player, new S_HOUSE_BIDS(true, true));
    }
}
