package com.aionemu.commons.configuration.transformers;

import java.net.InetSocketAddress;
import java.net.URI;

import com.aionemu.commons.configuration.TransformationTypeInfo;

/**
 * @author Lost Academy Team & Durak
 */
public class InetSocketAddressTransformer extends PropertyTransformer<InetSocketAddress> {

	@Override
	public boolean matches(Class<?> targetType) {
		return InetSocketAddress.class.isAssignableFrom(targetType);
	}

	@Override
	protected InetSocketAddress parseObject(String value, TransformationTypeInfo typeInfo) throws Exception {
		URI uri = new URI(null, value, null, null, null);
		return new InetSocketAddress(uri.getHost(), uri.getPort());
	}
}
