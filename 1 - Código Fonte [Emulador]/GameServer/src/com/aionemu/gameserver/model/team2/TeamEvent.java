package com.aionemu.gameserver.model.team2;


public interface TeamEvent {

    void handleEvent();

    boolean checkCondition();
}
