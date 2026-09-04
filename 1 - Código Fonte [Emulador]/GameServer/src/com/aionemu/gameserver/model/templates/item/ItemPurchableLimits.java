package com.aionemu.gameserver.model.templates.item;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;



@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "Purchable")
public class ItemPurchableLimits
{
	@XmlAttribute(name = "rank_min")
	private int minRank;
	
	public int getMinRank() {
		return minRank;
	}
	
	public boolean verifyRank(int rank) {
		return minRank <= rank;
	}
}