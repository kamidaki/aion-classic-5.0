package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Opcode wire 0x0181 (dec 0x00F3) - CM_RANKING_SUBSCRIBE
 * Sent by client on login with [D tipo][C isLocalServer].
 */
public class CM_RANKING_SUBSCRIBE extends AionClientPacket {

	private static final Logger log = LoggerFactory.getLogger(CM_RANKING_SUBSCRIBE.class);

	private int rankingType;
	private int isLocalServer;

	public CM_RANKING_SUBSCRIBE(int opcode, State state, State... restStates) {
		super(opcode, state, restStates);
	}

	public CM_RANKING_SUBSCRIBE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		rankingType = readD();
		isLocalServer = readC();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null) {
			log.debug("Player " + player.getName() + " subscribed to ranking type " + rankingType + ", local=" + isLocalServer);
		}
	}
}
