package com.aionemu.gameserver.network.chatserver.clientpackets;

import com.aionemu.gameserver.network.chatserver.CsClientPacket;
import com.aionemu.gameserver.services.ChatService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CM_CS_PLAYER_AUTH_RESPONSE extends CsClientPacket
{
    protected static final Logger log = LoggerFactory.getLogger(CM_CS_PLAYER_AUTH_RESPONSE.class);
    private int playerId;
    private byte[] token;
	
    public CM_CS_PLAYER_AUTH_RESPONSE(int opcode) {
        super(opcode);
    }
	
    @Override
    protected void readImpl() {
        playerId = readD();
        int tokenLenght = readC();
        token = readB(tokenLenght);
    }
	
    @Override
    protected void runImpl() {
        ChatService.playerAuthed(playerId, token);
    }
}