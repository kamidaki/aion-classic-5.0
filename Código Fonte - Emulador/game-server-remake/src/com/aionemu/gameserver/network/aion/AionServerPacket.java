package com.aionemu.gameserver.network.aion;

import java.nio.ByteBuffer;

import com.aionemu.commons.network.packet.BaseServerPacket;
import com.aionemu.gameserver.model.gameobjects.player.PlayerAppearance;
import com.aionemu.gameserver.network.Crypt;

/**
 * @author Lost Academy Team & Durak
 */
public abstract class AionServerPacket extends BaseServerPacket {

	public static final int MAX_CLIENT_SUPPORTED_PACKET_SIZE = 8192;
	public static final int MAX_USABLE_PACKET_BODY_SIZE = MAX_CLIENT_SUPPORTED_PACKET_SIZE - 7; // 8192 - 2 (body length) - 2 (opCode) - 1 (staticServerPacketCode) - 2 (opCode flipped bits)

	public static int byteLengthForString(String text) {
		if (text == null || text.isEmpty())
			return 2;
		return (text.length() + 1) * 2;
	}

	public static int byteLengthForFixedString(int fixedLength) {
		return (fixedLength + 1) * 2;
	}

	/**
	 * Constructs new server packet
	 */
	protected AionServerPacket() {
		super();
		setOpCode(ServerPacketsOpcodes.getOpcode(getClass()));
	}

	protected AionServerPacket(int opCode) {
		super(opCode);
	}

	/**
	 * Write packet opCode and two additional bytes
	 */
	private void writeOP() {
		// obfuscate packet id
		int op = Crypt.encodeServerPacketOpcode(getOpCode());
		buf.putShort((short) (op));
		// put static server packet code
		buf.put(Crypt.staticServerPacketCode);
		// for checksum?
		buf.putShort((short) (~op));
	}

	/**
	 * Write and encrypt this packet data for given connection, to given buffer.
	 * 
	 * @param con
	 * @param buf
	 */
	public final void write(AionConnection con, ByteBuffer buffer) {
		setBuf(buffer);
		buf.putShort((short) 0);
		writeOP();
		writeImpl(con);
		buf.flip();
		buf.putShort((short) buf.limit());
		ByteBuffer b = buf.slice();
		buf.position(0);
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
	 * Write string to buffer with a fixed length. Characters exceeding fixedLength will be truncated. Missing ones will be zero-padded.
	 * The number of written bytes to the buffer is fixedLength * 2 + 2. The additional two bytes are the terminating (zero) char which the client
	 * always requires. One could actually populate that last char normally and it would be displayed on client side, but then following data may get
	 * corrupted.
	 */
	protected final void writeS(String text, int fixedLength) {
		if (text == null || text.isEmpty()) {
			buf.put(new byte[byteLengthForFixedString(fixedLength)]);
		} else {
			for (int i = 0; i < fixedLength; i++)
				buf.putChar(i < text.length() ? text.charAt(i) : '\000');
			buf.putChar('\000');
		}
	}

	/**
	 * Writes dye information (dye status + 3 byte RGB value) to the buffer.
	 * 
	 * @param rgb
	 *          - may be null
	 */
	protected final void writeDyeInfo(Integer rgb) {
		if (rgb == null) {
			writeB(new byte[4]);
		} else {
			writeC(1); // dye status (1 = dyed, 0 = not dyed)
			writeC((rgb & 0xFF0000) >> 16); // r
			writeC((rgb & 0xFF00) >> 8); // g
			writeC(rgb & 0xFF); // b
		}
	}

	@Override
	protected int getOpCodeZeroPadding() {
		return 3;
	}

	/**
	 * Aparência como no S_PUT_USER: as 4 cores e os 51 bytes de rosto e corpo, sem a voz. O S_STATUS_OTHER do 5.0 (S 0x02) leva os
	 * mesmos 67 bytes (Kodra, captura outros 2026-09-21 06:10, igual byte a byte ao S_PUT_USER dele).
	 */
	protected void writeAppearance(PlayerAppearance appearance) {
		writeD(appearance.getSkinRGB());
		writeD(appearance.getHairRGB());
		writeD(appearance.getEyeRGB());
		writeD(appearance.getLipRGB());
		writeC(appearance.getFace());
		// cabelo = H no offset 0x11 da aparência: o Game.dll lê word ptr [+0x11] e soma 1 para o %s%03d_Hair.cgf (0x3907fe); os penteados de
		// tintura especial vão de 20000 a 20027 (df20001_hair...). O byte que vinha depois, como "deco", é o byte alto deste H.
		writeH(appearance.getHair());
		writeC(appearance.getTattoo());
		writeC(appearance.getFaceContour());
		writeC(appearance.getExpression());
		writeC(appearance.getFaceExpression());
		writeC(appearance.getJawLine());
		writeC(appearance.getForehead());
		writeC(appearance.getEyeHeight());
		writeC(appearance.getEyeSpace());
		writeC(appearance.getEyeWidth());
		writeC(appearance.getEyeSize());
		writeC(appearance.getEyeShape());
		writeC(appearance.getEyeAngle());
		writeC(appearance.getBrowHeight());
		writeC(appearance.getBrowAngle());
		writeC(appearance.getBrowShape());
		writeC(appearance.getNose());
		writeC(appearance.getNoseBridge());
		writeC(appearance.getNoseWidth());
		writeC(appearance.getNoseTip());
		writeC(appearance.getCheek());
		writeC(appearance.getLipHeight());
		writeC(appearance.getMouthSize());
		writeC(appearance.getLipSize());
		writeC(appearance.getSmile());
		writeC(appearance.getLipShape());
		writeC(appearance.getJawHeigh());
		writeC(appearance.getChinJut());
		writeC(appearance.getEarShape());
		writeC(appearance.getHeadSize());
		writeC(appearance.getNeck());
		writeC(appearance.getNeckLength());
		writeC(appearance.getShoulderSize());
		writeC(appearance.getTorso());
		writeC(appearance.getChest());
		writeC(appearance.getWaist());
		writeC(appearance.getHips());
		writeC(appearance.getArmThickness());
		writeC(appearance.getHandSize());
		writeC(appearance.getLegThickness());
		writeC(appearance.getFootSize());
		writeC(appearance.getFacialRate());
		writeC(0x00);
		writeC(appearance.getArmLength());
		writeC(appearance.getLegLength());
		writeC(appearance.getShoulders());
		writeC(appearance.getFaceShape());
		writeC(0x00);
		writeC(0x00);
	}

	protected void writeNameId(int nameId) {
		writeH(0x24);
		writeD(nameId);
		writeH(0x00);
	}
}
