package com.aionemu.gameserver.model.team;


public interface TeamEvent {

    void handleEvent();

    boolean checkCondition();
}
