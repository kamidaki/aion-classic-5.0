package com.aionemu.commons.configuration.transformers;

import com.aionemu.commons.configuration.TransformationTypeInfo;

/**
 * @author Lost Academy Team & Durak
 */
public class BooleanTransformer extends PropertyTransformer<Boolean> {

	@Override
	public boolean matches(Class<?> targetType) {
		return targetType == boolean.class;
	}

	@Override
	protected Boolean parseObject(String value, TransformationTypeInfo typeInfo) {
		// not using "Boolean.parseBoolean" since it never throws an error (returns false if string is not "true" ignoring case)
		if ("true".equalsIgnoreCase(value) || "1".equals(value)) {
			return true;
		} else if ("false".equalsIgnoreCase(value) || "0".equals(value)) {
			return false;
		} else {
			throw new IllegalArgumentException("Only true, false, 1 and 0 are allowed.");
		}
	}
}
