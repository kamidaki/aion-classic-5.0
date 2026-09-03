package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * CM_INIT_LEVEL (0x0056 wire 0x12C).
 * Notificacao de inicializacao de level enviada pelo cliente Classic 5.0 (payload [INIT] de 81 bytes).
 */
public class CM_INIT_LEVEL extends AionClientPacket {
    public CM_INIT_LEVEL(int opcode, State state, State... restStates) {
        super(opcode, state, restStates);
    }

    @Override
    protected void readImpl() {
        readB(getRemainingBytes());
    }

    @Override
    protected void runImpl() {
        // Notificacao de inicializacao de level recebida com sucesso
    }
}
