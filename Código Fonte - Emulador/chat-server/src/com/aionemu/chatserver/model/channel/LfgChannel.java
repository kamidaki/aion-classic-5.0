package com.aionemu.chatserver.model.channel;

import com.aionemu.chatserver.model.ChannelType;
import com.aionemu.chatserver.model.Race;

/**
 * @author Lost Academy Team & Durak
 */
public class LfgChannel extends RaceChannel {

	public LfgChannel(int gameServerId, Race race) {
		super(ChannelType.LFG, gameServerId, race);
	}
}
