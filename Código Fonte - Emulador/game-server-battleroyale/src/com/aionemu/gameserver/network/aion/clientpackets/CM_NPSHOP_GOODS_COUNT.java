package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.mail.BlackCloudMailService;

/**
 * [C_REQUEST_NPSHOP_GOODS_COUNT] (0xAA, sem corpo). Nas capturas vem depois de cada S_RESPONSE_NPSHOP_GOODS_LIST (3 de 3) e ao entrar no
 * mundo, sempre respondido pelo S_NPSHOP_GOODS_COUNT (0x10A). Antes o emulador registrava aqui o CM_PING_REQUEST (CUR_STATUS da 4.8), que
 * não respondia nada.
 */
public class CM_NPSHOP_GOODS_COUNT extends AionClientPacket {

	public CM_NPSHOP_GOODS_COUNT(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			BlackCloudMailService.sendGoodsCount(player);
	}
}
