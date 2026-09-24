package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_CUSTOM_SETTINGS;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_CUSTOM_SETTINGS extends AionClientPacket {

	private int display;
	private int deny;

	public CM_CUSTOM_SETTINGS(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		if (getRemainingBytes() >= 4) {
			display = readUH();
			deny = readUH();
		} else if (getRemainingBytes() >= 2) {
			display = readUH();
		}
	}

	@Override
	protected void runImpl() {
		Player activePlayer = getConnection().getActivePlayer();
		if (activePlayer == null || activePlayer.getPlayerSettings() == null)
			return;

		activePlayer.getPlayerSettings().setDisplay(display);
		activePlayer.getPlayerSettings().setDeny(deny);

		PacketSendUtility.broadcastPacket(activePlayer, new SM_CUSTOM_SETTINGS(activePlayer), true);
	}
}
