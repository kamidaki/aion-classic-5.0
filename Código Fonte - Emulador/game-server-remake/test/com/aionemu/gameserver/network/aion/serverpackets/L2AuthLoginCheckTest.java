package com.aionemu.gameserver.network.aion.serverpackets;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * Teste unitario de conformidade do pacote SM_L2AUTH_LOGIN_CHECK (0xC6 / 198)
 * com as capturas oficiais do Aion Classic 5.0 (Wireshark).
 */
class L2AuthLoginCheckTest {

	private static final int OFFICIAL_STATIC_LENGTH = 1283; // 579 tabela + 2 qtd + 117 * 6 entradas
	private static final int OFFICIAL_TOTAL_MAPS = 117;
	private static final int OFFICIAL_PCAP_BODY_LENGTH = 1305; // com conta de 8 caracteres "40856603"

	@Test
	void testStaticDataStructureAndMapEntries() {
		byte[] staticData = SM_L2AUTH_LOGIN_CHECK.getStaticData();
		assertNotNull(staticData);
		assertEquals(OFFICIAL_STATIC_LENGTH, staticData.length, "Tamanho dos dados estaticos deve ser exatamente 1283 bytes");

		ByteBuffer buf = ByteBuffer.wrap(staticData).order(ByteOrder.LITTLE_ENDIAN);

		// 1) Tabela estatica de 579 bytes (0x243)
		byte[] table = new byte[579];
		buf.get(table);
		assertEquals((byte) 0x00, table[0]);
		assertEquals((byte) 0x3F, table[table.length - 1]);

		// 2) Quantidade de mapas (H = 2 bytes)
		int count = Short.toUnsignedInt(buf.getShort());
		assertEquals(OFFICIAL_TOTAL_MAPS, count, "Quantidade de mapas deve ser exatamente 117");

		// 3) Leitura e validacao das 117 entradas
		Map<Integer, Integer> mapChannels = new HashMap<>();
		for (int i = 0; i < count; i++) {
			int mapId = buf.getInt();
			int channels = Short.toUnsignedInt(buf.getShort());
			mapChannels.put(mapId, channels);
		}

		assertEquals(OFFICIAL_TOTAL_MAPS, mapChannels.size());
		assertEquals(0, buf.remaining(), "Nao deve haver bytes soltos ou sobrando");

		// Mapas essenciais e correções medidas contra o oficial:
		assertEquals(1, mapChannels.get(400010000)); // Sanctum / Elyos capital
		assertEquals(20, mapChannels.get(120030000)); // Pandaemonium Entrance (faltava no emulador)
		assertEquals(1, mapChannels.get(120040000));  // Habrok (faltava no emulador)
		assertEquals(20, mapChannels.get(110030000)); // Sanctum Gate (faltava no emulador)
		assertEquals(1, mapChannels.get(110040000));  // Griffoen (faltava no emulador)
		assertEquals(10, mapChannels.get(210080000)); // Lacrima Elyos (faltava no emulador)
		assertEquals(10, mapChannels.get(220090000)); // Lacrima Asmo (faltava no emulador)
		assertEquals(1, mapChannels.get(800030000));  // Laphsaran (faltava no emulador)
		assertEquals(1, mapChannels.get(800050000));  // Sunshara Isle Lobby (faltava no emulador)
		assertEquals(0, mapChannels.get(390000000));  // Land of Shadows (faltava no emulador)

		// Correção de canais oficiais 5.0 (emulador tinha 10, oficial tem 20):
		assertEquals(20, mapChannels.get(210010000)); // Poeta = 20 canais
		assertEquals(20, mapChannels.get(220010000)); // Ishalgen = 20 canais

		// Mapa que estava sobrando incorretamente no emulador antigo:
		assertFalse(mapChannels.containsKey(300560000), "Mapa obsoleto 300560000 nao deve constar no Classic 5.0");
	}

	@Test
	void testPacketMatchesOfficialCaptureLengthAndStructure() throws Exception {
		// Simula exatamente a conta capturada no Wireshark oficial ("40856603")
		SM_L2AUTH_LOGIN_CHECK packet = new SM_L2AUTH_LOGIN_CHECK(true, "40856603");
		byte[] body = extractPacketBody(packet);

		assertEquals(OFFICIAL_PCAP_BODY_LENGTH, body.length,
			"Payload completo deve ter exatamente 1305 bytes como nas capturas oficiais");

		ByteBuffer buf = ByteBuffer.wrap(body).order(ByteOrder.LITTLE_ENDIAN);

		// D ok = 0
		int ok = buf.getInt();
		assertEquals(0, ok, "D ok deve ser 0 para login bem-sucedido");

		// Pula 1283 bytes estaticos (tabela + entradas)
		byte[] staticPart = new byte[OFFICIAL_STATIC_LENGTH];
		buf.get(staticPart);
		assertArrayEquals(SM_L2AUTH_LOGIN_CHECK.getStaticData(), staticPart);

		// String UTF-16LE com terminador nulo
		byte[] strBytes = new byte[buf.remaining()];
		buf.get(strBytes);
		assertEquals(18, strBytes.length); // 8 chars * 2 + 2 null bytes = 18 bytes
		String accountDecoded = new String(strBytes, 0, strBytes.length - 2, StandardCharsets.UTF_16LE);
		assertEquals("40856603", accountDecoded);
	}

	@Test
	void testAccountStringHasNoSdPrefix() throws Exception {
		SM_L2AUTH_LOGIN_CHECK packet = new SM_L2AUTH_LOGIN_CHECK(true, "admin");
		byte[] body = extractPacketBody(packet);

		// 4 (ok) + 1283 (static) + 12 (5 chars * 2 + 2 nulo) = 1299 bytes
		assertEquals(1299, body.length);

		String rawHex = HexFormat.of().formatHex(body);
		// Verifica que o padrao hex de "_sd_" ou "sd" nao esta presente antes do nome
		// "_sd_" em UTF-16LE seria: 5f 00 73 00 64 00 5f 00
		assertFalse(rawHex.contains("5f00730064005f00"), "Pacote nao deve conter prefixo legado _sd_");

		// Verifica que a string final decodifica corretamente para "admin"
		ByteBuffer buf = ByteBuffer.wrap(body).order(ByteOrder.LITTLE_ENDIAN);
		buf.position(4 + OFFICIAL_STATIC_LENGTH);
		byte[] strBytes = new byte[buf.remaining()];
		buf.get(strBytes);
		String decoded = new String(strBytes, 0, strBytes.length - 2, StandardCharsets.UTF_16LE);
		assertEquals("admin", decoded);
	}

	private static byte[] extractPacketBody(AionServerPacket packet) throws Exception {
		ByteBuffer buffer = ByteBuffer.allocate(4096).order(ByteOrder.LITTLE_ENDIAN);
		packet.setBuf(buffer);
		var method = packet.getClass().getDeclaredMethod("writeImpl", AionConnection.class);
		method.setAccessible(true);
		method.invoke(packet, new Object[] { null });
		return Arrays.copyOf(buffer.array(), buffer.position());
	}
}
