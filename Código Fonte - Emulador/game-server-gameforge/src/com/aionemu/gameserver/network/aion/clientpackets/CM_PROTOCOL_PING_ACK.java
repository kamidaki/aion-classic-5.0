package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Pacote C_Opcode 0x0122 (Fio 0x01D0) - 10 bytes.
 * Resposta de handshake/ping de versao de protocolo ("2/0/0\0").
 * Payload oficial medido: f1 fc 38 76 32 2f 30 2f 30 00.
 */
public class CM_PROTOCOL_PING_ACK extends AionClientPacket {

    private static final Logger log = LoggerFactory.getLogger(CM_PROTOCOL_PING_ACK.class);

    private int token;
    private String version;

    public CM_PROTOCOL_PING_ACK(int opcode, Set<State> validStates) {
        super(opcode, validStates);
    }

    public CM_PROTOCOL_PING_ACK(int opcode, State state, State... restStates) {
        super(opcode, state, restStates);
    }

    @Override
    protected void readImpl() {
        if (getRemainingBytes() >= 4) {
            token = readD();
            if (getRemainingBytes() > 0) {
                byte[] strBytes = readB(getRemainingBytes());
                int len = strBytes.length;
                if (len > 0 && strBytes[len - 1] == 0) {
                    len--;
                }
                version = new String(strBytes, 0, len, java.nio.charset.StandardCharsets.US_ASCII);
            }
        } else {
            readB(getRemainingBytes());
        }
    }

    @Override
    protected void runImpl() {
        if (log.isDebugEnabled()) {
            log.debug("[CM_PROTOCOL_PING_ACK] token=0x{} version={}", Integer.toHexString(token), version);
        }
    }
}
