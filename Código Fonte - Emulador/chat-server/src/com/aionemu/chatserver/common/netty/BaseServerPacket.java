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
		buf.writeIntLE(value);
	}

	/**
	 * Write short to buffer
	 */
	protected final void writeH(ByteBuf buf, int value) {
		buf.writeShortLE((short) value);
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
		buf.writeDoubleLE(value);
	}

	/**
	 * Write float to buffer
	 */
	protected final void writeF(ByteBuf buf, float value) {
		buf.writeFloatLE(value);
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
				buf.writeShortLE((short) text.charAt(i));
		}
		buf.writeShortLE(0);
	}

	/**
	 * Write long to buffer
	 */
	protected final void writeQ(ByteBuf buf, long data) {
		buf.writeLongLE(data);
	}
}
