package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.questEngine.model.QuestState;
import javolution.util.FastList;

import java.util.List;

public class S_LOAD_FINISHEDQUEST extends AionServerPacket
{
	private List<QuestState> questState;
	
	public S_LOAD_FINISHEDQUEST(List<QuestState> questState) {
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
			// Classic 5.0: cada quest finalizada tem 20 bytes (op 0x007A, pacote [37] da captura oficial)
			writeD(qs.getQuestId());
			writeD(qs.getCompleteCount());
			writeD(0);
			writeD(0);
			writeD(1);
		}
		if (questState instanceof FastList) {
			FastList.recycle((FastList<?>) questState);
		}
		questState = null;
	}
}