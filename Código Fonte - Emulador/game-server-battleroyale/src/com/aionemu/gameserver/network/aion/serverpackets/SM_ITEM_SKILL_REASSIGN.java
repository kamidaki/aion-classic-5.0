package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Reassign da skill de equipamento, 5.0 oficial (capturas de 2026-09-14 e 2026-10-18, 4 sorteios): [D item][D skill atual][D outra][D 0].
 * <ul>
 * <li>0x193, resposta ao C 0x107: a outra é a skill sorteada, que o jogador aceita ou recusa;</li>
 * <li>0x194, resposta ao C 0x130: a outra é a skill que ficou no item (a atual, quando ele recusa).</li>
 * </ul>
 */
public class SM_ITEM_SKILL_REASSIGN extends AionServerPacket {

	private final int itemObjId;
	private final int currentSkillId;
	private final int otherSkillId;

	public SM_ITEM_SKILL_REASSIGN(int itemObjId, int currentSkillId, int otherSkillId) {
		this.itemObjId = itemObjId;
		this.currentSkillId = currentSkillId;
		this.otherSkillId = otherSkillId;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(itemObjId);
		writeD(currentSkillId);
		writeD(otherSkillId);
		writeD(0);
	}
}
