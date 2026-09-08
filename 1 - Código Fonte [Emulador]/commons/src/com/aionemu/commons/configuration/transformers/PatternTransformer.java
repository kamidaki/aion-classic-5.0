package com.aionemu.commons.configuration.transformers;

import java.util.regex.Pattern;

import com.aionemu.commons.configuration.TransformationTypeInfo;

/**
 * @author Lost Academy Team & Durak
 */
public class PatternTransformer extends PropertyTransformer<Pattern> {

	@Override
	public boolean matches(Class<?> targetType) {
		return targetType == Pattern.class;
	}

	@Override
	protected Pattern parseObject(String value, TransformationTypeInfo typeInfo) {
		return value.isEmpty() ? null : Pattern.compile(value);
	}
}
