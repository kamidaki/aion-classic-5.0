package com.aionemu.gameserver.controllers.observer;

/**
 * @author Lost Academy Team & Durak
 */
public class StartMovingListener extends ActionObserver {

	private boolean effectorMoved = false;

	public StartMovingListener() {
		super(ObserverType.MOVE);
	}

	/**
	 * @return the effectorMoved
	 */
	public boolean isEffectorMoved() {
		return effectorMoved;
	}

	@Override
	public void moved() {
		effectorMoved = true;
	}
}
