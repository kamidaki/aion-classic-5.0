package com.aionemu.gameserver.network.aion.serverpackets;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * DIAGNOSTICO TEMPORARIO (01/10, chat e tela preta do Aion Look). Manda bytes crus da captura oficial com qualquer opcode, para achar por
 * eliminacao qual pacote de entrada no mundo o cliente espera. Le config/diag_entrada_oficial.txt (linhas "0xOPCODE payload_hex", # comenta);
 * sem o arquivo nao faz nada. Sai junto com o arquivo assim que o pacote certo for implementado de verdade.
 */
public class SM_DIAG_RAW extends AionServerPacket {

	private static final Logger log = LoggerFactory.getLogger(SM_DIAG_RAW.class);
	private static final Path FILE = Path.of("config", "diag_entrada_oficial.txt");

	private final byte[] payload;

	private SM_DIAG_RAW(int opcode, byte[] payload) {
		super(opcode);
		this.payload = payload;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeB(payload);
	}

	public static List<SM_DIAG_RAW> loadEnterWorldPackets() {
		List<SM_DIAG_RAW> packets = new ArrayList<>();
		if (!Files.exists(FILE))
			return packets;
		try {
			for (String line : Files.readAllLines(FILE)) {
				String s = line.strip();
				int hash = s.indexOf('#');
				if (hash >= 0)
					s = s.substring(0, hash).strip();
				if (s.isEmpty())
					continue;
				String[] parts = s.split("\\s+");
				int opcode = Integer.decode(parts[0]);
				byte[] payload = parts.length > 1 ? HexFormat.of().parseHex(parts[1]) : new byte[0];
				packets.add(new SM_DIAG_RAW(opcode, payload));
			}
			log.info("[DIAG] {} pacotes crus de {} na entrada no mundo", packets.size(), FILE);
		} catch (Exception e) {
			log.error("[DIAG] falha ao ler {}", FILE, e);
		}
		return packets;
	}
}
