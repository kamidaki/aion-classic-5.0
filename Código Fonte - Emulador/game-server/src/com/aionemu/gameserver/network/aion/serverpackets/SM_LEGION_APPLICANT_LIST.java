package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.model.team.legion.LegionApplicant;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x152, candidatos da Legion (aba Applicant), no login do membro: [H 0] sem candidatos; com o Schelp, [H 0xFFFF] e ([D personagem][S nome]
 * [C classe][C sexo][H nível][S apresentação][D hora]) (Nova Pasta 2026-09-29 16:49, 40 b, sobra 0).
 * <p>
 * PENDENTE_DE_COMPROVACAO: o H com mais de um candidato (0xFFFF com um só) e se o C depois da classe é o sexo ou a raça (os dois valem 1 no
 * Schelp).
 */
public class SM_LEGION_APPLICANT_LIST extends AionServerPacket {

	private final List<LegionApplicant> applicants;

	public SM_LEGION_APPLICANT_LIST(List<LegionApplicant> applicants) {
		this.applicants = applicants;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(applicants.isEmpty() ? 0 : 0xFFFF);
		for (LegionApplicant applicant : applicants) {
			writeD(applicant.playerId());
			writeS(applicant.name());
			writeC(applicant.playerClass());
			writeC(applicant.gender());
			writeH(applicant.level());
			writeS(applicant.intro());
			writeD(applicant.applyTime());
		}
	}
}
