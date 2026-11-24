package com.aionemu.gameserver.model.templates.mail;

/**
 * @author Lost Academy Team & Durak
 */
public interface IMailFormatter {

	MailPartType getType();

	String getFormattedString(MailPartType partType);

	String getParamValue(String name);
}
