package com.aionemu.gameserver.network.aion.serverpackets;

/**
 * 0x194: resultado do Reassign (C 0x130), mesmo corpo do {@link SM_ITEM_SKILL_REASSIGN}: [D item][D skill antiga][D skill que ficou][D 0].
 */
public class SM_ITEM_SKILL_REASSIGN_RESULT extends SM_ITEM_SKILL_REASSIGN {

	public SM_ITEM_SKILL_REASSIGN_RESULT(int itemObjId, int oldSkillId, int finalSkillId) {
		super(itemObjId, oldSkillId, finalSkillId);
	}
}
