package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

/**
 * 0x171, fragmentos que saíram da identificação (C 0xDC). Layout no {@link SM_STORYBOOK_ITEM_RESULT}.
 */
public class SM_STORYBOOK_APPRAISE_RESULT extends SM_STORYBOOK_ITEM_RESULT {

	public SM_STORYBOOK_APPRAISE_RESULT(List<Result> results) {
		super(results);
	}
}
