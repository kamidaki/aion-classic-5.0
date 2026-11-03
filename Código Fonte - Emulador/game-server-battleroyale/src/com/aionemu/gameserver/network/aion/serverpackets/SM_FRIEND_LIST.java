package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Friend;
import com.aionemu.gameserver.model.gameobjects.player.FriendList;
import com.aionemu.gameserver.model.gameobjects.player.FriendList.Status;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_FRIEND_LIST extends AionServerPacket {

	@Override
	protected void writeImpl(AionConnection con) {
		FriendList list = con.getActivePlayer().getFriendList();

		writeH(-list.getSize());
		writeC(0);// unk

		for (Friend friend : list) {
			writeD(friend.getObjectId());
			writeS(friend.getName());
			writeD(friend.getLevel());
			writeD(friend.getPlayerClass().getClassId());
			writeC(friend.getStatus() == Status.ONLINE ? 1 : 0);
			writeD(friend.getMapId());
			writeD(friend.getStatus() == Status.ONLINE ? 0 : friend.getLastOnlineEpochSeconds());
			writeS(friend.getNote()); // Friend note
			writeC(friend.getStatus().getId());
			writeS(friend.getFriendMemo());
		}
	}
}
