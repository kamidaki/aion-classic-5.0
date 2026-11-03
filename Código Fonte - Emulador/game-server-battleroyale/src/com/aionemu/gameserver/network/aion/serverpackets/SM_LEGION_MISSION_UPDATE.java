package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S 0x15D, progresso de missão da Legion: [H n] n x ([Q instância][C estado][D valor][20 b 0]).
 * <p>
 * Ação em andamento: estado 1 e o progresso (35 b, 153 nas capturas). Ação concluída: estado 2 e o progresso, seguida da missão com estado 1 e
 * as ações concluídas (68 b; Lost Academy 22/09: 1 e depois 3, quando veio a recompensa do estágio).
 */
public class SM_LEGION_MISSION_UPDATE extends AionServerPacket {

	public record Entry(long instanceId, int state, int value) {}

	private final List<Entry> entries;

	public SM_LEGION_MISSION_UPDATE(List<Entry> entries) {
		this.entries = entries;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(entries.size());
		for (Entry entry : entries) {
			writeQ(entry.instanceId());
			writeC(entry.state());
			writeD(entry.value());
			writeB(new byte[20]);
		}
	}
}
