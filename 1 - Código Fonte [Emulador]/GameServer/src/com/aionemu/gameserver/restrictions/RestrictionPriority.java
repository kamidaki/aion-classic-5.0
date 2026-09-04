package com.aionemu.gameserver.restrictions;

import java.lang.annotation.*;


@Inherited
@Retention(RetentionPolicy.RUNTIME)
@Target({ ElementType.TYPE, ElementType.METHOD })
public @interface RestrictionPriority {

	public static final double DEFAULT_PRIORITY = 0.0;

	double value() default DEFAULT_PRIORITY;
}
