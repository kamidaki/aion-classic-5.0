package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_MACRO_RESULT;
import com.aionemu.gameserver.services.player.PlayerService;

/**
 * @author Lost Academy Team & Durak
 */
public class CM_MACRO_DELETE extends AionClientPacket {

	/**
	 * Macro id that has to be deleted
	 */
	private int macroPosition;

	/**
	 * Constructs new client packet instance.
	 * 
	 * @param opcode
	 */
	public CM_MACRO_DELETE(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	/**
	 * Reading macro id
	 */
	@Override
	protected void readImpl() {
		macroPosition = readUC();
	}

	@Override
	protected void runImpl() {
		PlayerService.removeMacro(getConnection().getActivePlayer(), macroPosition);
		sendPacket(SM_MACRO_RESULT.SM_MACRO_DELETED);
	}
}
