package com.aionemu.gameserver.model.templates;

import com.aionemu.gameserver.utils.ChatUtil;

/**
 * @author Lost Academy Team & Durak
 */
public interface L10n {

	/**
	 * @return The ID of the given client string
	 */
	public int getL10nId();

	/**
	 * @return String identifier for a client message.
	 * @see ChatUtil#l10n(int)
	 */
	public default String getL10n() {
		return ChatUtil.l10n(getL10nId());
	}

}
