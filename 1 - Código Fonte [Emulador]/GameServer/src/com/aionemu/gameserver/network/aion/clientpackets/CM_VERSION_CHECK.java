package com.aionemu.gameserver.network.aion.clientpackets;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;



public class CM_VERSION_CHECK extends AionClientPacket
{
	private int version;
	@SuppressWarnings("unused")
	private int subversion;
	@SuppressWarnings("unused")
	private int windowsEncoding;
	@SuppressWarnings("unused")
	private int windowsVersion;
	@SuppressWarnings("unused")
	private int windowsSubVersion;
	private int unk;

	private static Logger log = LoggerFactory.getLogger(CM_VERSION_CHECK.class);
	
	public CM_VERSION_CHECK(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}
	
	@Override
	protected void readImpl() {
		version = readH();
		subversion = readH();
		windowsEncoding = readD();
		windowsVersion = readD();
		windowsSubVersion = readD();
	}
	
	@Override
	protected void runImpl() {
		sendPacket(new S_VERSION_CHECK(version));
		sendPacket(new S_SERVER_ENV());
		log.info("version : " + this.version);
	}


}