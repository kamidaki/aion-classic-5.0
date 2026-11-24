package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.Map;

/**
 * @deprecated Use {@link SM_SIEL_ANVIL_POINTS_INFO} instead.
 */
@Deprecated
public class SM_UNK_01AB extends SM_SIEL_ANVIL_POINTS_INFO {
    public SM_UNK_01AB() {
        super();
    }

    public SM_UNK_01AB(Map<Integer, Integer> points) {
        super(points);
    }
}
