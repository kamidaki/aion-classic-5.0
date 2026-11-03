package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.team.TeamType;
import com.aionemu.gameserver.model.team.common.legacy.LootGroupRules;
import com.aionemu.gameserver.model.team.group.PlayerGroup;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_GROUP_INFO extends AionServerPacket {

	private final LootGroupRules lootRules;
	private final int groupId;
	private final int leaderId;
	private final TeamType type;

	public SM_GROUP_INFO(PlayerGroup group) {
		groupId = group.getObjectId();
		leaderId = group.getLeader().getObjectId();
		lootRules = group.getLootGroupRules();
		type = group.getTeamType();
	}

	@Override
	protected void writeImpl(AionConnection con) {
		// 5.0 (captura 06_Sistemas_Novos 2026-10-19 22:54, 59 b): sem o mapa depois do líder, 7 graus de item e sem o id de mensagem
		writeD(groupId);
		writeD(leaderId);
		writeD(lootRules.getLootRule().getId());
		writeD(lootRules.getMisc());
		writeD(lootRules.getCommonItemAbove());
		writeD(lootRules.getSuperiorItemAbove());
		writeD(lootRules.getHeroicItemAbove());
		writeD(lootRules.getFabledItemAbove());
		writeD(lootRules.getEternalItemAbove());
		writeD(lootRules.getMythicItemAbove());
		writeD(lootRules.getDivinityItemAbove());
		writeD(0x02);
		writeC(0x00);
		writeD(type.getType());
		writeD(type.getSubType());
		writeS(""); // name
	}

}
