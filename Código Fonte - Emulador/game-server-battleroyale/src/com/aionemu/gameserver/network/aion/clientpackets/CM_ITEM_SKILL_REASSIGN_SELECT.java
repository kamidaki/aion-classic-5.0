package com.aionemu.gameserver.network.aion.clientpackets;

import java.util.Set;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.services.item.ItemSkillService;

/**
 * Decodificado 0x130 (cru 0x1C2), escolha depois do Reassign: [D item][D skill]. 0 mantém a skill atual (2 de 4 nas capturas); a skill
 * sorteada no S 0x193 troca (2 de 4).
 */
public class CM_ITEM_SKILL_REASSIGN_SELECT extends AionClientPacket {

	private int itemObjId;
	private int skillId;

	public CM_ITEM_SKILL_REASSIGN_SELECT(int opcode, Set<State> validStates) {
		super(opcode, validStates);
	}

	@Override
	protected void readImpl() {
		itemObjId = readD();
		skillId = readD();
	}

	@Override
	protected void runImpl() {
		Player player = getConnection().getActivePlayer();
		if (player != null)
			ItemSkillService.selectReassign(player, itemObjId, skillId);
	}
}
