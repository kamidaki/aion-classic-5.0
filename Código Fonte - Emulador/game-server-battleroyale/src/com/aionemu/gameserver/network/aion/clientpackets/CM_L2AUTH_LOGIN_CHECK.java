package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.loginserver.LoginServer;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_L2AUTH_LOGIN_CHECK extends AionClientPacket {

	private int playOk2;
	private int playOk1;
	private int accountId;
	private int loginOk;

	public CM_L2AUTH_LOGIN_CHECK(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_L2AUTH_LOGIN_CHECK(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		playOk2 = readD();
		if (getOpcode() == 0x182) { // 5.0 HQ_LOGIN
			accountId = readD();
			if (getRemainingBytes() >= 8) {
				readD();
				readD();
			}
			if (getRemainingBytes() > 0) {
				readB(getRemainingBytes());
			}
		} else {
			playOk1 = readD();
			accountId = readD();
			loginOk = readD();
			if (getRemainingBytes() >= 8) {
				readD();
				readD();
			}
		}
	}

	@Override
	protected void runImpl() {
		LoginServer.getInstance().registerLoginRequest(accountId, getConnection(), loginOk, playOk1, playOk2);
	}
}
