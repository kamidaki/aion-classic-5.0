package com.aionemu.gameserver.model.templates.item;

/**
 * What happens to a socketed stone removed through the Classic 5.0 option clear window (client_option_clear.xml).
 */
public enum OptionClearType {
	/** The stone is exchanged for a non-tradeable stone of the same option. */
	RETURN,
	/** The stone is destroyed. */
	DELETE
}
