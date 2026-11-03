package com.aionemu.gameserver.model.team;

/**
 * @author Lost Academy Team & Durak
 */
public interface TeamEvent {

	void handleEvent();

	boolean checkCondition();
}
