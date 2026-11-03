package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.LegionApplicantService;

/**
 * Busca de Legion, dec 0x118: [C 0][H 0] lista geral, [C 1][S texto] pelo nome (Legion Name) e [C 2][S texto] pela apresentação (Legion
 * Introduction); a resposta é o S 0x150 (Nova Pasta 2026-09-29 16:49, 5 de 5; 17:59, 6 de 6: "Lost" e "lost" deram as mesmas 9 Legions com o nome
 * contendo o texto, de nível 1 a 5; 18:08: "lost" pela apresentação deu a lista vazia [H 0][C 1]). PENDENTE_DE_COMPROVACAO: o H da lista geral
 * (sempre 0).
 */
public class CM_LEGION_SEARCH extends AionClientPacket {

	private int mode;
	private String name;

	public CM_LEGION_SEARCH(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		mode = readUC();
		if (mode == 1 || mode == 2)
			name = readS();
		else
			readH();
	}

	@Override
	protected void runImpl() {
		LegionApplicantService.getInstance().search(getConnection().getActivePlayer(), mode == 0 ? null : name, mode == 2);
	}
}
