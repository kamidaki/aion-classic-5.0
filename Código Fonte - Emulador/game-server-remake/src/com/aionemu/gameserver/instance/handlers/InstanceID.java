package com.aionemu.gameserver.instance.handlers;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * @author Lost Academy Team & Durak
 */
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface InstanceID {

	/**
	 * @return id of the instance
	 */
	int value();
}
