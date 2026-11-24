package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;
import java.util.function.Function;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.questEngine.model.QuestState;

/**
 * SM_QUEST_COMPLETED_LIST (0x007A) - 20 bytes per quest (Classic 5.0 wire verified).
 * @author Lost Academy Team & Durak
 */
public class SM_QUEST_COMPLETED_LIST extends AionServerPacket {

	public static final int STATIC_BODY_SIZE = 4;
	public static final Function<QuestState, Integer> DYNAMIC_BODY_PART_SIZE_CALCULATOR = (questState) -> 20;

	private final int updateMode;
	private final List<QuestState> questStates;

	/**
	 * @param updateMode
	 *          0 = rewrite all entries, 1 = insert new entries
	 * @param questStates
	 *          list of affected quests
	 */
	public SM_QUEST_COMPLETED_LIST(int updateMode, List<QuestState> questStates) {
		this.updateMode = updateMode;
		this.questStates = questStates;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		if (questStates == null) {
			writeH(0x01);
			writeH(0);
			return;
		}

		writeC(1); // unk, always 1
		writeC(updateMode); // 0 = rewrite all entries, 1 = insert new entries
		writeH(-questStates.size() & 0xFFFF);
		for (QuestState qs : questStates) {
			// Classic 5.0: each completed quest is exactly 20 bytes
			writeD(qs.getQuestId());
			writeD(qs.getCompleteCount());
			writeD(0);
			writeD(0);
			writeD(1);
		}
	}
}

