package com.aionemu.gameserver.utils.idfactory;

/**
 * @author Lost Academy Team & Durak
 */
public class IDFactoryError extends Error {

	private static final long serialVersionUID = 6945059882804355687L;

	public IDFactoryError(String message) {
		super(message);
	}

	public IDFactoryError(String message, Throwable cause) {
		super(message, cause);
	}

	public IDFactoryError(Throwable cause) {
		super(cause);
	}
}
