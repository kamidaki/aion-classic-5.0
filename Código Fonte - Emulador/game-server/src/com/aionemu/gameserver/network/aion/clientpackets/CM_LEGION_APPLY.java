package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.LegionApplicantService;

/**
 * Candidatura a uma Legion da busca, dec 0x119: [D Legion][S nome da Legion][C 0][S apresentação]; a resposta é o S 0x151 com a Legion
 * (Nova Pasta 2026-09-29 16:49, 3 de 3). PENDENTE_DE_COMPROVACAO: o C depois do nome (sempre 0).
 */
public class CM_LEGION_APPLY extends AionClientPacket {

	private int legionId;
	private String intro;

	public CM_LEGION_APPLY(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		legionId = readD();
		readS(); // nome da Legion
		readC();
		intro = readS();
	}

	@Override
	protected void runImpl() {
		LegionApplicantService.getInstance().apply(getConnection().getActivePlayer(), legionId, intro);
	}
}
