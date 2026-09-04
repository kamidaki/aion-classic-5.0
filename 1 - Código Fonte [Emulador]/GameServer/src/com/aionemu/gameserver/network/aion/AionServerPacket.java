package com.aionemu.gameserver.network.aion;

import com.aionemu.commons.network.packet.BaseServerPacket;
import com.aionemu.gameserver.configs.network.NetworkConfig;
import com.aionemu.gameserver.network.Crypt;
import com.aionemu.gameserver.network.aion.serverpackets.S_MESSAGE;
import com.aionemu.gameserver.utils.PacketSendUtility;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.Buffer;
import java.nio.ByteBuffer;

/**
 * Base class for every GS -> Aion Server Packet.
 * 
 */
public abstract class AionServerPacket extends BaseServerPacket {

	private static final Logger log = LoggerFactory.getLogger(AionServerPacket.class);

	/**
	 * Constructs new server packet
	 */
	protected AionServerPacket() {
		super();
		setOpcode(ServerPacketsOpcodes.getOpcode(getClass()));
	}

	/**
	 * Para pacotes cujo opcode nao vem da classe. Existe para o {@link RajadaOficial}, que
	 * reproduz corpos lidos da captura sem ter uma classe por opcode.
	 */
	protected AionServerPacket(int opcode) {
		super();
		setOpcode(opcode);
	}

	/**
	 * Write packet opcodec and two additional bytes
	 * 
	 * @param buf
	 * @param value
	 */
	private final void writeOP(int value) {
		/** obfuscate packet id */
		int op = Crypt.encodeOpcodec(value);
		buf.putShort((short) (op));

		/** put static server packet code */
		buf.put(Crypt.staticServerPacketCode);

		/** for checksum? */
		buf.putShort((short) (~op));

		// log.info("op : " + op);
		// log.info("op 2 : " + ~op);

	}

	public final void write(AionConnection con) {
		write(con, buf);
	}

	/**
	 * Write and encrypt this packet data for given connection, to given buffer.
	 * 
	 * @param con
	 * @param buf
	 */
	public final void write(AionConnection con, ByteBuffer buffer) {
		if (log.isDebugEnabled()) {
			log.debug(String.format("[REDE -> SERVIDOR] Enviando %s (Opcode=0x%04X, State=%s)", getClass().getSimpleName(),
					getOpcode(), con.getState()));
		}
		if (con.getState().equals(AionConnection.State.IN_GAME) && con.getActivePlayer() != null
				&& con.getActivePlayer().getPlayerAccount() != null
				&& con.getActivePlayer().getPlayerAccount().getAccessLevel() == 5 && NetworkConfig.DISPLAY_PACKETS) {
			// O eco e feito com um S_MESSAGE, entao ecoar um S_MESSAGE realimenta a si mesmo. A
			// guarda existia, mas comparava com a string "SM_MESSAGE", nome anterior a renomeacao
			// dos pacotes -- nunca casava. Em 2026-09-03 isso gerou 8,7 milhoes de pacotes e 1,8 GB
			// de rastro no instante em que uma conta virou accessLevel 5. Comparar com o tipo, e
			// nao com o nome, para nao quebrar de novo numa renomeacao.
			if (!(this instanceof S_MESSAGE)) {
				PacketSendUtility.sendMessage(con.getActivePlayer(),
						"0x" + Integer.toHexString(this.getOpcode()).toUpperCase() + " : " + this.getPacketName());
			}
		}
		this.setBuf(buffer);
		buf.putShort((short) 0);
		writeOP(getOpcode());
		writeImpl(con);
		((Buffer) buf).flip();
		if (WireTrace.ativo()) {
			WireTrace.servidor(con, getOpcode(), buf.limit() - 7, getClass().getSimpleName(),
				WireTrace.hexDe(buf, 7, buf.limit() - 7));
		}
		buf.putShort((short) buf.limit());
		ByteBuffer b = buf.slice();
		((Buffer) buf).position(0);
		con.encrypt(b);
	}

	/**
	 * Write data that this packet represents to given byte buffer.
	 * 
	 * @param con
	 */
	protected void writeImpl(AionConnection con) {

	}

	public final ByteBuffer getBuf() {
		return this.buf;
	}

	/**
	 * Write String to buffer
	 * 
	 * @param text
	 * @param size
	 */
	protected final void writeS(String text, int size) {
		if (text == null) {
			buf.put(new byte[size]);
		} else {
			final int len = text.length();
			for (int i = 0; i < len; i++)
				buf.putChar(text.charAt(i));
			buf.put(new byte[size - (len * 2)]);
		}
	}

	protected void writeNameId(int nameId) {
		writeH(0x24);
		writeD(nameId);
		writeH(0x00);
	}
}
