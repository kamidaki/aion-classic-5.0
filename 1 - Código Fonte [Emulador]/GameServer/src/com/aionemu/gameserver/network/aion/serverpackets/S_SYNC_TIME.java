package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;
import org.apache.commons.lang.math.RandomUtils;

import java.sql.Timestamp;
import java.util.Random;

/**
 * I have no idea wtf is this
 * 
 */
public class S_SYNC_TIME extends AionServerPacket {

	// Don't be fooled with empty class :D
	// This packet is just sending opcode, without any content

	// 1.5.x sending 8 bytes

	private int nanoTime;
	private int time;
	private Timestamp dateTime;

	public S_SYNC_TIME(int nanoTime) {
		this.dateTime = new Timestamp((new java.util.Date()).getTime());
		this.nanoTime = nanoTime;
		this.time = (int) dateTime.getTime();
	}

	/**
	 * {@inheritDoc}
	 */

	@Override
	protected void writeImpl(AionConnection con) {
		writeD(RandomUtils.nextInt());
		writeD(nanoTime);
		writeD(RandomUtils.nextInt());
		/*
		 * O ultimo campo e um numero de sequencia por conexao, nao uma constante: na captura
		 * oficial as sincronias que antecedem o CM_LEVEL_READY vem com 2 e depois 3, e o cliente
		 * devolve o mesmo valor no seu CM_TIME_CHECK de confirmacao.
		 */
		writeD(con.proximaSequenciaSyncTime());
	}
}
