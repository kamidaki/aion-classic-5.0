package com.aionemu.chatserver.utils;

import java.util.concurrent.atomic.AtomicInteger;

/**
 * @author Lost Academy Team & Durak
 */
public class IdFactory {

	private static final IdFactory instance = new IdFactory();

	private final AtomicInteger nextId = new AtomicInteger();

	public static IdFactory getInstance() {
		return instance;
	}

	public int nextId() {
		return nextId.incrementAndGet();
	}
}
