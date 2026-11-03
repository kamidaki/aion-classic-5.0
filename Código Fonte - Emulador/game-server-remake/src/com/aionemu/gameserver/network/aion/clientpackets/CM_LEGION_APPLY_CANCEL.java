package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.LegionApplicantService;

/**
 * Cancelamento da candidatura, dec 0x11A: [D Legion]; a resposta é o S 0x151 vazio (Nova Pasta 2026-09-29 16:49, 1 de 1).
 */
public class CM_LEGION_APPLY_CANCEL extends AionClientPacket {

	private int legionId;

	public CM_LEGION_APPLY_CANCEL(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		legionId = readD();
	}

	@Override
	protected void runImpl() {
		LegionApplicantService.getInstance().cancel(getConnection().getActivePlayer(), legionId);
	}
}
