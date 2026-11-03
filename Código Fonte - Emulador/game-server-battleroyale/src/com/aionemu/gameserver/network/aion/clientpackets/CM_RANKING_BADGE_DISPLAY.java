package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_RANKING_BADGE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_RANKING_BADGE_OTHER;
import com.aionemu.gameserver.utils.PacketSendUtility;

/**
 * Opção "mostrar ranking badge" das configurações do jogo, C 0xC8 [D objeto][D 0][C mostrar] (9 b; captura 06_Sistemas_Novos 2026-10-20
 * 02:17, 0 e depois 1). A resposta é o S 0x138 e o S 0x139, que também vai para quem está vendo o jogador.
 */
public class CM_RANKING_BADGE_DISPLAY extends AionClientPacket {

	private boolean shown;

	public CM_RANKING_BADGE_DISPLAY(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		readD(); // objeto do próprio jogador
		readD();
		shown = readC() != 0;
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		player.getPlayerSettings().setRankingBadgeShown(shown);
		sendPacket(new SM_RANKING_BADGE(shown));
		PacketSendUtility.broadcastPacket(player, new SM_RANKING_BADGE_OTHER(player.getObjectId(), shown), true);
	}
}
