package com.aionemu.gameserver.model.templates.pet;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;



@XmlType(name = "merch")
@XmlAccessorType(XmlAccessType.NONE)
public class PetMerchandEntry
{
	@XmlAttribute(name = "id", required = true)
	private int id;
	
	@XmlAttribute(name = "rate_price")
	private int ratePrice;
	
	public int getId() {
		return id;
	}
	
	public int getRatePrice() {
		return ratePrice;
	}
}