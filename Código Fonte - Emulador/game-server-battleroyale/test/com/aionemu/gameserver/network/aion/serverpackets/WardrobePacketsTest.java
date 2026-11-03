package com.aionemu.gameserver.network.aion.serverpackets;

import static org.junit.jupiter.api.Assertions.*;

import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.model.DescriptionId;
import com.aionemu.gameserver.model.gameobjects.player.WardrobeEntry;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Wardrobe contra as capturas oficiais 06_Sistemas_Novos_5.0 de 2026-09-21 14:56 (login com 3 entradas, tingir, favoritar) e 15:16 (registrar,
 * apagar, login vazio).
 */
class WardrobePacketsTest {

	private static final HexFormat HEX = HexFormat.of();

	@Test
	void loadMatchesOfficialLogins() throws Exception {
		List<WardrobeEntry> entries = List.of(new WardrobeEntry(0xC081B22B, 110900536, null, false),
			new WardrobeEntry(0xC081B22C, 102500336, null, false), new WardrobeEntry(0xC081B22D, 187060068, null, false));
		assertEquals("01000200030001" + "2bb281c038359c06000000000000000000" + "2cb281c0f0071c06000000000000000000"
			+ "2db281c0644f260b000000000000000000", HEX.formatHex(body(new SM_USER_CLASSIC_WARDROBE_LOAD(2, entries))));
		assertEquals("01000000000001", HEX.formatHex(body(new SM_USER_CLASSIC_WARDROBE_LOAD(0, List.of()))));
		// Global Auction House 2026-09: uma entrada tingida de 1f87f5
		assertEquals("01000000010001" + "09a640c03e339c0601" + "1f87f5" + "0000000000", HEX.formatHex(
			body(new SM_USER_CLASSIC_WARDROBE_LOAD(0, List.of(new WardrobeEntry(0xC040A609, 110900030, 0x1F87F5, false))))));
	}

	@Test
	void dataUpdatedMatchesOfficialActions() throws Exception {
		WardrobeEntry dyed = new WardrobeEntry(0xC081B22B, 110900536, 0x198D94, false);
		assertEquals("032bb281c038359c0601198d940000000000", HEX.formatHex(body(new SM_USER_CLASSIC_WARDROBE_DATA_UPDATED(3, dyed))));
		dyed.setLiked(true);
		assertEquals("042bb281c038359c0601198d940000000001", HEX.formatHex(body(new SM_USER_CLASSIC_WARDROBE_DATA_UPDATED(4, dyed))));
		assertEquals("02ba0882c0f1f6730701c7af270000000000", HEX.formatHex(body(new SM_USER_CLASSIC_WARDROBE_DATA_UPDATED(2,
			new WardrobeEntry(0xC08208BA, 125040369, 0xC7AF27, false)))));
		assertEquals("01840a82c00a657307000000000000000000", HEX.formatHex(body(new SM_USER_CLASSIC_WARDROBE_DATA_UPDATED(1,
			new WardrobeEntry(0xC0820A84, 125003018, null, false)))));
	}

	@Test
	void hairstyleListAndSlots() throws Exception {
		assertEquals("000001000000", HEX.formatHex(body(new SM_USER_CLASSIC_HAIRSTYLE_LOAD(0x2E0F5BD9, List.of(), 1, 0))));
		// S 0x177 da captura de 2026-09-21 14:56, menos o Q (842 no oficial, não lido pelo cliente)
		WardrobeEntry hair = new WardrobeEntry(0xC081B22E, 169800480, null, false);
		assertEquals("01002eb281c0" + "0000000000000000" + "d95b0f2e20f31e0a000100000000000001000000",
			HEX.formatHex(body(new SM_USER_CLASSIC_HAIRSTYLE_LOAD(0x2E0F5BD9, List.of(hair), 1, 0))));
		// S 0x178 (Game.dll 0x8CC860): [C ação] + o mesmo registro
		assertEquals("01" + "2eb281c0" + "0000000000000000" + "d95b0f2e20f31e0a0001000000000000",
			HEX.formatHex(body(new SM_USER_CLASSIC_HAIRSTYLE_DATA_UPDATED(SM_USER_CLASSIC_HAIRSTYLE_DATA_UPDATED.REGISTERED, 0x2E0F5BD9, hair))));
		// S 0x179 (Game.dll 0x8CCCD0): [H gratuitos][H comprados]
		assertEquals("01000200", HEX.formatHex(body(new SM_USER_CLASSIC_HAIRSTYLE_SLOTS(1, 2))));
	}

	@Test
	void appearanceCarriesTheHairAsWord() throws Exception {
		// Game.dll 0x3907fe: word ptr [aparência + 0x11] + 1 = malha %s%03d_Hair.cgf; 20011 (tintura especial) vira df20012_hair
		com.aionemu.gameserver.model.gameobjects.player.PlayerAppearance look = new com.aionemu.gameserver.model.gameobjects.player.PlayerAppearance();
		look.setFace(25);
		look.setHair(20011);
		byte[] out = body(new AionServerPacket(0x20) {
			@Override
			protected void writeImpl(AionConnection con) {
				writeAppearance(look);
			}
		});
		assertEquals(67, out.length);
		assertEquals("192b4e", HEX.formatHex(out, 16, 19));
		look.setHair(210); // S_PUT_USER oficial de 2026-09-21 14:56: 19 d2 00
		assertEquals("19d200", HEX.formatHex(body(new AionServerPacket(0x20) {
			@Override
			protected void writeImpl(AionConnection con) {
				writeAppearance(look);
			}
		}), 16, 19));
	}

	@Test
	void infoUpdatedCarriesOnlyThePurchasedSlots() throws Exception {
		// Game.dll 0x8C9300 lê só [H slots comprados] (o mesmo global do 2º H do LOAD)
		assertEquals("0300", HEX.formatHex(body(new SM_USER_CLASSIC_WARDROBE_INFO_UPDATED(3))));
	}

	@Test
	void messagesCarryTheItemName() throws Exception {
		// apagar o capacete 125040369 (desc 798315) e tingir o torso 110900536 (798919) com a tinta 169200001 (728300)
		assertEquals("190000000000c6621500012400d75c1800000000", HEX.formatHex(body(new SM_SYSTEM_MESSAGE(1401542, new DescriptionId(798315 * 2 + 1)))));
		assertEquals("190000000000dd6215000224008f61180000002400d939160000" + "0000", HEX.formatHex(
			body(new SM_SYSTEM_MESSAGE(1401565, new DescriptionId(798919 * 2 + 1), new DescriptionId(728300 * 2 + 1)))));
	}

	@Test
	void blackDyeIsNotLost() {
		WardrobeEntry black = new WardrobeEntry(1, 110900536, 0, false);
		assertEquals(0x1000000, black.getStoredColor());
		assertEquals(0, WardrobeEntry.fromStoredColor(black.getStoredColor()));
		assertNull(WardrobeEntry.fromStoredColor(new WardrobeEntry(1, 110900536, null, false).getStoredColor()));
		assertEquals(0xC7AF27, WardrobeEntry.fromStoredColor(new WardrobeEntry(1, 125040369, 0xC7AF27, false).getStoredColor()));
	}

	private static byte[] body(AionServerPacket packet) throws Exception {
		ByteBuffer buffer = ByteBuffer.allocate(8192).order(ByteOrder.LITTLE_ENDIAN);
		packet.setBuf(buffer);
		Method method = null;
		for (Class<?> c = packet.getClass(); method == null; c = c.getSuperclass())
			method = Arrays.stream(c.getDeclaredMethods()).filter(m -> m.getName().equals("writeImpl")).findFirst().orElse(null);
		method.setAccessible(true);
		method.invoke(packet, new Object[] { (AionConnection) null });
		return Arrays.copyOf(buffer.array(), buffer.position());
	}
}
