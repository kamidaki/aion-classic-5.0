package com.aionemu.gameserver.model.instance;

public enum InstanceCoolTimeType
{
    RELATIVE,
    WEEKLY,
    DAILY;
	
    public boolean isRelative() {
        return this.equals(InstanceCoolTimeType.RELATIVE);
    }
	
    public boolean isWeekly() {
        return this.equals(InstanceCoolTimeType.WEEKLY);
    }
	
    public boolean isDaily() {
        return this.equals(InstanceCoolTimeType.DAILY);
    }
}