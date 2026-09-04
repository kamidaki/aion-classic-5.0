package com.aionemu.gameserver.services.siegeservice;

import com.aionemu.gameserver.ai.AbstractAI;
import com.aionemu.gameserver.ai.GeneralAIEvent;
import com.aionemu.gameserver.ai.eventcallback.OnDieEventCallback;
import com.aionemu.gameserver.ai.eventcallback.OnDieEventListener;
import com.aionemu.gameserver.services.SiegeService;

@SuppressWarnings("rawtypes")
public class SiegeBossDeathListener extends OnDieEventListener {

	private final Siege<?> siege;

	public SiegeBossDeathListener(Siege<?> siege) {
		this.siege = siege;
	}

	@Override
	public void onBeforeEvent(GeneralAIEvent event) {
		super.onBeforeEvent(event);
	}

	@Override
	public void onAfterEvent(GeneralAIEvent event) {
		if (event.isHandled()) {
			this.siege.setBossKilled(true);
			SiegeService.getInstance().stopSiege(this.siege.getSiegeLocationId());
		}
	}
}
