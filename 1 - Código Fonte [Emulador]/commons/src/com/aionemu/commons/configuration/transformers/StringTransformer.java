package com.aionemu.commons.configuration.transformers;

import com.aionemu.commons.configuration.TransformationTypeInfo;

/**
 * @author Lost Academy Team & Durak
 */
public class StringTransformer extends PropertyTransformer<String> {

	@Override
	public boolean matches(Class<?> targetType) {
		return targetType == String.class;
	}

	@Override
	protected String parseObject(String value, TransformationTypeInfo typeInfo) {
		return value;
	}
}
