package com.aionemu.gameserver.network.aion.clientpackets;

import static org.junit.jupiter.api.Assertions.*;

import java.lang.reflect.Field;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.EnumSet;
import java.util.HexFormat;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.network.aion.AionClientPacket;
import com.aionemu.gameserver.network.aion.AionConnection.State;

/**
 * Pedidos do Wardrobe capturados em 06_Sistemas_Novos_5.0 de 2026-09-21 (14:56 e 15:16), lidos com os opcodes crus do registro.
 */
class WardrobeClientPacketsTest {

	@Test
	void requestsFromCapture() throws Exception {
		assertEquals(0xC082083E, field(read(new CM_USER_CLASSIC_WARDROBE_REGISTER(0x184, EnumSet.of(State.IN_GAME)), "3e0882c0"), "itemObjId"));
		assertEquals(0xC08208BA, field(read(new CM_USER_CLASSIC_WARDROBE_REMOVE(0x185, EnumSet.of(State.IN_GAME)), "ba0882c0"), "entryObjId"));

		CM_USER_CLASSIC_WARDROBE_DYE dye = read(new CM_USER_CLASSIC_WARDROBE_DYE(0x18A, EnumSet.of(State.IN_GAME)), "2bb281c0e1bd81c0");
		assertEquals(0xC081B22B, field(dye, "entryObjId"));
		assertEquals(0xC081BDE1, field(dye, "dyeObjId"));

		CM_USER_CLASSIC_WARDROBE_FAVORITE favorite = read(new CM_USER_CLASSIC_WARDROBE_FAVORITE(0x18B, EnumSet.of(State.IN_GAME)), "2bb281c001");
		assertEquals(0xC081B22B, field(favorite, "entryObjId"));
		assertEquals(1, field(favorite, "favorite"));

		CM_USER_CLASSIC_WARDROBE_APPLY apply = read(new CM_USER_CLASSIC_WARDROBE_APPLY(0x188, EnumSet.of(State.IN_GAME)), "68b181c02db281c0");
		assertEquals(0xC081B168, field(apply, "itemObjId"));
		assertEquals(0xC081B22D, field(apply, "entryObjId"));
		CM_USER_CLASSIC_WARDROBE_APPLY remove = read(new CM_USER_CLASSIC_WARDROBE_APPLY(0x188, EnumSet.of(State.IN_GAME)), "68b181c000000000");
		assertEquals(0, field(remove, "entryObjId"));
	}

	@Test
	void hairstyleExtendReadsThePayment() throws Exception {
		// serializador 0x11A da aba de cabelo: [H 1][C 1 Quna, 2 item], fio 0x198
		assertEquals(1, field(read(new CM_USER_CLASSIC_HAIRSTYLE_EXTEND(0x198, EnumSet.of(State.IN_GAME)), "010001"), "payment"));
		assertEquals(2, field(read(new CM_USER_CLASSIC_HAIRSTYLE_EXTEND(0x198, EnumSet.of(State.IN_GAME)), "010002"), "payment"));
	}

	@Test
	void extendKeepsTheWholeBody() throws Exception {
		// cliente real em 21/09, pagando com Quna; a fonte 2.4 anota "use key in official = 01 00 02" para o item
		CM_USER_CLASSIC_WARDROBE_EXTEND quna = read(new CM_USER_CLASSIC_WARDROBE_EXTEND(0x189, EnumSet.of(State.IN_GAME)), "010001");
		assertArrayEquals(new byte[] { 1, 0, 1 }, (byte[]) field(quna, "body"));
		CM_USER_CLASSIC_WARDROBE_EXTEND item = read(new CM_USER_CLASSIC_WARDROBE_EXTEND(0x189, EnumSet.of(State.IN_GAME)), "010002");
		assertArrayEquals(new byte[] { 1, 0, 2 }, (byte[]) field(item, "body"));
	}

	@Test
	void rawOpcodesDecodeToTheCapturedOnes() {
		int[][] pares = { { 0x184, 0xEE }, { 0x185, 0xEF }, { 0x18A, 0xF8 }, { 0x18B, 0xF9 }, { 0x188, 0xFA }, { 0x189, 0xFB } };
		for (int[] par : pares)
			assertEquals(par[1], ((par[0] ^ 0x36) - 0xC4) & 0xFFFF, Integer.toHexString(par[0]));
	}

	private static <T extends AionClientPacket> T read(T packet, String hex) {
		packet.setBuffer(ByteBuffer.wrap(HexFormat.of().parseHex(hex)).order(ByteOrder.LITTLE_ENDIAN));
		assertTrue(packet.read());
		assertEquals(0, packet.getRemainingBytes());
		return packet;
	}

	private static Object field(Object packet, String name) throws Exception {
		for (Class<?> c = packet.getClass(); c != null; c = c.getSuperclass()) {
			try {
				Field f = c.getDeclaredField(name);
				f.setAccessible(true);
				return f.get(packet);
			} catch (NoSuchFieldException e) {
				// campo da superclasse
			}
		}
		throw new NoSuchFieldException(name);
	}
}
