package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.configs.network.NetworkConfig;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.team.legion.LegionMember;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_LEGION_ADD_MEMBER extends AionServerPacket {

	private final int objectId;
	private final String name;
	private final int rank;
	private final boolean isMember;
	private final int classId;
	private final int level;
	private final int worldId;
	private final boolean online;
	private final int lastOnline;
	private final int msgId;
	private final String text;

	public SM_LEGION_ADD_MEMBER(Player player, boolean isMember, int msgId, String text) {
		this(player.getObjectId(), player.getName(), player.getLegionMember().getRank().getRankId(), isMember,
			player.getCommonData().getPlayerClass().getClassId(), player.getLevel(), player.getPosition().getMapId(), true, 0, msgId, text);
	}

	/**
	 * Membro offline, como o candidato aceito pela aba Applicant: online 0 e a hora do último logoff (Nova Pasta 2026-09-29 16:49, 53 b).
	 */
	public SM_LEGION_ADD_MEMBER(LegionMember member, int msgId, String text) {
		this(member.getObjectId(), member.getName(), member.getRank().getRankId(), false, member.getPlayerClass().getClassId(), member.getLevel(),
			member.getWorldId(), member.isOnline(), member.getLastOnlineEpochSeconds(), msgId, text);
	}

	private SM_LEGION_ADD_MEMBER(int objectId, String name, int rank, boolean isMember, int classId, int level, int worldId, boolean online,
		int lastOnline, int msgId, String text) {
		this.objectId = objectId;
		this.name = name;
		this.rank = rank;
		this.isMember = isMember;
		this.classId = classId;
		this.level = level;
		this.worldId = worldId;
		this.online = online;
		this.lastOnline = lastOnline;
		this.msgId = msgId;
		this.text = text;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(objectId);
		writeS(name);
		writeC(rank);
		writeC(isMember ? 0x01 : 0x00);// is New Member?
		writeC(classId);
		writeC(level);
		writeD(worldId);
		// 5.0: online e hora do último logoff entre o mapa e o servidor, como no S_CHANGE_GUILD_MEMBER_INFO (39 a 65 b, 24 de 24 nas capturas)
		writeC(online ? 0x01 : 0x00);
		writeD(online ? 0 : lastOnline);
		writeD(NetworkConfig.GAMESERVER_ID); // TODO: add to account model?
		writeD(msgId);
		writeS(text);
	}
}
