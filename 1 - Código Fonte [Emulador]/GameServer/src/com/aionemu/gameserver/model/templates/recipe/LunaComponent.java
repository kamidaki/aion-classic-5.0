package com.aionemu.gameserver.model.templates.recipe;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlType;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;

/****/
/** Author Rinzler (Encom)
/****/

@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(name = "LunaComponent")
public class LunaComponent
{
	@XmlElement(name = "luna_component")
	protected ArrayList<LunaComponentElement> luna_component;
	
	public Collection<LunaComponentElement> getComponents() {
		return luna_component != null ? luna_component : Collections.<LunaComponentElement> emptyList();
	}
}