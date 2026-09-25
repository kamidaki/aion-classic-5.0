package com.aionemu.gameserver.network.aion.serverpackets;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.HexFormat;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * S_POLYMORPH (0x3A) contra as capturas oficiais: candy de panda marinho, candy invisivel e fim da transformacao (outros2, 2026-09-22 10:23)
 * e o cubo do tutorial num NPC (subida 1-60, 2026-08-28).
 */
class PolymorphPacketTest {

	private static final HexFormat HEX = HexFormat.of();

	@Test
	void candyTransformMatchesOfficialCapture() throws Exception {
		// 10498 Classic_Candy_D_SHAPE_sea_panda_Phy_01 -> NPC 202596 sea_panda_d_01
		assertEquals("d95b0f2e6417030001000000803e00000040000100000000000000000000000000000000000229",
			HEX.formatHex(body(player(0x2E0F5BD9, 202596, 10498))));
	}

	@Test
	void invisibleCandyUsesModelZero() throws Exception {
		// 10813 Classic_Candy_SHAPE_INVISIBLE_EXCHANGE_50 (reserved9 "0")
		assertEquals("8037462e0000000001000000803e00000040000100000000000000000000000000000000003d2a",
			HEX.formatHex(body(player(0x2E463780, 0, 10813))));
	}

	@Test
	void endOfTransformSendsTemplateWithoutSkill() throws Exception {
		assertEquals("d95b0f2ea386010001000000803e00000040000100000000000000000000000000000000000000",
			HEX.formatHex(body(player(0x2E0F5BD9, 100003, 0))));
	}

	@Test
	void npcKeepsItsOwnCollisionPair() throws Exception {
		// 19981 IDTutorialQ_NPC_Polymorph_Cube_2 no NPC 804156: 0.35/2.0 e o mesmo par do S_PUT_NPC dele
		SM_TRANSFORM p = new SM_TRANSFORM(0x8021D6E9, 804169, 0x21, 0.35f, 2.0f, 0, 0, 19981, false, false, false, false, false, false, false);
		assertEquals("e9d6218049450c0021003333b33e00000040000000000000000000000000000000000000000d4e", HEX.formatHex(body(p)));
	}

	private static SM_TRANSFORM player(int objectId, int modelId, int skillId) {
		return new SM_TRANSFORM(objectId, modelId, 1, 0.25f, 2.0f, 1, 0, skillId, false, false, false, false, false, false, false);
	}

	private static byte[] body(AionServerPacket packet) throws Exception {
		ByteBuffer buffer = ByteBuffer.allocate(64).order(ByteOrder.LITTLE_ENDIAN);
		packet.setBuf(buffer);
		Method method = null;
		for (Class<?> c = packet.getClass(); method == null; c = c.getSuperclass())
			method = Arrays.stream(c.getDeclaredMethods()).filter(m -> m.getName().equals("writeImpl")).findFirst().orElse(null);
		method.setAccessible(true);
		method.invoke(packet, new Object[] { (AionConnection) null });
		return Arrays.copyOf(buffer.array(), buffer.position());
	}
}
