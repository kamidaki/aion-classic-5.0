package com.aionemu.gameserver.world.knownlist;


public interface VisitorWithOwner<T, V> {

	void visit(T object, V owner);
}
