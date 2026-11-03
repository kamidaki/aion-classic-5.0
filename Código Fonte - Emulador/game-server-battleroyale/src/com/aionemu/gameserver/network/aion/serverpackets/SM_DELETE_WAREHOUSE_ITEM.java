package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemDeleteType;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_DELETE_WAREHOUSE_ITEM extends AionServerPacket {

	private int warehouseType;
	private int itemObjId;
	private ItemDeleteType deleteType;

	public SM_DELETE_WAREHOUSE_ITEM(int warehouseType, int itemObjId, ItemDeleteType deleteType) {
		this.warehouseType = warehouseType;
		this.itemObjId = itemObjId;
		this.deleteType = deleteType;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(warehouseType);
		writeD(itemObjId);
		writeD(deleteType.getMask()); // 5.0: tipo em D, 9 bytes no total (captura oficial de warehouse)
	}

}
