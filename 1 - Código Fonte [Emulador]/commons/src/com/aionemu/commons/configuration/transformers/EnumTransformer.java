package com.aionemu.commons.configuration.transformers;

import com.aionemu.commons.configuration.TransformationTypeInfo;

/**
 * @author Lost Academy Team & Durak
 */
public class EnumTransformer extends PropertyTransformer<Enum<?>> {

	@Override
	public boolean matches(Class<?> targetType) {
		return targetType.isEnum();
	}

	@Override
	@SuppressWarnings({ "unchecked", "rawtypes" })
	protected Enum<?> parseObject(String value, TransformationTypeInfo typeInfo) {
		return value.isEmpty() ? null : Enum.valueOf((Class<? extends Enum>) typeInfo.getType(), value);
	}
}
