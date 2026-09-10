package com.aionemu.gameserver.dataholders.loadingutils.adapters;

import javax.xml.bind.annotation.XmlElement;

/**
 * @author Lost Academy Team & Durak
 */
public class NpcEquipmentList {

	@XmlElement(name = "item")
	public int[] items;

}
