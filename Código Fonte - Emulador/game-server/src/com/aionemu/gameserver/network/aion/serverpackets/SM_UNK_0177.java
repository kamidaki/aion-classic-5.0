package com.aionemu.gameserver.network.aion.serverpackets;

/**
 * Legacy alias for SM_EQUIPMENT_VIEW_STATE (0x0177).
 * @deprecated Use {@link SM_EQUIPMENT_VIEW_STATE} instead.
 */
@Deprecated
public class SM_UNK_0177 extends SM_EQUIPMENT_VIEW_STATE {
    public SM_UNK_0177() {
        super();
    }

    public SM_UNK_0177(int viewType, int count, int state) {
        super(viewType, count, state);
    }
}
