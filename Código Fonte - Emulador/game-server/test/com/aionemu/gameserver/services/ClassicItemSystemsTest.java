package com.aionemu.gameserver.services;

import java.io.File;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.HexFormat;
import javax.xml.bind.JAXBContext;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import com.aionemu.gameserver.dataholders.ClassicItemSystemsData;
import com.aionemu.gameserver.dataholders.CubeExpandData;
import com.aionemu.gameserver.dataholders.DataManager;
import com.aionemu.gameserver.dataholders.ItemData;
import com.aionemu.gameserver.model.gameobjects.Item;
import com.aionemu.gameserver.model.items.ItemSlot;
import com.aionemu.gameserver.model.templates.item.enums.ItemGroup;
import com.aionemu.gameserver.model.templates.item.enums.EquipType;
import com.aionemu.gameserver.configs.main.GSConfig;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionConnection.State;
import com.aionemu.gameserver.network.aion.clientpackets.CM_CUBE_EXPAND;
import com.aionemu.gameserver.network.aion.clientpackets.CM_COMBAT_TALENT_REWARD;
import com.aionemu.gameserver.network.aion.clientpackets.CM_REMOVE_STIGMA;
import com.aionemu.gameserver.network.factories.AionPacketHandlerFactory;
import com.aionemu.gameserver.network.aion.serverpackets.SM_COMBAT_TALENT_REWARD_UPDATE;
import com.aionemu.gameserver.network.aion.serverpackets.SM_INVENTORY_ADD_ITEM;
import com.aionemu.gameserver.services.item.ItemPacketService.ItemAddType;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob;
import com.aionemu.gameserver.network.aion.iteminfo.ItemInfoBlob.ItemBlobType;
import com.aionemu.gameserver.network.aion.serverpackets.S_SERVER_ENV;
import com.aionemu.gameserver.network.aion.serverpackets.SM_SYSTEM_MESSAGE;

class ClassicItemSystemsTest {
	@BeforeAll static void loadOfficialRules() throws Exception {
		DataManager.CLASSIC_ITEM_SYSTEMS_DATA = (ClassicItemSystemsData) JAXBContext.newInstance(ClassicItemSystemsData.class)
			.createUnmarshaller().unmarshal(new File("data/static_data/items/classic_item_systems.xml"));
		DataManager.ITEM_DATA = (ItemData) JAXBContext.newInstance(ItemData.class).createUnmarshaller()
			.unmarshal(new File("data/static_data/items/item_templates.xml"));
		DataManager.CUBEEXPANDER_DATA = (CubeExpandData) JAXBContext.newInstance(CubeExpandData.class)
			.createUnmarshaller().unmarshal(new File("data/static_data/storage_expander/cube_expander.xml"));
	}

	@Test void essenceUsesOfficialCostsAndFailureTransition() {
		var common = DataManager.CLASSIC_ITEM_SYSTEMS_DATA.getEnchant("common_enchant", 0);
		assertEquals(2500, common.cost);
		assertEquals(5000, DataManager.CLASSIC_ITEM_SYSTEMS_DATA.getEnchant("rare_enchant", 0).cost);
		assertEquals(1, common.stones);
		assertEquals(1, common.success);
		assertEquals(0, common.failure);
		assertEquals(0, DataManager.CLASSIC_ITEM_SYSTEMS_DATA.getEnchant("unique_enchant", 1).failure);
		assertEquals(3, DataManager.CLASSIC_ITEM_SYSTEMS_DATA.getEnchant("unique_enchant", 4).failure);
		for (int id : new int[] {166300500, 166300000}) {
			var stone = DataManager.ITEM_DATA.getItemTemplate(id);
			assertTrue(stone.isEnchantEssence());
			assertEquals(ItemGroup.ENCHANTMENT, stone.getItemGroup());
			assertEquals(120, stone.getLevel());
		}
		assertNull(DataManager.CLASSIC_ITEM_SYSTEMS_DATA.getEnchant("common_enchant", 15));
	}

	@Test void everyArcamantUsesItsOwnSlotAndCanEnchant() {
		for (int id : new int[] {130000011,130000016,130000021,130000026,130000031,130000036,
			130000041,130000042,130000043,130000044,130000045,130000046}) {
			var item = DataManager.ITEM_DATA.getItemTemplate(id);
			assertEquals(ItemGroup.ARCAMANT, item.getItemGroup());
			assertEquals(EquipType.ARMOR, item.getEquipmentType());
			assertEquals(ItemSlot.ARCAMANT.getSlotIdMask(), item.getItemSlot());
			assertEquals(0, item.getItemSlot() & ItemSlot.SHARD_RIGHT_OR_LEFT.getSlotIdMask());
			assertEquals("seed_enchant", item.getEnchantGroup());
			assertEquals(15, item.getMaxEnchantLevel());
		}
	}

	@Test void arcamantBlobUsesItsOwnAccessorySlotInsteadOfWingEntry() {
		Item item = new Item(4, DataManager.ITEM_DATA.getItemTemplate(130000011));
		var blob = ItemInfoBlob.getFullBlob(null, item);
		assertTrue(blob.getBlobEntries().stream().anyMatch(e -> e instanceof com.aionemu.gameserver.network.aion.iteminfo.AccessoryInfoBlobEntry));
		assertFalse(blob.getBlobEntries().stream().anyMatch(e -> e instanceof com.aionemu.gameserver.network.aion.iteminfo.WingInfoBlobEntry));
		ByteBuffer buffer = ByteBuffer.allocate(32).order(ByteOrder.LITTLE_ENDIAN);
		ItemInfoBlob.newBlobEntry(ItemBlobType.SLOTS_ACCESSORY, null, item).writeThisBlob(buffer);
		assertEquals(16, buffer.position());
		assertEquals(ItemSlot.ARCAMANT.getSlotIdMask(), buffer.getLong(0));
		assertEquals(0, buffer.getLong(8));
	}

	@Test void arcamantRetainsOfficialBasicAttributeBonuses() {
		var stats = new com.aionemu.gameserver.model.stats.container.StatEnum[] {
			com.aionemu.gameserver.model.stats.container.StatEnum.POWER,
			com.aionemu.gameserver.model.stats.container.StatEnum.HEALTH,
			com.aionemu.gameserver.model.stats.container.StatEnum.AGILITY,
			com.aionemu.gameserver.model.stats.container.StatEnum.ACCURACY,
			com.aionemu.gameserver.model.stats.container.StatEnum.KNOWLEDGE,
			com.aionemu.gameserver.model.stats.container.StatEnum.WILL
		};
		for (int i = 0; i < stats.length; i++) {
			var stat = stats[i];
			var item = DataManager.ITEM_DATA.getItemTemplate(130000011 + 5 * i);
			assertEquals(5, item.getModifiers().stream().filter(m -> m.getName() == stat && m.isBonus())
				.mapToInt(m -> m.getValue()).sum(), item.getName());
		}
	}

	@Test void wingSlotsDoNotConsumeTheFollowingManaSocketsBlob() {
		Item item = new Item(5, DataManager.ITEM_DATA.getItemTemplate(187000001));
		ByteBuffer buffer = ByteBuffer.allocate(2048).order(ByteOrder.LITTLE_ENDIAN);
		ItemInfoBlob.getFullBlob(null, item).writeMe(buffer);
		buffer.flip();
		buffer.getShort(); // blob length
		assertEquals(0x06, Byte.toUnsignedInt(buffer.get()));
		buffer.getLong(); // equipped slot
		assertEquals(0x0D, Byte.toUnsignedInt(buffer.get()));
		assertEquals(ItemSlot.WINGS.getSlotIdMask(), buffer.getLong());
		assertEquals(0, buffer.getLong());
		assertEquals(0x0B, Byte.toUnsignedInt(buffer.get())); // next entry, as read by the client
	}

	@Test void discardUsesBreakableRatherThanGroundDropPermission() {
		// Official essence has breakable=TRUE and item_drop_permitted=FALSE.
		assertTrue(DataManager.ITEM_DATA.getItemTemplate(166300500).isDeletable());
		assertFalse(DataManager.ITEM_DATA.getItemTemplate(182400001).isDeletable());
	}

	@Test void inventoryExpansionUsesOfficialUiPacketAndNpcPriceTable() {
		assertEquals(1000, DataManager.CUBEEXPANDER_DATA.getPrice(1));
		assertEquals(12000, DataManager.CUBEEXPANDER_DATA.getPrice(2));
		assertEquals(80000, DataManager.CUBEEXPANDER_DATA.getPrice(3));
		assertEquals(180000, DataManager.CUBEEXPANDER_DATA.getPrice(4));
		assertEquals(360000, DataManager.CUBEEXPANDER_DATA.getPrice(5));
		assertNull(DataManager.CUBEEXPANDER_DATA.getPrice(6));

		var packets = AionPacketHandlerFactory.getInstance().getPacketHandler().getPacketsPrototypes().get(State.IN_GAME);
		assertInstanceOf(CM_CUBE_EXPAND.class, packets.get(0x1B8)); // decoded 0x00CA, one-byte type
		assertInstanceOf(CM_REMOVE_STIGMA.class, packets.get(0x136)); // decoded 0x003C, shared item-object request
	}

	@Test void enchantPowerUsesExactOfficialPointsAndExcludesStigmas() {
		Item item = new Item(1, DataManager.ITEM_DATA.getItemTemplate(110601334));
		int base = CombatTalentService.calculateItemPower(item);
		item.setEnchantLevel(15);
		assertEquals(842, CombatTalentService.calculateItemPower(item) - base);
		item.setEnchantLevel(10);
		assertEquals(291, CombatTalentService.calculateItemPower(item) - base);
		assertEquals(0, CombatTalentService.calculateItemPower(new Item(2, DataManager.ITEM_DATA.getItemTemplate(140000008))));
	}

	@Test void combatTalentRewardMatchesOfficialClaimCapture() throws Exception {
		var reward = DataManager.CLASSIC_ITEM_SYSTEMS_DATA.getCombatReward(11);
		assertNotNull(reward);
		assertEquals(14000, reward.goal);
		assertEquals(166300500, reward.item);
		assertEquals(10, reward.amount);
		assertEquals(14, DataManager.CLASSIC_ITEM_SYSTEMS_DATA.getCombatRewardCount());

		var packets = AionPacketHandlerFactory.getInstance().getPacketHandler().getPacketsPrototypes().get(State.IN_GAME);
		assertInstanceOf(CM_COMBAT_TALENT_REWARD.class, packets.get(0x1E5)); // decoded C 0x010F
		assertEquals("0b0001", HexFormat.of().formatHex(body(new SM_COMBAT_TALENT_REWARD_UPDATE(11, true))));
		assertEquals("190000000000646415000224005bf31800000031003000000000",
			HexFormat.of().formatHex(body(SM_SYSTEM_MESSAGE.STR_MSG_COMBAT_POWER_REWARD_GET(817581, 10))));

		Item item = new Item(0xC041BDBB, DataManager.ITEM_DATA.getItemTemplate(166300500));
		item.setItemCount(10);
		byte[] add = body(new SM_INVENTORY_ADD_ITEM(item, null, ItemAddType.COMBAT_TALENT_REWARD));
		assertEquals("eb00000000010100", HexFormat.of().formatHex(Arrays.copyOf(add, 8)));
	}

	@Test void clientMaskIsIndependentFromGameplayPermissions() {
		var arcamant = DataManager.ITEM_DATA.getItemTemplate(130000011);
		assertEquals(0x402C, arcamant.getClientMask());
		assertEquals(0, arcamant.getClientMask() & 0x40); // no soul-bind requirement
		assertEquals(0, arcamant.getClientMask() & 0x100); // enchant is permitted
		var armor = DataManager.ITEM_DATA.getItemTemplate(110601334);
		assertFalse(armor.isNoEnchant());
		assertEquals(0x8028, armor.getClientMask());
		assertNotNull(DataManager.CLASSIC_ITEM_SYSTEMS_DATA.getEnchant(armor.getEnchantGroup(), 0));
		assertEquals(500, DataManager.CLASSIC_ITEM_SYSTEMS_DATA.getGap(1, 60, "epic"));
		Item stone = new Item(3, DataManager.ITEM_DATA.getItemTemplate(166300500));
		ByteBuffer buffer = ByteBuffer.allocate(128).order(ByteOrder.LITTLE_ENDIAN);
		ItemInfoBlob.newBlobEntry(ItemBlobType.GENERAL_INFO, null, stone).writeThisBlob(buffer);
		assertEquals(0x6128, Short.toUnsignedInt(buffer.getShort(0))); // measured official essence blob
	}

	@Test void environmentMatchesOfficialSixtyBytePayload() throws Exception {
		int previous = GSConfig.CHARACTER_REENTRY_TIME;
		try {
			GSConfig.CHARACTER_REENTRY_TIME = 15;
			byte[] body = body(new S_SERVER_ENV());
			assertEquals(60, body.length);
			assertArrayEquals(HexFormat.of().parseHex(
				"5e01010a010a0a0a02000f000000000064000000014b0000004b000000000000006400000000003c000000023c000000ff7f0000"),
				Arrays.copyOf(body, 52));
		} finally { GSConfig.CHARACTER_REENTRY_TIME = previous; }
	}

	@Test void successMessageUsesClassicClientStringId() throws Exception {
		byte[] body = body(SM_SYSTEM_MESSAGE.STR_ENCHANT_ITEM_SUCCEED("item"));
		assertEquals(1300455, ByteBuffer.wrap(body).order(ByteOrder.LITTLE_ENDIAN).getInt(6));
	}

	private static byte[] body(AionServerPacket packet) throws Exception {
		ByteBuffer buffer = ByteBuffer.allocate(2048).order(ByteOrder.LITTLE_ENDIAN);
		packet.setBuf(buffer);
		var method = packet.getClass().getDeclaredMethod("writeImpl", AionConnection.class);
		method.setAccessible(true);
		method.invoke(packet, new Object[] {null});
		return Arrays.copyOf(buffer.array(), buffer.position());
	}
}
