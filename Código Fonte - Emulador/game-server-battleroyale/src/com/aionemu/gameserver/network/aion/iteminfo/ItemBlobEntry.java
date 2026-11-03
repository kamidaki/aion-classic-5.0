package com.aionemu.gameserver.network.aion.iteminfo;

import java.nio.ByteBuffer;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.model.stats.calc.functions.IStatFunction;
import com.aionemu.gameserver.network.PacketWriteHelper;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

/**
 * @author Lost Academy Team & Durak
 */
public abstract class ItemBlobEntry extends PacketWriteHelper {

	private final ItemBlobType type;
	Player owner;
	Item ownerItem;
	IStatFunction modifier;

	ItemBlobEntry(ItemBlobType type) {
		this.type = type;
	}

	void setOwner(Player owner, Item item, IStatFunction modifier) {
		this.owner = owner;
		this.ownerItem = item;
		this.modifier = modifier;
	}

	@Override
	protected void writeMe(ByteBuffer buf) {
		writeC(buf, type.getEntryId());
		writeThisBlob(buf);
	}

	public abstract void writeThisBlob(ByteBuffer buf);

	public abstract int getSize();

}
