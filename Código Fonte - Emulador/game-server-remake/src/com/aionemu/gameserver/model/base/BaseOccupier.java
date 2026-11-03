package com.aionemu.gameserver.model.base;

import com.aionemu.gameserver.model.Race;

/**
 * @author Lost Academy Team & Durak
 */
public enum BaseOccupier {

	ELYOS,
	ASMODIANS,
	BALAUR;

	public static BaseOccupier findBy(Race race) {
		return switch (race) {
			case ELYOS -> ELYOS;
			case ASMODIANS -> ASMODIANS;
			default -> BALAUR;
		};
	}
}
