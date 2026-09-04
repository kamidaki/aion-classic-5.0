package com.aionemu.gameserver.model.templates.instancerift;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlType;



@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "instance_rift")
public class InstanceRiftTemplate
{
	@XmlAttribute(name = "id")
	protected int id;
	
	public int getId() {
		return this.id;
	}
}