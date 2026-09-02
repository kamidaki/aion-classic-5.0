package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.model.EmotionType;
import com.aionemu.gameserver.model.actions.PlayerMode;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.state.CreatureState;
import com.aionemu.gameserver.model.templates.windstreams.WindstreamPath;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.S_ACTION;
import com.aionemu.gameserver.network.aion.serverpackets.S_POLYMORPH;
import com.aionemu.gameserver.network.aion.serverpackets.S_WIND_PATH_RESULT;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * CM_WIND_PATH (0x0046 wire 0x13C)
 * Na entrada do mundo o cliente 5.0 envia este pacote com 0 bytes de payload (notificacao/query).
 * Quando o payload e vazio, o servidor oficial nao responde nada (silencio conforme PCAP).
 */
public class CM_WIND_PATH extends AionClientPacket {

    private int teleportId;
    private int distance;
    private int state;
    private boolean hasPayload;

    public CM_WIND_PATH(int opcode, State state, State... restStates) {
        super(opcode, state, restStates);
    }

    @Override
    protected void readImpl() {
        if (getRemainingBytes() >= 12) {
            teleportId = readD();
            distance = readD();
            state = readD();
            hasPayload = true;
        } else if (getRemainingBytes() > 0) {
            readB(getRemainingBytes());
            hasPayload = false;
        } else {
            hasPayload = false;
        }
    }

    @Override
    protected void runImpl() {
        if (!hasPayload) {
            // Corpo vazio medido no PCAP oficial 5.0 (01_Login_World) - servidor oficial permanece em silencio.
            return;
        }
        Player player = getConnection().getActivePlayer();
        if (player == null) {
            return;
        }
        switch (state) {
            case 0:
            case 7:
            case 8:
                if (state == 7) {
                    PacketSendUtility.broadcastPacket(player, new S_ACTION(player, EmotionType.WINDSTREAM_START_BOOST, 0, 0), true);
                } else if (state == 8) {
                    PacketSendUtility.broadcastPacket(player, new S_ACTION(player, EmotionType.WINDSTREAM_END_BOOST, 0, 0), true);
                }
                PacketSendUtility.sendPacket(player, new S_WIND_PATH_RESULT(state, 1));
                break;
            case 1:
                if (player.isInPlayerMode(PlayerMode.WINDSTREAM)) {
                    return;
                }
                player.setPlayerMode(PlayerMode.WINDSTREAM, new WindstreamPath(teleportId, distance));
                player.unsetState(CreatureState.ACTIVE);
                player.unsetState(CreatureState.GLIDING);
                player.setState(CreatureState.FLYING);
                PacketSendUtility.broadcastPacket(player, new S_ACTION(player, EmotionType.WINDSTREAM, teleportId, distance), true);
                player.getLifeStats().triggerFpRestore();
                break;
            case 2:
            case 3:
            case 4:
                if (!player.isInPlayerMode(PlayerMode.WINDSTREAM)) {
                    return;
                }
                player.unsetState(CreatureState.FLYING);
                player.setState(CreatureState.ACTIVE);
                if (state == 2) {
                    player.setState(CreatureState.GLIDING);
                    player.getLifeStats().triggerFpReduce();
                }
                if (state == 4 || player.isTransformed()) {
                    player.setState(CreatureState.GLIDING);
                    player.getLifeStats().triggerFpReduce();
                    PacketSendUtility.broadcastPacketAndReceive(player, new S_POLYMORPH(player, player.getTransformedModelId(), true, player.getTransformedItemId()));
                    PacketSendUtility.broadcastPacketAndReceive(player, new S_POLYMORPH(player, true));
                    player.getEffectController().updatePlayerEffectIcons();
                }
                PacketSendUtility.broadcastPacket(player, new S_ACTION(player, state == 2 ? EmotionType.WINDSTREAM_END : EmotionType.WINDSTREAM_EXIT, 0, 0), true);
                player.getGameStats().updateStatsAndSpeedVisually();
                PacketSendUtility.sendPacket(player, new S_WIND_PATH_RESULT(state, 1));
                player.unsetPlayerMode(PlayerMode.WINDSTREAM);
                break;
        }
    }
}
