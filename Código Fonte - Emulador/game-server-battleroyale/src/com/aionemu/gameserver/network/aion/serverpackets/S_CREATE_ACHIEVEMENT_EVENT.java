package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.gameobjects.player.battlePass.BattlePassQuest;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

public class S_CREATE_ACHIEVEMENT_EVENT extends AionServerPacket {

	private final Player player;

	public S_CREATE_ACHIEVEMENT_EVENT(Player player) {
		this.player = player;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(this.player.getPlayerBattlePass().getBattlePassQuest().size());
		for (BattlePassQuest quest : this.player.getPlayerBattlePass().getBattlePassQuest().values()) {
			writeC(1); // active
			writeQ(quest.getObjectId()); // objectId
			writeD(quest.getId()); // id
			writeD(0);
			writeD(0);
			writeC(6); // type
			writeC(0);
			writeC(quest.getState().getValue()); // state
			writeD(quest.getStep()); // step
			writeC(0);
			writeD(0);
			writeD(0);
			writeD(0);
			writeD(0);
			writeD(0);
			long startMs = (quest.getTemplate() != null && quest.getTemplate().getStartDate() != null) ? quest.getTemplate().getStartDate().getMillisecond() : 0;
			long endMs = (quest.getTemplate() != null && quest.getTemplate().getStartDate() != null) ? quest.getTemplate().getStartDate().getMillisecond() : 0;
			writeQ(startMs); // start
			writeQ(endMs); // end
			writeC(0); // Classic 5.0 trailing byte (66 bytes per quest)
		}
	}
}
