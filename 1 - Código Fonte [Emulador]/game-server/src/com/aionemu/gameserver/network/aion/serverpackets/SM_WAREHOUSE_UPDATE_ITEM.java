package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.gameobjects.player.Player;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;

/**
 * S_CHANGE_WAREHOUSE_ITEM_DESC (0xAA). Classic 5.0: [D obj][C armazém][H tamanho][blob][D motivo][C 0], sem nameId (captura
 * aumentariventario 2026-09-19: kinah entre cubo e armazém, 46 bytes, motivos 0x05 e 0x06).
 *
 * @author Lost Academy Team & Durak
 */
public class SM_WAREHOUSE_UPDATE_ITEM extends AionServerPacket {

	private Player player;
	private Item item;
	private int warehouseType;
	private ItemUpdateType updateType;

	public SM_WAREHOUSE_UPDATE_ITEM(Player player, Item item, int warehouseType, ItemUpdateType updateType) {
		this.player = player;
		this.item = item;
		this.warehouseType = warehouseType;
		this.updateType = updateType;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(item.getObjectId());
		writeC(warehouseType);

		if (updateType.isSendable()) {
			// Como no S_CHANGE_ITEM_DESC (0x1D), o blob que fecha com motivo é o completo: nas capturas, todo 0x1D com trailer
			// o traz, e o S 0xA8 do mesmo armazém também. Para kinah o blob completo é só a entrada 0x00, igual ao 0xAA oficial.
			ItemInfoBlob.getFullBlob(player, item).writeMe(getBuf());
			writeD(updateType.getReason());
			writeC(0);
		} else {
			ItemInfoBlob itemInfoBlob = new ItemInfoBlob(player, item);
			itemInfoBlob.addBlobEntry(ItemBlobType.GENERAL_INFO);
			itemInfoBlob.writeMe(getBuf());
		}
	}
}
