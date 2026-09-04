package com.aionemu.gameserver.network.chatserver;

import com.aionemu.commons.network.packet.BaseClientPacket;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class CsClientPacket extends BaseClientPacket<ChatServerConnection> implements Cloneable
{
    private static final Logger log = LoggerFactory.getLogger(CsClientPacket.class);
	
    protected CsClientPacket(int opcode) {
        super(opcode);
    }
	
    @Override
    public final void run() {
        try {
            runImpl();
        } catch (Throwable e) {
            log.warn("error handling ls (" + getConnection().getIP() + ") message " + this, e);
        }
    }
	
    protected void sendPacket(CsServerPacket msg) {
        getConnection().sendPacket(msg);
    }
	
    public CsClientPacket clonePacket() {
        try {
            return (CsClientPacket) super.clone();
        } catch (CloneNotSupportedException e) {
            return null;
        }
    }
}