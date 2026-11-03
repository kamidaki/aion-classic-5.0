package com.aionemu.gameserver.model.templates.ranking;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

/**
 * Uma linha do system/client_combat_power_rank_buff.xml: o buff que se compra de quem está em {@link #getRank()} na aba {@link #getRankId()}.
 */
@XmlAccessorType(XmlAccessType.NONE)
@XmlType(name = "CombatPowerRankBuff")
public class CombatPowerRankBuff {

	@XmlAttribute(name = "id", required = true)
	private int id;
	@XmlAttribute(name = "rank_id", required = true)
	private int rankId;
	/** 0 = todas as classes (abas 1000 e 1002) */
	@XmlAttribute(name = "class_id", required = true)
	private int classId;
	@XmlAttribute(name = "rank", required = true)
	private int rank;
	@XmlAttribute(name = "price", required = true)
	private long price;
	@XmlAttribute(name = "skill_id", required = true)
	private int skillId;
	@XmlAttribute(name = "basic_kina")
	private long basicKina;

	public int getId() {
		return id;
	}

	public int getRankId() {
		return rankId;
	}

	public int getClassId() {
		return classId;
	}

	public int getRank() {
		return rank;
	}

	public long getPrice() {
		return price;
	}

	public int getSkillId() {
		return skillId;
	}

	public long getBasicKina() {
		return basicKina;
	}
}
