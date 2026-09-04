package com.aionemu.gameserver.model.templates.teleport;

import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;
import java.util.List;

/****/
/** Author Rinzler (Encom)
/****/

@XmlType(name = "MultiReturn")
public class MultiReturn
{
	@XmlAttribute(name = "id")
	private int id;
	
	@XmlElement(name = "loc")
	private List<MultiReturnLocationList> MultiReturnList;
	
	public int getId() {
		return id;
	}
	
	public MultiReturnLocationList getReturnDataById(int id) {
		if (MultiReturnList != null) {
			return MultiReturnList.get(id);
		}
		return null;
	}
	
	public List<MultiReturnLocationList> getMultiReturnList() {
		return MultiReturnList;
	}
}