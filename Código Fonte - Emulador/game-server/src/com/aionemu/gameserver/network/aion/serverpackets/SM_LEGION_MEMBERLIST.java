package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.configs.network.NetworkConfig;
import com.aionemu.gameserver.model.team.legion.LegionMember;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_LEGION_MEMBERLIST extends AionServerPacket {

	private final boolean isFirst, isLast;
	private final List<LegionMember> legionMembers;

	public SM_LEGION_MEMBERLIST(List<LegionMember> legionMembers, boolean isFirst, boolean isLast) {
		this.legionMembers = legionMembers;
		this.isFirst = isFirst;
		this.isLast = isLast;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		int size = legionMembers.size();
		writeC(isFirst ? 1 : 0);
		writeH(isLast ? -size : size);
		for (LegionMember legionMember : legionMembers)
			writeLegionMember(legionMember);
	}

	protected void writeLegionMember(LegionMember legionMember) {
		writeD(legionMember.getObjectId());
		writeS(legionMember.getName());
		writeC(legionMember.getPlayerClass().getClassId());
		writeD(legionMember.getLevel());
		writeC(legionMember.getRank().getRankId());
		writeD(legionMember.getWorldId());
		writeC(legionMember.isOnline() ? 1 : 0);
		writeS(legionMember.getSelfIntro());
		writeS(legionMember.getNickname());
		writeD(legionMember.isOnline() ? 0 : legionMember.getLastOnlineEpochSeconds());
		// 5.0 (lista de 38 membros da Org Asmo, 16/09, sem sobra): servidor só de quem está online (23; 121 em Tiamaranta), 0 para os offline.
		// A 4.8 mandava casa e porta antes do servidor; na 5.0 as duas posições finais são outras.
		writeD(legionMember.isOnline() ? NetworkConfig.GAMESERVER_ID : 0);
		// doações do membro hoje e no total: os mesmos valores do S 0x156 (Chinike 1 e 126, Adnama 0 e 61). O servidor ainda não tem o sistema
		// de doação (C_GUILD 0x13/0x14), então os dois ficam em 0 para todos.
		writeD(0);
		writeD(0);
	}
}
