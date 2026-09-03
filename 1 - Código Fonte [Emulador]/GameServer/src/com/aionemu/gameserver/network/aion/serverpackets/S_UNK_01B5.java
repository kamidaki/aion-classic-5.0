package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Opcode 0x01B5 — semantica ainda desconhecida, conteudo constante.
 *
 * Nas duas capturas oficiais 5.0 (personagem antigo e recem-criado) ele aparece sempre com os
 * mesmos 12 bytes, todos 0xFF, e sempre logo depois de um `S_NPSHOP_GOODS_COUNT` (0x010A, quatro
 * zeros) — provavelmente tres campos "sem valor". Faz parte do trecho final que antecede o
 * `CM_LEVEL_READY` do cliente:
 *
 *     0x0089 -> 0x010A -> 0x01B5 -> 0x0027 (sincronia de relogio) -> CM_LEVEL_READY
 *
 * Enquanto nao houver evidencia do significado dos campos, o pacote reproduz o que a captura
 * mostra. Renomear quando alguem descobrir o que ele carrega.
 */
public class S_UNK_01B5 extends AionServerPacket {

    @Override
    protected void writeImpl(AionConnection con) {
        writeD(0xFFFFFFFF);
        writeD(0xFFFFFFFF);
        writeD(0xFFFFFFFF);
    }
}
