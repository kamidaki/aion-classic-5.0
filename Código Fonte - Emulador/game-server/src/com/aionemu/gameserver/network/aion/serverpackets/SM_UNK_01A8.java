package com.aionemu.gameserver.network.aion.serverpackets;

/**
 * @deprecated Use {@link SM_AVATAR_PRESENCE_SYNC} instead.
 */
@Deprecated
public class SM_UNK_01A8 extends SM_AVATAR_PRESENCE_SYNC {
    public SM_UNK_01A8(int objectId) {
        super(objectId);
    }

    public SM_UNK_01A8() {
        super(0);
    }
}
