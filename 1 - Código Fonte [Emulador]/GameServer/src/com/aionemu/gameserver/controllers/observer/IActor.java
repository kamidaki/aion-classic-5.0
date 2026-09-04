package com.aionemu.gameserver.controllers.observer;


public interface IActor {

	void act();
	
	void setEnabled(boolean enable);

	void abort();
}
