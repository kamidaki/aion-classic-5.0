package com.aionemu.gameserver.utils;

/**
 * @author Lost Academy Team & Durak
 */
public class TimeUtil {

	/**
	 * Check whether supplied time in ms is expired
	 */
	public static final boolean isExpired(long time) {
		return time < System.currentTimeMillis();
	}
}
