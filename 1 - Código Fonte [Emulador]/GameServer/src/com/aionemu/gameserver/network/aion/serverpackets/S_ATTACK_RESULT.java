package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Servidor Oficial Classic 5.0: Opcode dec=0x0072 wire=0x01E2 (2 bytes)
 * Notifica o cliente do resultado / parada de ataque básico.
 */
public class S_ATTACK_RESULT extends AionServerPacket {

    private final int message;
    private final int attackCount;

    public static S_ATTACK_RESULT TARGET_IN_DIFFERENT_AREA(int count) {
        return new S_ATTACK_RESULT(1, count);
    }

    public static S_ATTACK_RESULT STOP_INVALID_TARGET(int count) {
        return new S_ATTACK_RESULT(2, count);
    }

    public static S_ATTACK_RESULT TARGET_TOO_FAR_AWAY(int count) {
        return new S_ATTACK_RESULT(4, count);
    }

    public static S_ATTACK_RESULT STOP_OBSTACLE_IN_THE_WAY(int count) {
        return new S_ATTACK_RESULT(5, count);
    }

    public static S_ATTACK_RESULT STOP_TOO_CLOSE_TO_ATTACK(int count) {
        return new S_ATTACK_RESULT(6, count);
    }

    public static S_ATTACK_RESULT STOP_WITHOUT_MESSAGE(int count) {
        return new S_ATTACK_RESULT(7, count);
    }

    public S_ATTACK_RESULT(int message, int attackCount) {
        this.message = message;
        this.attackCount = attackCount;
    }

    @Override
    protected void writeImpl(AionConnection con) {
        writeC(message);
        writeC(attackCount);
    }
}
