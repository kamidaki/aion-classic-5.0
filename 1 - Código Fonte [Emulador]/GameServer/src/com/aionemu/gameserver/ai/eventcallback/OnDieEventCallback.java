package com.aionemu.gameserver.ai.eventcallback;

import com.aionemu.gameserver.ai.AbstractAI;
import com.aionemu.gameserver.ai.GeneralAIEvent;
import com.aionemu.gameserver.ai.event.AIEventType;
import com.aionemu.gameserver.events.EventListener;

/**
 * Callback for {@link AIEventType#DIED} event
 *
 */
public abstract class OnDieEventCallback implements EventListener<GeneralAIEvent> {

	@Override
	public void onBeforeEvent(GeneralAIEvent event) {
		if (AIEventType.DIED == event.getEventType()) {
			event.setHandled(true);
		}
	}

	@Override
	public void onAfterEvent(GeneralAIEvent event) {
		if (AIEventType.DIED == event.getEventType()) {
			event.setHandled(true);
		}
	}
}
