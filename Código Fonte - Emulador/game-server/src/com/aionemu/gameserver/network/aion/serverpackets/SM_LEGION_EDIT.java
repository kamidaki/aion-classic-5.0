package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.team.legion.Legion;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.services.abyss.AbyssRankingCache;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_LEGION_EDIT extends AionServerPacket {

	private int type;
	private Legion legion;
	private int unixTime;
	private String announcement;

	public SM_LEGION_EDIT(int type) {
		this.type = type;
	}

	public SM_LEGION_EDIT(int type, Legion legion) {
		this.type = type;
		this.legion = legion;
	}

	public SM_LEGION_EDIT(int type, int unixTime) {
		this.type = type;
		this.unixTime = unixTime;
	}

	public SM_LEGION_EDIT(Legion.Announcement announcement) {
		this.type = 0x05;
		this.announcement = announcement.message();
		this.unixTime = (int) (announcement.time().getTime() / 1000);
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(type);
		switch (type) {
			case 0x00: // Change Legion Level
				writeC(legion.getLegionLevel());
				break;
			case 0x01: // Change Abyss Ranking List Position
				writeD(AbyssRankingCache.getInstance().getRankingListPosition(legion));
				break;
			case 0x02: // Change Legion Permissions
				writeH(legion.getDeputyPermission());
				writeH(legion.getCenturionPermission());
				writeH(legion.getLegionaryPermission());
				writeH(legion.getVolunteerPermission());
				break;
			case 0x03: // Change Legion Contributions: D na 5.0 (03 25 cf f6 0d, Org Asmo 13/09; 4 de 4 com 5 b)
				writeD((int) Math.min(legion.getContributionPoints(), Integer.MAX_VALUE));
				break;
			case 0x04:
				writeQ(legion.getLegionWarehouse().getKinah());
				break;
			case 0x05: // Change Legion Announcement
				writeS(announcement);
				writeD(unixTime);
				break;
			case 0x06: // Disband Legion
				writeD(unixTime);
				break;
			case 0x07: // Recover Legion
				break;
			case 0x08: // aviso de histórico geral (o cliente pede a aba 0 com o 0xFFFF)
				break;
			case 0x0B: // Legion Join Settings, como o C_GUILD 0x10 (Nova Pasta 2026-09-29 16:14 e 16:40, 7 de 7)
				writeS(legion.getJoinIntro());
				writeC(legion.getJoinType());
				writeH(legion.getJoinMinLevel());
				break;
			case 0x0C: // Legion Activity, como o C_GUILD 0x17 (Nova Pasta 2026-09-29 16:14 e 16:40, 6 de 6)
				writeD(legion.getCampaignActivity());
				writeD(legion.getLegionActivity());
				break;
		}
	}
}
