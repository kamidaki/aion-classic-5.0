/**
 * This file is part of Aion-Lightning <aion-lightning.org>.
 *
 *  Aion-Lightning is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  Aion-Lightning is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details. *
 *  You should have received a copy of the GNU General Public License
 *  along with Aion-Lightning.
 *  If not, see <http://www.gnu.org/licenses/>.
 */


package com.aionemu.loginserver.network.aion;

import java.util.Arrays;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.aionemu.loginserver.network.ncrypt.BlowfishCipher;

/**
 * Diagnostico para quando o pacote do cliente nao decripta.
 *
 * "Wrong checksum from client" tem quase sempre a mesma causa: o cliente pegou a chave Blowfish de
 * um offset do SM_INIT diferente do que escrevemos. O sintoma nao aponta para o offset, entao esta
 * classe testa todas as janelas de 16 bytes da regiao da chave -- se alguma decriptar para um
 * checksum valido, o offset dela e onde o cliente realmente le.
 *
 * E ferramenta de bancada: so roda quando algo ja falhou, e o resultado vai para o log.
 */
public final class CryptDiagnostics {

	private static final Logger log = LoggerFactory.getLogger(CryptDiagnostics.class);

	/** Offset em SM_INIT onde comeca a regiao reconstruida abaixo. */
	private static final int REGION_START = 0x89;

	/** Chave estatica usada ate o SM_INIT trocar para a chave de sessao. */
	private static final byte[] STATIC_KEY = {
		(byte) 0x6b, (byte) 0x60, (byte) 0xcb, (byte) 0x5b,
		(byte) 0x82, (byte) 0xce, (byte) 0x90, (byte) 0xb1,
		(byte) 0xcc, (byte) 0x2b, (byte) 0x6c, (byte) 0x55,
		(byte) 0x6c, (byte) 0x6c, (byte) 0x6c, (byte) 0x6c
	};

	private CryptDiagnostics() {
	}

	/**
	 * Reconstroi SM_INIT de 0x89 ate o fim. Precisa ficar igual ao writeImpl do SM_INIT -- se um
	 * mudar sem o outro, o diagnostico passa a mentir.
	 */
	private static byte[] initTail(byte[] sessionKey) {
		byte[] region = new byte[40];                       // 0x89 .. 0xB0
		System.arraycopy(sessionKey, 0, region, 12, 16);    // 0x95 .. 0xA4
		region[27] = (byte) ClassicProtocol.INIT_RSA_ENABLE_FLAG;   // 0xA8
		region[28] = (byte) ClassicProtocol.CLIENT_VERSION_MAJOR;   // 0xA9
		region[29] = (byte) ClassicProtocol.CLIENT_VERSION_MINOR;   // 0xAA
		return region;
	}

	private static boolean checksumOk(byte[] data, int offset, int length) {
		if ((length & 3) != 0 || length <= 4) {
			return false;
		}
		long chksum = 0;
		int count = offset + length - 4;
		for (int i = offset; i < count; i += 4) {
			long check = data[i] & 0xff;
			check |= (data[i + 1] << 8) & 0xff00;
			check |= (data[i + 2] << 0x10) & 0xff0000;
			check |= ((long) data[i + 3] << 0x18) & 0xff000000L;
			chksum ^= check;
		}
		long last = data[count] & 0xff;
		last |= (data[count + 1] << 8) & 0xff00;
		last |= (data[count + 2] << 0x10) & 0xff0000;
		last |= ((long) data[count + 3] << 0x18) & 0xff000000L;
		return (chksum ^ last) == 0;
	}

	private static boolean decryptsWith(byte[] key, byte[] cipherText) {
		byte[] copy = cipherText.clone();
		new BlowfishCipher(key).decipher(copy, 0, copy.length);
		return checksumOk(copy, 0, copy.length);
	}

	private static String hex(byte[] data) {
		StringBuilder sb = new StringBuilder(data.length * 2);
		for (byte b : data) {
			sb.append(String.format("%02x", b));
		}
		return sb.toString();
	}

	/**
	 * Chamado quando o checksum falha. Registra os bytes crus e procura a chave que funcionaria.
	 *
	 * @param data buffer recebido
	 * @param offset inicio do pacote em data
	 * @param length tamanho do pacote
	 * @param sessionKey chave Blowfish que enviamos no SM_INIT
	 */
	public static void explainChecksumFailure(byte[] data, int offset, int length, byte[] sessionKey) {
		byte[] cipherText = Arrays.copyOfRange(data, offset, offset + length);

		log.warn("pacote do cliente nao decripta: {} bytes", length);
		log.warn("  cifrado    : {}", hex(cipherText));
		log.warn("  chave envia: {} (SM_INIT+0x95)", hex(sessionKey));

		if (decryptsWith(STATIC_KEY, cipherText)) {
			log.warn("  -> decripta com a CHAVE ESTATICA: o cliente nao trocou para a chave de sessao");
			return;
		}

		byte[] region = initTail(sessionKey);
		for (int w = 0; w + 16 <= region.length; w++) {
			byte[] candidate = Arrays.copyOfRange(region, w, w + 16);
			if (decryptsWith(candidate, cipherText)) {
				log.warn("  -> decripta com a chave em SM_INIT+0x{}: mova a chave Blowfish para la",
						Integer.toHexString(REGION_START + w));
				log.warn("     chave que funcionou: {}", hex(candidate));
				return;
			}
		}

		log.warn("  -> nenhuma janela da regiao da chave decripta. O problema nao e o offset:");
		log.warn("     ou o cliente cifra de outro jeito, ou o pacote nem e Blowfish.");
	}
}
