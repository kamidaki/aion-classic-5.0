package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_CHANGE_FLAG extends AionServerPacket {

	private Integer obj;
	private int unk = 0;
	private int display;
	private int deny;

	public S_CHANGE_FLAG(Player player) {
		this(player.getObjectId(), 1, player.getPlayerSettings().getDisplay(), player.getPlayerSettings().getDeny());
	}

	public S_CHANGE_FLAG(int objectId, int unk, int display, int deny) {
		obj = objectId;
		this.display = display;
		this.deny = deny;
		this.unk = unk;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(obj);
		writeC(unk); // unk
		writeH(display);
		writeH(deny);
	}
}
