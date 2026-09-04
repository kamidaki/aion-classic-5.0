package com.aionemu.gameserver.model.team;


public interface TeamMember<M> {

    Integer getObjectId();

    String getName();

    M getObject();
}
