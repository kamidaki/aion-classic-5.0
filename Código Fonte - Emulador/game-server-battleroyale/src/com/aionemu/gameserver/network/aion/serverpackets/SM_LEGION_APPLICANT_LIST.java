package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.model.team.legion.LegionApplicant;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x152, candidatos da Legion (aba Applicant), no login do membro: [H -n] e n x ([D personagem][S nome][C classe][C sexo][H nível]
 * [S apresentação][D hora]), pelo id do personagem (Nova Pasta 2026-09-29 16:49: [H 0] e [H -1] com o Schelp; 17:59: [H -3] com Sclepius,
 * Kodrarik e Sertralina, todos Asmodianos, sexo 0, 0 e 1; sobra 0 nos três).
 */
public class SM_LEGION_APPLICANT_LIST extends AionServerPacket {

	private final List<LegionApplicant> applicants;

	public SM_LEGION_APPLICANT_LIST(List<LegionApplicant> applicants) {
		this.applicants = applicants;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(-applicants.size());
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
