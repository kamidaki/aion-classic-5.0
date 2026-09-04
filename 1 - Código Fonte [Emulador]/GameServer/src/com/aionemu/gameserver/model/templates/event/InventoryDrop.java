package com.aionemu.gameserver.model.templates.event;


import com.aionemu.gameserver.model.Race;

import javax.xml.bind.annotation.*;



@XmlType(name = "InventoryDrop")
@XmlAccessorType(XmlAccessType.FIELD)
public class InventoryDrop
{
	@XmlValue
	private int dropItem;
	
	@XmlAttribute(name = "startlevel", required = false)
	private int startLevel;
	
	@XmlAttribute(name = "endlevel", required = false)
	private int endLevel;
	
	@XmlAttribute(name = "interval", required = true)
	private int interval;
	
	@XmlAttribute(name = "maxCountOfDay", required = false)
	private int maxCountOfDay;
	
	@XmlAttribute(name = "cleanTime", required = false)
	private int cleanTime;
	
	@XmlAttribute
	private Race race = Race.PC_ALL;
	
	public Race getRace() {
		return race;
	}
	
	public int getDropItem() {
		return dropItem;
	}
	
	public int getStartLevel() {
		return startLevel;
	}
	
	public int getEndLevel() {
		return endLevel;
	}
	
	public int getInterval() {
		return interval;
	}
	
	public int getMaxCountOfDay() {
		return maxCountOfDay;
	}
	
	public int getCleanTime() {
		return cleanTime;
	}
}