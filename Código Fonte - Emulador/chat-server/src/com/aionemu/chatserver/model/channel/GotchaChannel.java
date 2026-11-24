package com.aionemu.chatserver.model.channel;

import com.aionemu.chatserver.model.ChannelType;
import com.aionemu.chatserver.model.Race;

/**
 * Canal do sistema de sorteio (gotcha) do 5.0. O cliente entra nele sozinho ao logar ("@\u0001gotcha...\u0001<servidor>.<raça>...");
 * o Game.dll tem o identificador "gotcha" junto dos de public/trade/partyFind, além de S_GOTCHA_NOTIFY e sys_UIfx.gotcha.*.
 */
public class GotchaChannel extends RaceChannel {

	public GotchaChannel(int gameServerId, Race race) {
		super(ChannelType.GOTCHA, gameServerId, race);
	}
}
