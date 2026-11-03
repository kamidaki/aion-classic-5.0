package com.aionemu.gameserver.network.aion.serverpackets;

/**
 * Legacy alias for SM_ZONE_HAZARD_LIST (0x0170).
 * @deprecated Use {@link SM_ZONE_HAZARD_LIST} instead.
 */
@Deprecated
public class SM_UNK_0170 extends SM_ZONE_HAZARD_LIST {
    public SM_UNK_0170() {
        super();
    }

    public SM_UNK_0170(int hazardCount) {
        super(hazardCount);
    }
}
