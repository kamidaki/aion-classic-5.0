package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_PONG;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_MAY_QUIT extends AionClientPacket {

	private static final Logger log = LoggerFactory.getLogger(CM_MAY_QUIT.class);

	/**
	 * @param opcode
	 */
	public CM_MAY_QUIT(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		if (getRemainingBytes() > 0) {
			readH();
		}
	}

	@Override
	protected void runImpl() {
		log.debug("[MAY_QUIT_PACKET] CM_MAY_QUIT recebido do cliente! Respondendo com SM_PONG");
		sendPacket(new SM_PONG());
	}
}
