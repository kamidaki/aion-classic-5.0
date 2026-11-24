package com.aionemu.gameserver.model.templates.item;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;

/**
 * Removal rule of a socketed manastone or godstone, generated from client_option_clear.xml of the Classic 5.0 client.
 */
@XmlAccessorType(XmlAccessType.NONE)
public class OptionClearTemplate {

	@XmlAttribute(name = "item_id", required = true)
	private int itemId;

	@XmlAttribute(name = "type", required = true)
	private OptionClearType type;

	@XmlAttribute(name = "kinah", required = true)
	private long kinah;

	@XmlAttribute(name = "return_item_id")
	private int returnItemId;

	public int getItemId() {
		return itemId;
	}

	public OptionClearType getType() {
		return type;
	}

	public long getKinah() {
		return kinah;
	}

	public int getReturnItemId() {
		return returnItemId;
	}
}
