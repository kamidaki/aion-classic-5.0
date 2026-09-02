package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.questEngine.model.QuestState;
import javolution.util.FastList;

import java.util.List;

public class S_LOAD_WORKINGQUEST extends AionServerPacket
{
	private List<QuestState> questState;
	
	public S_LOAD_WORKINGQUEST(List<QuestState> questState) {
		this.questState = questState;
	}
	
	@Override
	protected void writeImpl(AionConnection con) {
		if (questState == null) {
			writeH(0x01);
			writeH(0);
			return;
		}
		writeH(0x01);
		writeH(-questState.size() & 0xFFFF);
		for (QuestState qs: questState) {
			writeD(qs.getQuestId());
			writeC(qs.getStatus().value());
			writeD(qs.getQuestVars().getQuestVars());
			writeC(qs.getCompleteCount());
		}
		if (questState instanceof FastList) {
			FastList.recycle((FastList<?>) questState);
		}
		questState = null;
	}
}