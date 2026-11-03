package com.aionemu.gameserver.network.aion.serverpackets;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.model.gameobjects.BlackCloudGoods;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Black Cloud Mail contra a captura oficial 06_Sistemas_Novos_Black_Cloud_Mail_5.0_2026-09-14 (S 0x10C e S 0x10D).
 */
class NpshopGoodsTest {

	private static final String OFFICIAL_LIST = "00000000010400d1113000000000005b004500760065006e0074005d00200045006e006300680061006e0074006d0065006e0074002000530074006f"
		+ "006e006500200028004c006500760065006c0020003100310030002900200028003100300029000000000000cf215895ffffffff94e3a46a00000000"
		+ "0000000000000000010100d6f9e4090a0000000000000000000000ff7f0000020000000000000050000000d0113000000000005b004500760065006e"
		+ "0074005d0020004d0061006a006f007200200041006e006300690065006e0074002000430072006f0077006e00200043006800650073007400200028"
		+ "0031003000200070006900650063006500730029000000000000cf215895ffffffff94e3a46a0000000000000000000000000101007c72350b010000"
		+ "000000000000000000ff7f0000020000000000000050000000cf113000000000005b004500760065006e0074005d002000520061007200650020004d"
		+ "0061006e006100730074006f006e0065002000420061006700200028004c006500760065006c00200036003000290020002800310030002900000000"
		+ "0000cf215895ffffffff94e3a46a0000000000000000000000000101006b74350b0a0000000000000000000000ff7f00000200000000000000500000"
		+ "00ce113000000000004d00690074006800720069006c0020004d006500640061006c00200028003100300029000000000000cf215895ffffffff94e3"
		+ "a46a0000000000000000000000000101003e23160b0a0000000000000000000000ff7f0000020000000000000050000000";
	private static final long OFFICIAL_REFUND = 0xFFFFFFFF955821CFL; // 0 - agora, no instante da captura
	private static final int REGISTERED = 0x6AA4E394;

	private static final List<BlackCloudGoods> CAPTURED_GOODS = List.of(
		new BlackCloudGoods(0x3011D1, 1, "[Event] Enchantment Stone (Level 110) (10)", 0x09E4F9D6, 10, REGISTERED),
		new BlackCloudGoods(0x3011D0, 1, "[Event] Major Ancient Crown Chest (10 pieces)", 0x0B35727C, 1, REGISTERED),
		new BlackCloudGoods(0x3011CF, 1, "[Event] Rare Manastone Bag (Level 60) (10)", 0x0B35746B, 10, REGISTERED),
		new BlackCloudGoods(0x3011CE, 1, "Mithril Medal (10)", 0x0B16233E, 10, REGISTERED));

	@Test
	void goodsListMatchesOfficialCapture() throws Exception {
		long before = System.currentTimeMillis() / 1000;
		byte[] body = body(new SM_NPSHOP_GOODS_LIST(CAPTURED_GOODS));
		long after = System.currentTimeMillis() / 1000;
		byte[] official = HexFormat.of().parseHex(OFFICIAL_LIST);
		assertEquals(589, official.length);
		assertEquals(official.length, body.length);

		// o reembolso depende da hora: confere o valor e troca pelo da captura antes de comparar byte a byte
		ByteBuffer buf = ByteBuffer.wrap(body).order(ByteOrder.LITTLE_ENDIAN);
		int offset = SM_NPSHOP_GOODS_LIST.STATIC_BODY_SIZE;
		for (BlackCloudGoods g : CAPTURED_GOODS) {
			int refundOffset = offset + 8 + AionServerPacket.byteLengthForString(g.name()) + 3;
			long refund = buf.getLong(refundOffset);
			assertTrue(refund <= -before && refund >= -after, "reembolso deve ser 0 - agora");
			buf.putLong(refundOffset, OFFICIAL_REFUND);
			offset += SM_NPSHOP_GOODS_LIST.bodySize(g);
		}
		assertEquals(body.length, offset);
		assertArrayEquals(official, body);
	}

	@Test
	void emptyGoodsListMatchesOfficialCapture() throws Exception {
		assertEquals("00000000010000", HexFormat.of().formatHex(body(new SM_NPSHOP_GOODS_LIST(List.of()))));
	}

	@Test
	void goodsReceiveMatchesOfficialCapture() throws Exception {
		assertEquals("ce1130000000000000000000", HexFormat.of().formatHex(body(new SM_NPSHOP_GOODS_RECV(0x3011CE, SM_NPSHOP_GOODS_RECV.SUCCESS))));
		assertEquals("04000000", HexFormat.of().formatHex(body(new SM_NPSHOP_GOODS_COUNT(4))));
	}

	private static byte[] body(AionServerPacket packet) throws Exception {
		ByteBuffer buffer = ByteBuffer.allocate(8192).order(ByteOrder.LITTLE_ENDIAN);
		packet.setBuf(buffer);
		var method = packet.getClass().getDeclaredMethod("writeImpl", AionConnection.class);
		method.setAccessible(true);
		method.invoke(packet, new Object[] { null });
		return Arrays.copyOf(buffer.array(), buffer.position());
	}
}
