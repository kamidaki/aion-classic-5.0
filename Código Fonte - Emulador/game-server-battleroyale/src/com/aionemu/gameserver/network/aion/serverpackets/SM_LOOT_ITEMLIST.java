package com.aionemu.gameserver.network.aion.serverpackets;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Set;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.model.drop.Drop;
import com.aionemu.gameserver.model.drop.DropItem;
import com.aionemu.gameserver.model.gameobjects.DropNpc;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.templates.item.ItemTemplate;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_LOOT_ITEMLIST extends AionServerPacket {

	private final int targetObjectId;
	private final boolean teamMembersNearby;
	private final List<DropItem> dropItems;

	public SM_LOOT_ITEMLIST(DropNpc dropNpc, Set<DropItem> setItems, Player player) {
		this.targetObjectId = dropNpc.getObjectId();
		Collection<Player> playersInRange = dropNpc.getInRangePlayers();
		this.teamMembersNearby = playersInRange.size() > 1 && playersInRange.contains(player);
		this.dropItems = new ArrayList<>();
		for (DropItem item : setItems)
			if (item.canViewDropItem(player.getObjectId()))
				dropItems.add(item);
	}

	@Override
	protected void writeImpl(AionConnection con) {
		Player activePlayer = con.getActivePlayer();
		if (activePlayer == null)
			return;
		writeD(targetObjectId);
		writeH(dropItems.size());

		for (DropItem dropItem : dropItems) {
			Drop drop = dropItem.getDropTemplate();
			writeD(dropItem.getIndex()); // u32 index in droplist
			writeD(drop.getItemId());
			writeD((int) dropItem.getCount());
			writeC(0);
			writeC(0);
		}
	}

}
