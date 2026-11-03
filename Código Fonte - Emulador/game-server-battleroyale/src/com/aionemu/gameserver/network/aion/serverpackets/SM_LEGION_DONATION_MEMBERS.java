package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x156, pontos de produção por membro: [H n] n x ([D objeto][D pontos hoje][D pontos total]) [C 1].
 * <p>
 * No login vem a Legion inteira (Org Asmo, 38 membros, 459 b); depois de cada produção, só quem produziu (15 b). O C final foi 1 nas 16 variantes.
 */
public class SM_LEGION_DONATION_MEMBERS extends AionServerPacket {

	public record Entry(int objectId, int pointsToday, int pointsTotal) {}

	private final List<Entry> entries;

	public SM_LEGION_DONATION_MEMBERS(List<Entry> entries) {
		this.entries = entries;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(entries.size());
		for (Entry entry : entries) {
			writeD(entry.objectId());
			writeD(entry.pointsToday());
			writeD(entry.pointsTotal());
		}
		writeC(1);
	}
}
