package com.aionemu.gameserver.network.aion.iteminfo;

import java.nio.ByteBuffer;
import java.util.List;

import com.aionemu.gameserver.model.templates.item.Stigma;
import com.aionemu.gameserver.model.templates.item.Stigma.RequiredSkillGroup;
import com.aionemu.gameserver.model.templates.item.Stigma.StigmaSkill;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

/**
 * Classic 5.0 layout, measured on the official Stigma/Stigma2 captures (24 stones, all matching client_items): the 258 bytes are followed
 * directly by the 0x0B MANA_SOCKETS blob.
 *
 * @author Lost Academy Team & Durak
 */
public class StigmaInfoBlobEntry extends ItemBlobEntry {

	private static final int REQUIRE_GROUPS = 4;
	private static final int REQUIRE_SKILLS = 10;

	StigmaInfoBlobEntry() {
		super(ItemBlobType.STIGMA_INFO);
	}

	@Override
	public void writeThisBlob(ByteBuffer buf) {
		Stigma stigma = ownerItem.getItemTemplate().getStigma();
		List<StigmaSkill> gainSkills = stigma.getGainSkills();
		List<RequiredSkillGroup> groups = stigma.getRequiredSkillGroups();

		writeD(buf, gainSkills.size() > 0 ? gainSkills.get(0).skillId() : 0);
		writeD(buf, gainSkills.size() > 1 ? gainSkills.get(1).skillId() : 0);
		writeD(buf, stigma.getShard());
		for (int group = 0; group < REQUIRE_GROUPS; group++) {
			List<Integer> skillIds = group < groups.size() ? groups.get(group).skillIds() : List.of();
			for (int i = 0; i < REQUIRE_SKILLS; i++)
				writeD(buf, i < skillIds.size() ? skillIds.get(i) : 0);
		}
		writeH(buf, gainSkills.size() > 0 ? gainSkills.get(0).level() : 0);
		writeH(buf, gainSkills.size() > 1 ? gainSkills.get(1).level() : 0);
		for (int group = 0; group < REQUIRE_GROUPS; group++) {
			int level = group < groups.size() ? groups.get(group).level() : 0; // the official blob fills all 10 positions of a used group
			for (int i = 0; i < REQUIRE_SKILLS; i++)
				writeH(buf, level);
		}
		writeH(buf, groups.size());
	}

	@Override
	public int getSize() {
		return 12 + REQUIRE_GROUPS * REQUIRE_SKILLS * 4 + 4 + REQUIRE_GROUPS * REQUIRE_SKILLS * 2 + 2; // 258
	}
}
