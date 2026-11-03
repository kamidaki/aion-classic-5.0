package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x150, resultado da busca de Legion (C 0x118): [H n] n x ([D Legion][S nome][S líder][C nível][D membros][S apresentação][C forma de entrada]
 * [H nível mínimo][D atividade de campanha][D atividade da Legion][D nível de crescimento]) [C última página].
 * <p>
 * Nova Pasta 2026-09-29 16:49: a busca pelo nome deu a Lost Academy (77 b, [C 1] no fim); a lista geral veio em dois pacotes, 34 e 16 Legions,
 * com [C 0] e [C 1] no fim (sobra 0 nos quatro).
 */
public class SM_LEGION_SEARCH_LIST extends AionServerPacket {

	public record Entry(int legionId, String name, String leader, int level, int members, String intro, int joinType, int joinMinLevel,
		int campaignActivity, int legionActivity, int growthLevel) {}

	private final List<Entry> entries;
	private final boolean lastPage;

	public SM_LEGION_SEARCH_LIST(List<Entry> entries, boolean lastPage) {
		this.entries = entries;
		this.lastPage = lastPage;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(entries.size());
		for (Entry entry : entries) {
			writeD(entry.legionId());
			writeS(entry.name());
			writeS(entry.leader());
			writeC(entry.level());
			writeD(entry.members());
			writeS(entry.intro());
			writeC(entry.joinType());
			writeH(entry.joinMinLevel());
			writeD(entry.campaignActivity());
			writeD(entry.legionActivity());
			writeD(entry.growthLevel());
		}
		writeC(lastPage ? 1 : 0);
	}
}
