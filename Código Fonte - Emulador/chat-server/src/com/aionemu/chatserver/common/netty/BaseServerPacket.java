package com.aionemu.chatserver.common.netty;

import io.netty.buffer.ByteBuf;

/**
 * @author Lost Academy Team & Durak
 */
public abstract class BaseServerPacket extends AbstractPacket {

	public BaseServerPacket(byte opCode) {
		super(opCode);
	}

	/**
	 * Write int to buffer
	 */
	protected final void writeD(ByteBuf buf, int value) {
		buf.writeInt(value);
	}

	/**
	 * Write short to buffer
	 */
	protected final void writeH(ByteBuf buf, int value) {
		buf.writeShort((short) value);
	}

	/**
	 * Write byte to Buffer
	 */
	protected final void writeC(ByteBuf buf, int value) {
		buf.writeByte((byte) value);
	}

	/**
	 * Write double to buffer
	 */
	protected final void writeDF(ByteBuf buf, double value) {
		buf.writeDouble(value);
	}

	/**
	 * Write float to buffer
	 */
	protected final void writeF(ByteBuf buf, float value) {
		buf.writeFloat(value);
	}

	/**
	 * Write byte array to buffer
	 */
	protected final void writeB(ByteBuf buf, byte[] data) {
		buf.writeBytes(data);
	}

	/**
	 * Write String to buffer
	 */
	protected final void writeS(ByteBuf buf, String text) {
		if (text != null) {
			final int len = text.length();
			for (int i = 0; i < len; i++)
				buf.writeChar(text.charAt(i));
		}
		buf.writeChar('\000');
	}

	/**
	 * Write long to buffer
	 */
	protected final void writeQ(ByteBuf buf, long data) {
		buf.writeLong(data);
	}
}
