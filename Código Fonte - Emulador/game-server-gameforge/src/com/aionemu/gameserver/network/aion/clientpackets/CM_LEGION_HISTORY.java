package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.team.legion.LegionHistoryAction.Type;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.serverpackets.SM_LEGION_HISTORY;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;

/**
 * Pedido de uma página do histórico da Legion: dec 0xFFFF [D página][C aba]. O cliente pede as abas 0 a 3 no login e, depois de cada S 0x9D 08/0A/0D,
 * a que mudou; a resposta é o S 0x0C da aba (Nova Pasta 2026-09-29 16:02: 0 e 3 depois de produzir, 0 e 2 depois de mexer no armazém).
 *
 * @author Lost Academy Team & Durak
 */
public class CM_LEGION_HISTORY extends AionClientPacket {

	private int page;
	private Type type;

	public CM_LEGION_HISTORY(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		page = readD();
		int tab = readUC();
		type = tab < Type.values().length ? Type.values()[tab] : null;
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player.getLegion() == null) {
			// o cliente pede a aba 0 logo depois de sair da Legion; o oficial responde que ele não está em uma (Nova Pasta 2026-09-29 18:08)
			sendPacket(SM_SYSTEM_MESSAGE.STR_GUILD_DISPERSE_I_AM_NOT_BELONG_TO_GUILD());
			return;
		}
		if (type == null)
			return;
		if (type == Type.REWARD && !player.getLegionMember().isBrigadeGeneral())
			return;
		sendPacket(new SM_LEGION_HISTORY(player.getLegion().getHistory(type), page, type));
	}
}
