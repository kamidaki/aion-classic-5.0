package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.item.ItemSkillService;

/**
 * Decodificado 0x107 (cru 0x1FD), botão Reassign da skill de equipamento: [D item]. 4 de 4 nas capturas oficiais (2026-09-14 e 2026-10-18),
 * respondido com S 0x11B (60 Quna) e S 0x193.
 */
public class CM_ITEM_SKILL_REASSIGN extends AionClientPacket {

	private int itemObjId;

	public CM_ITEM_SKILL_REASSIGN(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		itemObjId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			ItemSkillService.requestReassign(player, itemObjId);
	}
}
