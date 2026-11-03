package com.aionemu.gameserver.model.templates.battle_pass;

import java.sql.Timestamp;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlSchemaType;
import javax.xml.bind.annotation.XmlType;
import javax.xml.datatype.XMLGregorianCalendar;

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "battlepass_season")
public class BattlePassSeasonTemplate {

	@XmlAttribute(name = "id", required = true)
	protected int id;

	@XmlAttribute(name = "name")
	protected String name;

	@XmlAttribute(name = "max_level", required = true)
	protected int maxLevel;

	@XmlAttribute(name = "unlock_level_start", required = true)
	protected int unlockLevelStart;

	@XmlAttribute(name = "unlock_pass_cost", required = true)
	protected int unlockPassCost;

	@XmlAttribute(name = "unlock_level_cost", required = true)
	protected int unlockLevelCost;

	@XmlAttribute(name = "start", required = true)
	@XmlSchemaType(name = "dateTime")
	protected XMLGregorianCalendar startDate;

	@XmlAttribute(name = "end", required = true)
	@XmlSchemaType(name = "dateTime")
	protected XMLGregorianCalendar endDate;

	public int getId() {
		return id;
	}

	public int getMaxLevel() {
		return maxLevel;
	}

	public int getUnlockLevelCost() {
		return unlockLevelCost;
	}

	public int getUnlockLevelStart() {
		return unlockLevelStart;
	}

	public int getUnlockPassCost() {
		return unlockPassCost;
	}

	public String getName() {
		return name;
	}

	private Timestamp customStartDate = null;
	private Timestamp customEndDate = null;

	public void setStartDate(Timestamp ts) {
		this.customStartDate = ts;
	}

	public void setEndDate(Timestamp ts) {
		this.customEndDate = ts;
	}

	public Timestamp getStartDate() {
		if (customStartDate != null) return customStartDate;
		return startDate != null ? new Timestamp(startDate.toGregorianCalendar().getTimeInMillis()) : new Timestamp(0);
	}

	public Timestamp getEndDate() {
		if (customEndDate != null) return customEndDate;
		return endDate != null ? new Timestamp(endDate.toGregorianCalendar().getTimeInMillis()) : new Timestamp(Long.MAX_VALUE);
	}
}
