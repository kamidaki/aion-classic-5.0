package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.mail.BlackCloudMailService;

/**
 * [C_SA_GOODSLIST] (0x9D, sem corpo): o cliente abre a aba "Black Cloud" da janela do carteiro. Na captura vem logo depois do C_MAIL_LIST
 * (0x8D) e recebe o S_RESPONSE_NPSHOP_GOODS_LIST (0x10C).
 */
public class CM_NPSHOP_GOODS_LIST extends AionClientPacket {

	public CM_NPSHOP_GOODS_LIST(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			BlackCloudMailService.sendGoodsList(player);
	}
}
