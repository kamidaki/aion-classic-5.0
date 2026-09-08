package com.aionemu.loginserver.model;

/**
 * @author Lost Academy Team & Durak
 */
public class ReconnectingAccount {

	/**
	 * Account object of account that will be reconnecting.
	 */
	private final Account account;
	/**
	 * Reconnection Key that will be used for authenticating
	 */
	private final int reconnectionKey;

	/**
	 * Constructor.
	 * 
	 * @param account
	 * @param reconnectionKey
	 */
	public ReconnectingAccount(Account account, int reconnectionKey) {
		this.account = account;
		this.reconnectionKey = reconnectionKey;
	}

	/**
	 * Return Account.
	 * 
	 * @return account
	 */
	public Account getAccount() {
		return account;
	}

	/**
	 * Return reconnection key for this account
	 * 
	 * @return reconnectionKey
	 */
	public int getReconnectionKey() {
		return reconnectionKey;
	}
}
