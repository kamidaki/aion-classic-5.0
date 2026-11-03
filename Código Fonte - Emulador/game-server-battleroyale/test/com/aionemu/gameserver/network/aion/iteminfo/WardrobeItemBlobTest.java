package com.aionemu.gameserver.network.aion.iteminfo;

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
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;

/**
 * Cor e marca de visual do Wardrobe no blob do item, contra os S 0x1D da captura 06_Sistemas_Novos_5.0 de 2026-09-21 14:56: torso 110301347
 * com o visual 110900536 tingido de 198d94 (aplicado e depois removido) e asa 187000036 com o visual 187060068.
 */
class WardrobeItemBlobTest {

	private static final HexFormat HEX = HexFormat.of();

	@BeforeAll
	static void load() throws Exception {
		DataManager.ITEM_DATA = (ItemData) JAXBContext.newInstance(ItemData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/items/item_templates.xml"));
	}

	@Test
	void dyedWardrobeSkinOnArmor() {
		Item torso = item(0xC081B163, 110301347);
		torso.setItemSkinTemplate(DataManager.ITEM_DATA.getItemTemplate(110900536));
		torso.setWardrobeSkin(true);
		torso.setItemColor(0x198D94);
		// 0x1D de 173.684: 02 08 00.. 00 01 19 8d 94
		assertEquals("02" + "0800000000000000" + "0000000000000000" + "01198d94", entry(ItemBlobType.SLOTS_ARMOR, torso));
		byte[] mana = HEX.parseHex(entry(ItemBlobType.MANA_SOCKETS, torso));
		assertEquals("38359c06", HEX.formatHex(mana, 3, 7));
		// [C tingido][R][G][B][C wardrobe][D 0][D validade][C wardrobe]...
		assertEquals("01198d94" + "01" + "00000000" + "00000000" + "01000000", HEX.formatHex(mana, 36, 53));

		// C 0xFA com entrada 0 (177.837): volta o visual do item, sem tinta e sem as marcas
		torso.setItemSkinTemplate(torso.getItemTemplate());
		torso.setItemColor(null);
		assertFalse(torso.isWardrobeSkin());
		assertEquals("02" + "0800000000000000" + "0000000000000000" + "00000000", entry(ItemBlobType.SLOTS_ARMOR, torso));
		assertEquals("00000000" + "00" + "00000000" + "00000000" + "00000000", HEX.formatHex(HEX.parseHex(entry(ItemBlobType.MANA_SOCKETS, torso)), 36, 53));
	}

	@Test
	void undyedWardrobeSkinOnWing() {
		Item wing = item(0xC081B168, 187000036);
		wing.setItemSkinTemplate(DataManager.ITEM_DATA.getItemTemplate(187060068));
		wing.setWardrobeSkin(true);
		byte[] mana = HEX.parseHex(entry(ItemBlobType.MANA_SOCKETS, wing));
		assertEquals("644f260b", HEX.formatHex(mana, 3, 7));
		// 0x1D de 25.952: 00 00 00 00 01 .. 01
		assertEquals("00000000" + "01" + "00000000" + "00000000" + "01000000", HEX.formatHex(mana, 36, 53));
	}

	private static Item item(int objId, int templateId) {
		return new Item(objId, DataManager.ITEM_DATA.getItemTemplate(templateId));
	}

	private static String entry(ItemBlobType type, Item item) {
		ItemBlobEntry entry = ItemInfoBlob.newBlobEntry(type, null, item);
		ByteBuffer buffer = ByteBuffer.allocate(1024).order(ByteOrder.LITTLE_ENDIAN);
		entry.writeMe(buffer);
		assertEquals(entry.getSize() + 1, buffer.position());
		return HEX.formatHex(Arrays.copyOf(buffer.array(), buffer.position()));
	}
}
