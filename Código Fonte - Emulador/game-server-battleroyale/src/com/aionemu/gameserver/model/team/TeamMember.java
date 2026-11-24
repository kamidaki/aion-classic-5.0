package com.aionemu.gameserver.model.team;

/**
 * @author Lost Academy Team & Durak
 */
public interface TeamMember<M> {

	int getObjectId();

	String getName();

	M getObject();
}
