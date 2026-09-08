package com.aionemu.commons.scripting.url;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.net.URLConnection;

import com.aionemu.commons.scripting.ScriptClassLoader;

/**
 * @author Lost Academy Team & Durak
 */
public class VirtualClassURLConnection extends URLConnection {

	/**
	 * Input stream, is assigned from class
	 */
	private InputStream is;

	/**
	 * Creates URL connections that "connects" to class binary data
	 * 
	 * @param url
	 *          class name
	 * @param cl
	 *          classloader
	 */
	protected VirtualClassURLConnection(URL url, ScriptClassLoader cl) {
		super(url);
		is = new ByteArrayInputStream(cl.getByteCode(url.getHost()));
	}

	/**
	 * This method is ignored
	 */
	@Override
	public void connect() throws IOException {

	}

	@Override
	public InputStream getInputStream() throws IOException {
		return is;
	}
}
