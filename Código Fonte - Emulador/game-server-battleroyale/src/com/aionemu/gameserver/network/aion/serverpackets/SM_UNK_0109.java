package com.aionemu.gameserver.network.aion.serverpackets;

/**
 * Legacy alias for SM_TUTORIAL_GUIDE_STATE (0x0109).
 * @deprecated Use {@link SM_TUTORIAL_GUIDE_STATE} instead.
 */
@Deprecated
public class SM_UNK_0109 extends SM_TUTORIAL_GUIDE_STATE {
    public SM_UNK_0109() {
        super();
    }

    public SM_UNK_0109(int guideId, int state) {
        super(guideId, state);
    }
}
