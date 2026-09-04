package com.aionemu.chatserver.model.channel;

import com.aionemu.chatserver.model.ChannelType;
import com.aionemu.chatserver.model.Race;


public class LfgChannel extends RaceChannel {

    public LfgChannel(Race race, String identifier) {
        super(ChannelType.GROUP, race, identifier);
    }
}
