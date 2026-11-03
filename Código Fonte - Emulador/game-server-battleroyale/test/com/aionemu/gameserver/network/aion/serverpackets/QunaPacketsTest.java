package com.aionemu.gameserver.network.aion.serverpackets;

import static org.junit.jupiter.api.Assertions.*;

import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.HexFormat;

import org.junit.jupiter.api.Test;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import com.aionemu.gameserver.services.player.QunaService;

/**
 * S 0x11B e mensagens de Quna contra as capturas: retune do Brawler (14/09), compra na Auction House (21/09 05:50) e troca de cabelo (21/09
 * 14:56), todas da mesma conta.
 */
class QunaPacketsTest {

	private static final HexFormat HEX = HexFormat.of();

	@Test
	void balanceMatchesOfficialCaptures() throws Exception {
		assertEquals("5c016302000000000000", HEX.formatHex(body(new SM_QUNA(0x15C, 611)))); // retune, -60
		assertEquals("2f01ca01000000000000", HEX.formatHex(body(new SM_QUNA(0x12F, 458)))); // Auction House, -33
		assertEquals("4901b601000000000000", HEX.formatHex(body(new SM_QUNA(0x149, 438)))); // cabelo, -20
	}

	@Test
	void spentAmountGoesAsText() throws Exception {
		assertEquals("190000000000e66215000132003000000000", HEX.formatHex(body(new SM_SYSTEM_MESSAGE(1401574, "20"))));
		assertEquals("190000000000bf6315000133003300000000", HEX.formatHex(body(new SM_SYSTEM_MESSAGE(1401791, "33"))));
	}

	@Test
	void currencyItemsAreQuna() {
		assertTrue(QunaService.isQunaItem(182499000));
		assertTrue(QunaService.isQunaItem(182499001));
		assertFalse(QunaService.isQunaItem(186000166));
	}

	private static byte[] body(AionServerPacket packet) throws Exception {
		ByteBuffer buffer = ByteBuffer.allocate(256).order(ByteOrder.LITTLE_ENDIAN);
		packet.setBuf(buffer);
		Method method = null;
		for (Class<?> c = packet.getClass(); method == null; c = c.getSuperclass())
			method = Arrays.stream(c.getDeclaredMethods()).filter(m -> m.getName().equals("writeImpl")).findFirst().orElse(null);
		method.setAccessible(true);
		method.invoke(packet, new Object[] { (AionConnection) null });
		return Arrays.copyOf(buffer.array(), buffer.position());
	}
}
