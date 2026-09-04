package com.aionemu.gameserver.world.knownlist;


@FunctionalInterface
public interface Visitor<T> {

	void visit(T object);
}
