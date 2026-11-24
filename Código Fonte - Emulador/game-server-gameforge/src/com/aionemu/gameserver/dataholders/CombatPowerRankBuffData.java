package com.aionemu.gameserver.dataholders;

import java.util.ArrayList;
import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;

import com.aionemu.gameserver.model.templates.ranking.CombatPowerRankBuff;

/**
 * Buffs do ranking de Combat Talent (ranking/combat_power_rank_buff.xml, gerado do system/client_combat_power_rank_buff.xml).
 */
@XmlRootElement(name = "combat_power_rank_buffs")
@XmlAccessorType(XmlAccessType.FIELD)
public class CombatPowerRankBuffData {

	@XmlElement(name = "buff")
	private List<CombatPowerRankBuff> buffs = new ArrayList<>();

	/**
	 * @param classId
	 *          classe do 1º lugar; ignorada nas abas de todas as classes (class_id 0)
	 * @return o buff da aba e da posição, ou null se não houver
	 */
	public CombatPowerRankBuff getBuff(int rankId, int rank, int classId) {
		for (CombatPowerRankBuff buff : buffs)
			if (buff.getRankId() == rankId && buff.getRank() == rank && (buff.getClassId() == 0 || buff.getClassId() == classId))
				return buff;
		return null;
	}

	public int size() {
		return buffs.size();
	}
}
