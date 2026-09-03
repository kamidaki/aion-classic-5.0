package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Pacote cru: opcode e corpo vindos da captura oficial, sem interpretacao.
 *
 * So existe para o experimento do {@link com.aionemu.gameserver.services.player.RajadaOficial} --
 * nao e forma de implementar protocolo. Quando um destes pacotes provar ser necessario, ele ganha
 * uma classe de verdade, com os campos lidos.
 */
public class S_RAJADA_OFICIAL extends AionServerPacket {

    private final byte[] corpo;

    public S_RAJADA_OFICIAL(int opcode, byte[] corpo) {
        super(opcode);
        this.corpo = corpo;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeB(corpo);
    }
}
