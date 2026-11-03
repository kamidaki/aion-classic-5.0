package com.aionemu.gameserver.network.aion.serverpackets;

import java.lang.management.ManagementFactory;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;

/**
 * @author Lost Academy Team & Durak
 */
public class SM_TIME_CHECK extends AionServerPacket {

	private final int serverUpTime;
	private final int nanoTime;
	private final int time;
	private final int flag;

	public SM_TIME_CHECK(int nanoTime) {
		this(nanoTime, (int) (System.currentTimeMillis() / 1000), 2);
	}

	public SM_TIME_CHECK(int nanoTime, int time, int flag) {
		this.serverUpTime = (int) ManagementFactory.getRuntimeMXBean().getUptime();
		this.nanoTime = nanoTime;
		this.time = time;
		this.flag = flag;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(serverUpTime);
		writeD(nanoTime);
		writeD(time);
		writeD(flag);
	}
}
