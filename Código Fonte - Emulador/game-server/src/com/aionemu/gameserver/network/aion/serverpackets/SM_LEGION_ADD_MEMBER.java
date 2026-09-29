package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.configs.network.NetworkConfig;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_LEGION_ADD_MEMBER extends AionServerPacket {

	private Player player;
	private boolean isMember;
	private int msgId;
	private String text;

	public SM_LEGION_ADD_MEMBER(Player player, boolean isMember, int msgId, String text) {
		this.player = player;
		this.isMember = isMember;
		this.msgId = msgId;
		this.text = text;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(player.getObjectId());
		writeS(player.getName());
		writeC(player.getLegionMember().getRank().getRankId());
		writeC(isMember ? 0x01 : 0x00);// is New Member?
		writeC(player.getCommonData().getPlayerClass().getClassId());
		writeC(player.getLevel());
		writeD(player.getPosition().getMapId());
		// 5.0: online e hora do último logoff entre o mapa e o servidor, como no S_CHANGE_GUILD_MEMBER_INFO (39 a 65 b, 24 de 24 nas capturas)
		writeC(0x01);
		writeD(0);
		writeD(NetworkConfig.GAMESERVER_ID); // TODO: add to account model?
		writeD(msgId);
		writeS(text);
	}
}
