package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.Collections;
import java.util.List;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.skill.PlayerSkillEntry;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.skillinfo.SkillEntryWriter;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_SKILL_LIST extends AionServerPacket {

	public static final int STATIC_BODY_SIZE = 7;

	private final List<PlayerSkillEntry> skillList;
	private final int messageId;
	private String skillNameL10n;
	private String skillLvl;
	boolean silentUpdate = false;
	private int[] descriptionIds;

	public SM_SKILL_LIST(List<PlayerSkillEntry> skillList) {
		this.skillList = skillList;
		this.messageId = 0;
		this.silentUpdate = true;
	}

	public SM_SKILL_LIST(PlayerSkillEntry skill, int messageId) {
		this.skillList = Collections.singletonList(skill);
		this.messageId = messageId;
		this.skillNameL10n = DataManager.SKILL_DATA.getSkillTemplate(skill.getSkillId()).getL10n();
		this.skillLvl = String.valueOf(skill.getSkillLevel());
	}

	/**
	 * 5.0, skill de equipamento ao equipar: mensagem 1403638 seguida do nome do item e do da skill como DescriptionId (33 b na captura
	 * de 2026-10-18 13:42), sem as strings do S_ADD_SKILL comum.
	 */
	public SM_SKILL_LIST(PlayerSkillEntry skill, int messageId, int itemDescriptionId, int skillDescriptionId) {
		this.skillList = Collections.singletonList(skill);
		this.messageId = messageId;
		this.descriptionIds = new int[] { itemDescriptionId, skillDescriptionId };
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeH(skillList.size()); // skills list size
		for (PlayerSkillEntry entry : skillList)
			SkillEntryWriter.writeSkillEntry(entry, getBuf());
		writeD(messageId);
		if (descriptionIds != null) {
			for (int descriptionId : descriptionIds)
				writeNameId(descriptionId);
		} else if (messageId != 0) {
			writeS(skillNameL10n);
			writeS(skillLvl);
			writeH(0x00);
		}
	}
}
