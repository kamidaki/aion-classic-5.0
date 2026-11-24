package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.List;

/**
 * 0x172, itens que saíram da desmontagem de fragmentos (C 0xDD). Layout no {@link SM_STORYBOOK_ITEM_RESULT}.
 */
public class SM_STORYBOOK_DISASSEMBLE_RESULT extends SM_STORYBOOK_ITEM_RESULT {

	public SM_STORYBOOK_DISASSEMBLE_RESULT(List<Result> results) {
		super(results);
	}
}
