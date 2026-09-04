package com.aionemu.gameserver.model.templates.teleport;

import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;

/****/
/** Author Rinzler (Encom)
/****/

@XmlType(name = "MultiReturnLocationList")
public class MultiReturnLocationList
{
	@XmlAttribute(name = "world_id")
	protected int worldId;
	
	@XmlAttribute(name = "desc")
	protected String desc;
	
	public final int getWorldId() {
		return worldId;
	}
	
	public final String getDesc() {
		return desc;
	}
}