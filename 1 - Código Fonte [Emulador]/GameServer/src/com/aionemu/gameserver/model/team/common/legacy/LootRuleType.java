package com.aionemu.gameserver.model.team.common.legacy;


public enum LootRuleType {

    FREEFORALL(0),
    ROUNDROBIN(1),
    LEADER(2);
    private int id;

    private LootRuleType(int id) {
        this.id = id;
    }

    public int getId() {
        return this.id;
    }
}
