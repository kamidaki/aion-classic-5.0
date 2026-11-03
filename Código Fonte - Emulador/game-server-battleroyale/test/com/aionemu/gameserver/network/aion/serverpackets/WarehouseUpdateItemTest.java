package com.aionemu.gameserver.network.aion.serverpackets;

import static org.junit.jupiter.api.Assertions.*;

import java.io.File;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.HexFormat;

import javax.xml.bind.JAXBContext;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.ItemData;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemUpdateType;

/**
 * S 0xAA (S_CHANGE_WAREHOUSE_ITEM_DESC) contra a captura oficial aumentariventario_2026-09-19, que tem os dois únicos 0xAA das capturas 5.0.
 */
class WarehouseUpdateItemTest {

	private static final int KINAH_OBJ = 0xC041CB9D;
	private static final int KINAH = 182400001;

	/** C 0xB5 do cubo (0) para o armazém 2, 7.401.493 kinah: o armazém soma, motivo 0x05. */
	private static final String OFFICIAL_KINAH_IN = "9dcb41c0022200001e6315f07000000000000000000000000000000000000000000000000000000f000500000000";
	/** C 0xB5 do armazém 2 para o cubo, 100.000 kinah: o armazém diminui, motivo 0x06. */
	private static final String OFFICIAL_KINAH_OUT = "9dcb41c0022200001e6375696f00000000000000000000000000000000000000000000000000000f000600000000";

	/**
	 * Blob do fragmento de estigma 141000002 (5.500) no armazém 1, tirado do S 0xA8 da captura 06_Sistemas_Novos_5.0_2026-09-13_05-05-25:
	 * entrada 0x08 e entrada 0x00, 39 bytes. As capturas não têm 0xAA de item que não seja kinah; o teste fixa que o 0xAA manda o mesmo
	 * blob que o 0xA8 e o 0x1D oficiais mandam para o item.
	 */
	private static final String OFFICIAL_SHARD_BLOB = "2700" + "0800000000" + "0028617c150000000000000000000000000000000000000000000000000000000f00";

	@BeforeAll
	static void load() throws Exception {
		DataManager.ITEM_DATA = (ItemData) JAXBContext.newInstance(ItemData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/items/item_templates.xml"));
	}

	@Test
	void kinahMatchesOfficialCapture() {
		assertEquals(46, OFFICIAL_KINAH_IN.length() / 2);
		assertEquals(OFFICIAL_KINAH_IN, body(item(KINAH_OBJ, KINAH, 7_401_493), 2, ItemUpdateType.INC_KINAH_MERGE));
		assertEquals(OFFICIAL_KINAH_OUT, body(item(KINAH_OBJ, KINAH, 7_301_493), 2, ItemUpdateType.DEC_ITEM_SPLIT));
	}

	@Test
	void stackableItemCarriesTheFullBlob() {
		assertEquals("afed60c0" + "01" + OFFICIAL_SHARD_BLOB + "01000000" + "00",
			body(item(0xC060EDAF, 141000002, 5500), 1, ItemUpdateType.INC_ITEM_MERGE));
	}

	@Test
	void internalTypesKeepGeneralInfoWithoutTrailer() {
		// [D obj][C armazém][H 34][entrada 0x00], sem [D motivo][C 0]
		assertEquals(OFFICIAL_KINAH_IN.substring(0, 2 * 41), body(item(KINAH_OBJ, KINAH, 7_401_493), 2, ItemUpdateType.EQUIP_UNEQUIP));
	}

	private static Item item(int objId, int templateId, long count) {
		Item item = new Item(objId, DataManager.ITEM_DATA.getItemTemplate(templateId));
		item.setItemCount(count);
		return item;
	}

	private static String body(Item item, int warehouse, ItemUpdateType type) {
		SM_WAREHOUSE_UPDATE_ITEM packet = new SM_WAREHOUSE_UPDATE_ITEM(null, item, warehouse, type);
		ByteBuffer buffer = ByteBuffer.allocate(1024).order(ByteOrder.LITTLE_ENDIAN);
		packet.setBuf(buffer);
		packet.writeImpl(null);
		return HexFormat.of().formatHex(Arrays.copyOf(buffer.array(), buffer.position()));
	}
}
