package com.aionemu.gameserver.network.aion.serverpackets;

import com.aionemu.gameserver.model.templates.world.WeatherEntry;
import com.aionemu.gameserver.network.aion.AionConnection;
import com.aionemu.gameserver.network.aion.AionServerPacket;


public class S_WEATHER extends AionServerPacket {

	private WeatherEntry[] weatherEntries;

	public S_WEATHER(WeatherEntry[] weatherEntries) {
		this.weatherEntries = weatherEntries;
	}

	@Override
	protected void writeImpl(AionConnection con) {
		writeC(0x00);// unk
		writeC(weatherEntries.length);
		for (WeatherEntry entry : weatherEntries)
			writeC(entry.getCode());
	}
}
