package com.aionemu.commons.configuration.transformers;

import java.util.TimeZone;

import com.aionemu.commons.configuration.TransformationTypeInfo;

/**
 * @author Lost Academy Team & Durak
 */
public class TimeZoneTransformer extends PropertyTransformer<TimeZone> {

	@Override
	public boolean matches(Class<?> targetType) {
		return TimeZone.class.isAssignableFrom(targetType);
	}

	@Override
	protected TimeZone parseObject(String value, TransformationTypeInfo typeInfo) {
		return value.isEmpty() ? TimeZone.getDefault() : TimeZone.getTimeZone(value);
	}
}
