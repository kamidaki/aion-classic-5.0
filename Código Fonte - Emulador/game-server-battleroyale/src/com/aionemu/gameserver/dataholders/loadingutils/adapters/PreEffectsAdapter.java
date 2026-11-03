package com.aionemu.gameserver.dataholders.loadingutils.adapters;

import javax.xml.bind.annotation.adapters.XmlAdapter;

/**
 * @author Lost Academy Team & Durak
 */
public class PreEffectsAdapter extends XmlAdapter<String, int[]> {

	@Override
	public String marshal(int[] v) {
		if (v == null || v.length == 0)
			return null;
		StringBuilder sb = new StringBuilder(v.length * 3);
		for (int i = 0; i < v.length; i++) {
			if (i > 0)
				sb.append(' ');
			sb.append(v[i]);
		}
		return sb.toString();
	}

	@Override
	public int[] unmarshal(String v) {
		if (v == null || v.trim().isEmpty())
			return null;
		String[] values = v.trim().split("[ _]+");
		int[] ints = new int[values.length];
		for (int i = 0; i < values.length; i++) {
			ints[i] = Integer.parseInt(values[i].trim());
		}
		return ints;
	}
}
