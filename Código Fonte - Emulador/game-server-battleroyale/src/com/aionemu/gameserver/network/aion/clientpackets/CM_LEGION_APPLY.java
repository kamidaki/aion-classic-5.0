package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.LegionApplicantService;

/**
 * Candidatura a uma Legion da busca, dec 0x119: [D Legion][S nome da Legion][C forma de entrada][S apresentação]; a resposta é o S 0x151 com a
 * Legion (Nova Pasta 2026-09-29 16:49 e 17:59, 8 de 8). O C é a forma de entrada da Legion na busca: 0 na Lost Academy e 1 na Connection Lost,
 * onde o personagem entrou direto, sem apresentação e sem S 0x151. A forma usada é a do servidor.
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
		readC(); // forma de entrada que o cliente viu na busca
		intro = readS();
	}

	@Override
	protected void runImpl() {
		LegionApplicantService.getInstance().apply(getConnection().getActivePlayer(), legionId, intro);
	}
}
