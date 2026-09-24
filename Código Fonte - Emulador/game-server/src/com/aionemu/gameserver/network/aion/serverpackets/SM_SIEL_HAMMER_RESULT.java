package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/** S_ITEM_CRUSH_RESULT: D status, H count, (D itemId, Q quantity, C bonus). */
public class SM_SIEL_HAMMER_RESULT extends AionServerPacket {
	public record Result(int itemId, long count, boolean bonus) { }
	private final int status;
	private final List<Result> results;
	public SM_SIEL_HAMMER_RESULT(int status, List<Result> results) {
		if (results.size() > 0x7FFF) throw new IllegalArgumentException("Hammer result vector too large");
		this.status = status;
		this.results = List.copyOf(results);
	}
	@Override
	protected void writeImpl(AionConnection connection) {
		writeD(status);
		writeH(results.size());
		for (var result : results) { writeD(result.itemId()); writeQ(result.count()); writeC(result.bonus() ? 1 : 0); }
	}
}
