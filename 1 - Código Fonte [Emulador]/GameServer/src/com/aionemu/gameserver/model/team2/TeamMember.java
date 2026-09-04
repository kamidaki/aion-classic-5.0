package com.aionemu.gameserver.model.team2;


public interface TeamMember<M> {

    Integer getObjectId();

    String getName();

    M getObject();
}
