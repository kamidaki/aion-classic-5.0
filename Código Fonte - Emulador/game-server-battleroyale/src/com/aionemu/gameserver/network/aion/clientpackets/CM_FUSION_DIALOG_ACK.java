package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Pacote C_Opcode 0x0005 (Fio 0x00FF) - 7 bytes.
 * Confirmacao/Acao enviada pelo cliente durante dialogos de fusao de armas.
 * Payload oficial medido: 08 00 00 00 00 00 00 (action=8, param=0, sub=0).
 */
public class CM_FUSION_DIALOG_ACK extends AionClientPacket {

    private static final Logger log = LoggerFactory.getLogger(CM_FUSION_DIALOG_ACK.class);

    private int actionId;
    private int param;
    private int subParam;

    public CM_FUSION_DIALOG_ACK(int opcode, Set<State> validStates) {
        super(opcode, validStates);
    }

    public CM_FUSION_DIALOG_ACK(int opcode, State state, State... restStates) {
        super(opcode, state, restStates);
    }

    @Override
    protected void readImpl() {
        if (getRemainingBytes() >= 7) {
            actionId = readD();
            param = readH();
            subParam = readC();
        } else {
            readB(getRemainingBytes());
        }
    }

    @Override
    protected void runImpl() {
        Player player = getConnection().getActivePlayer();
        if (player == null || !player.isSpawned()) {
            return;
        }
        if (log.isDebugEnabled()) {
            log.debug("[CM_FUSION_DIALOG_ACK] Player {} actionId={} param={} subParam={}",
                    player.getName(), actionId, param, subParam);
        }
    }
}
