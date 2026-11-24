package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.S_SERVER_ENV;
import com.aionemu.gameserver.network.aion.serverpackets.SM_VERSION_CHECK;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_VERSION_CHECK extends AionClientPacket {


	private int version;
	@SuppressWarnings("unused")
	private int subversion;
	@SuppressWarnings("unused")
	private int windowsEncoding;
	@SuppressWarnings("unused")
	private int windowsVersion;
	@SuppressWarnings("unused")
	private int windowsSubVersion;

	public CM_VERSION_CHECK(int opcode, Set<State> validStates) {
		super(opcode, validStates);
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
		sendPacket(new SM_VERSION_CHECK(version));
		sendPacket(new S_SERVER_ENV());
        // log.info("Client version: {}", version);
	}
}
