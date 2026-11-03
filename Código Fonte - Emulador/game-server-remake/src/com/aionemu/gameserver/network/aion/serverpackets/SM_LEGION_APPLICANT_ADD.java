package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.team.legion.LegionApplicant;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x153, candidato novo para o membro online: [D personagem][S nome][C classe][C sexo][H nível][S apresentação][D hora], a mesma entrada do
 * S 0x152 (Nova Pasta 2026-09-29 18:08: a candidatura da Kimmie chegou ao Kodra online, 32 b, sem mensagem).
 */
public class SM_LEGION_APPLICANT_ADD extends AionServerPacket {

	private final LegionApplicant applicant;

	public SM_LEGION_APPLICANT_ADD(LegionApplicant applicant) {
		this.applicant = applicant;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(applicant.playerId());
		writeS(applicant.name());
		writeC(applicant.playerClass());
		writeC(applicant.gender());
		writeH(applicant.level());
		writeS(applicant.intro());
		writeD(applicant.applyTime());
	}
}
