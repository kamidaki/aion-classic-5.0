package com.aionemu.loginserver.taskmanager;

import com.aionemu.loginserver.model.Account;


public interface IExpirable {

	public long getExpireTime();

	public void expireEnd(Account account);

	public boolean canExpireNow();

	public void expireMessage(Account account, long time);

}
